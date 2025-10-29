import requests, time, json
#zsr00810@laoia.com
#jWn7PRGjbW7Si_4
COOKIE = "serviceToken=m41w%2FCyfA%2B8gqMCiBpFSk9zjQGI8FIpZPbz4YWlngBOIDCCj%2FNrq9%2FdqzjVZseECQpTSqMfjrLBdZQdapzKsivMxvDdnjzLZyynF%2FVYQWS98xx9Qn7I9KiGblOnkn9BZxpJYIdD38NYNeauM4u8sM8dWKByrKO69y%2Bht26obOCA%3D; mUserId=LmVXjOn%2FDOl5HNwVonMqG6R6cf%2FBC2IJwDWkDAqa8w%3D"
EMAIL = "quyenquachujxnt@gmail.com"
PREFIX = "86486807273"
URL = "https://hd.c.mi.com/vn/eventapi/api/imeiexchange/getactinfo"
HEADERS = {
    "Cookie": COOKIE,
    "Referer": "https://www.mi.com/vn/imei-redemption/",
    "User-Agent": "Mozilla/5.0"
}
INTERVAL = 1.5

with open("IMEI.txt", encoding="utf-8") as f:
    lines = f.read().strip().splitlines()

for imei in lines:
    try:
        r = requests.get(
            URL,
            params={"from": "pc", "imei": imei, "email": EMAIL, "tel": "", "captchaCode": "bf3a"},
            headers=HEADERS,
            timeout=10
        )
        j = r.json()
        print(f"{imei} -> {j}")

        if j.get("code") == 0:
            goods_list = j.get("data", {}).get("goodsList", [])
            if not goods_list or goods_list[0].get("goodsId") == 61265:
                continue

            act_list = goods_list[0].get("actList", [])
            if act_list:
                can_redeem = act_list[0].get("canRedeem")
                if can_redeem == 0:
                    with open("IMEI_canRedeem0.txt", "a", encoding="utf-8") as f:
                        f.write(imei + "\n")

    except Exception as e:
        print(f"Error {imei}: {e}")
    time.sleep(INTERVAL)
