import requests
import time

BASE_URL = "https://api.mail.tm"

# Tạo tài khoản ngẫu nhiên
domain = requests.get(BASE_URL + "/domains").json()["hydra:member"][0]["domain"]
username = f"demo{int(time.time())}@{domain}"
password = "test12345678"

# Đăng ký
register = requests.post(BASE_URL + "/accounts", json={"address": username, "password": password})
print("📮 Email:", username)

# Đăng nhập
token_res = requests.post(BASE_URL + "/token", json={"address": username, "password": password})
token = token_res.json()["token"]
headers = {"Authorization": f"Bearer {token}"}

# Theo dõi inbox
print("⏳ Chờ email...")
while True:
    inbox = requests.get(BASE_URL + "/messages", headers=headers).json()
    if inbox["hydra:member"]:
        msg_id = inbox["hydra:member"][0]["id"]
        msg = requests.get(BASE_URL + f"/messages/{msg_id}", headers=headers).json()
        print("📩 Tiêu đề:", msg["subject"])
        print("📝 Nội dung:\n", msg["text"])
        break
    time.sleep(5)
