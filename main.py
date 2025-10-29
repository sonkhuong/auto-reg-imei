import logging
import subprocess
from datetime import datetime, timedelta
from uuid import uuid4

import json
import re
import requests
import time
from cryptography.fernet import Fernet

LOG_FILE = "bot.log"
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE, encoding="utf-8"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


def load_secrets():
    """Giải mã file secrets.enc để lấy token và API key"""
    with open("key.key", "rb") as f:
        key = f.read()
    fernet = Fernet(key)
    with open("secrets.enc", "rb") as f:
        encrypted = f.read()
    decrypted = fernet.decrypt(encrypted)
    return json.loads(decrypted.decode())


secrets = load_secrets()

# === CONFIG ===
PREFIXES = ["8648680715", "8629980740", "8690180787", "8674980612"]  # danh sách prefix cần check
COOKIE = "serviceToken=m41w%2FCyfA%2B8gqMCiBpFSk9zjQGI8FIpZPbz4YWlngBOIDCCj%2FNrq9%2FdqzjVZseECQpTSqMfjrLBdZQdapzKsivMxvDdnjzLZyynF%2FVYQWS98xx9Qn7I9KiGblOnkn9BZxpJYIdD38NYNeauM4u8sM8dWKByrKO69y%2Bht26obOCA%3D; mUserId=LmVXjOn%2FDOl5HNwVonMqG6R6cf%2FBC2IJwDWkDAqa8w%3D"
URL = "https://hd.c.mi.com/vn/eventapi/api/imeiexchange/getactinfo"
HEADERS = {
    "Cookie": COOKIE,
    "Referer": "https://www.mi.com/vn/imei-redemption/",
    "User-Agent": "Mozilla/5.0"
}
GITHUB_TOKEN = secrets["GITHUB_TOKEN"]
GITHUB_REPO = "https://github.com/sonkhuong/auto-reg-imei.git"
GITHUB_USER = "sonkhuong"
INTERVAL = 1.3  # giây giữa mỗi request
EMAIL_REFRESH_MINUTES = 25


def push_to_github():
    """Tự động commit & push dữ liệu mới lên GitHub."""
    try:
        repo_url = GITHUB_REPO
        token = GITHUB_TOKEN

        if not all([repo_url, token]):
            logger.warning("[GIT PUSH] Thiếu biến môi trường GitHub → Bỏ qua push.")
            return

        subprocess.run(["git", "config", "user.name", GITHUB_USER])
        subprocess.run(["git", "config", "user.email", "sonmasteryi@gmail.com"])

        # Add, commit và push
        subprocess.run(["git", "add", "."], check=True)
        subprocess.run(["git", "commit", "-m", "update kho"], check=False)
        subprocess.run(["git", "push", "-f", "origin", "main"], check=True)

        logger.info("[GIT PUSH] ✅ Đã push dữ liệu mới lên GitHub.")
    except subprocess.CalledProcessError as e:
        logger.error(f"[GIT PUSH ERROR] {e}")
    except Exception as e:
        logger.error(f"[GIT PUSH EXCEPTION] {e}")


# === 1. Tạo email từ mail.tm ===
def create_email():
    base = "https://api.mail.tm"
    domain = requests.get(f"{base}/domains").json()["hydra:member"][0]["domain"]
    email = f"demo{int(time.time())}@{domain}"
    password = str(uuid4())
    requests.post(f"{base}/accounts", json={"address": email, "password": password}).raise_for_status()
    token = requests.post(f"{base}/token", json={"address": email, "password": password}).json()["token"]
    return email, token


# === 2. Gửi mã xác minh qua API có kèm Cookie ===
def trigger_send_verification(email):
    api_url = f"https://hd.c.mi.com/vn/eventapi/api/imeiexchange/sendcode?from=pc&email={email}&tel="
    headers = {
        "Cookie": COOKIE,
        "User-Agent": "Mozilla/5.0"
    }
    r = requests.get(api_url, headers=headers)
    logger.info(f"📤 Gửi yêu cầu gửi mã xác minh tới: {email}")
    logger.info("🔁 Phản hồi gửi mã:", r.text)


# === 3. Đợi nhận mã xác minh từ email ===
def wait_for_code(token, timeout=90):
    headers = {"Authorization": f"Bearer {token}"}
    for _ in range(timeout // 2):
        res = requests.get("https://api.mail.tm/messages", headers=headers).json()
        if res["hydra:member"]:
            msg_id = res["hydra:member"][0]["id"]
            msg = requests.get(f"https://api.mail.tm/messages/{msg_id}", headers=headers).json()
            logger.info("📩 Tiêu đề:", msg["subject"])
            logger.info("📝 Nội dung:\n", msg["text"])
            match = re.search(r"Mã xác minh[:：]\s*([a-zA-Z0-9]{4,})", msg["text"])
            if match:
                return match.group(1)
        time.sleep(2)
    raise TimeoutError("Không nhận được mã xác minh!")


# === 4. Chạy random IMEI cho 1 email + captcha ===
def run_check(email, captcha, start_index, prefix):
    for i in range(start_index, 100000):
        imei = prefix + f"{i:04d}"
        try:
            res = requests.get(URL, params={
                "from": "pc", "imei": imei, "email": email, "tel": "", "captchaCode": captcha
            }, headers=HEADERS, timeout=10)
            j = res.json()
            # logger.info(f"{imei} -> {j}")

            if j.get("code") == 0:
                goods = j["data"]["goodsList"][0]
                act = goods["actList"][0]
                info = {
                    "imei": imei,
                    "goodsId": goods["goodsId"],
                    "activityId": act["activityId"],
                    "goodsName": goods["goodsName"],
                    "canRedeem": act["canRedeem"]
                }
                if act["canRedeem"] == 0:
                    with open("IMEI_canRedeem0.txt", "a", encoding="utf-8") as f:
                        f.write(json.dumps(info, ensure_ascii=False) + "\n")

        except Exception as e:
            logger.info(f"❌ Error {imei}: {e}")
        time.sleep(INTERVAL)

        # Kiểm tra timeout 25 phút để reset captcha
        if datetime.now() >= run_check.expire_time:
            return i + 1  # trả về số tiếp theo để tiếp tục
    return None  # đã chạy hết


# === MAIN LOOP ===
def main():
    for prefix in PREFIXES:
        current_index = 0
        while current_index is not None and current_index < 100000:
            # ✅ 1. Push GitHub trước khi refresh email
            logger.info("🔁 Pushing dữ liệu trước khi tạo email mới...")
            push_to_github()

            # ✅ 2. Tạo email mới
            logger.info("📮 Tạo email mới...")
            email, token = create_email()
            logger.info("📧 Email:", email)

            # ✅ 3. Gửi yêu cầu mã xác minh
            trigger_send_verification(email)

            # ✅ 4. Chờ nhận mã xác minh
            logger.info("⏳ Chờ mã xác minh...")
            captcha = wait_for_code(token)
            logger.info("✅ Mã xác minh:", captcha)

            # ✅ 5. Set thời gian hết hạn captcha 25 phút sau
            run_check.expire_time = datetime.now() + timedelta(minutes=EMAIL_REFRESH_MINUTES)

            # ✅ 6. Bắt đầu chạy IMEI loop
            current_index = run_check(email, captcha, current_index, prefix)

    logger.info("🧹 Đã chạy xong tất cả prefix → push dữ liệu cuối cùng...")
    push_to_github()
    logger.info("✅ Đã chạy xong toàn bộ prefix và IMEI.")


if __name__ == "__main__":
    main()
