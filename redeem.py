import requests, json, time

URL = "https://hd.c.mi.com/vn/eventapi/api/imeiexchange/redeem"
COOKIE = "serviceToken=m41w%2FCyfA%2B8gqMCiBpFSk9zjQGI8FIpZPbz4YWlngBOIDCCj%2FNrq9%2FdqzjVZseECQpTSqMfjrLBdZQdapzKsivMxvDdnjzLZyynF%2FVYQWS98xx9Qn7I9KiGblOnkn9BZxpJYIdD38NYNeauM4u8sM8dWKByrKO69y%2Bht26obOCA%3D; mUserId=LmVXjOn%2FDOl5HNwVonMqG6R6cf%2FBC2IJwDWkDAqa8w%3D"
EMAIL = "quyenquachujxnt@gmail.com"
#https://hd.c.mi.com/vn/eventapi/api/imeiexchange/sendcode?from=pc&email=quyenquachu.j.xnt@gmail.com&tel=
CAPTCHA = "7ole"

HEADERS = {
    "accept": "*/*",
    "accept-encoding": "gzip, deflate, br, zstd",
    "accept-language": "en-US,en;q=0.9",
    "content-type": "application/x-www-form-urlencoded; charset=UTF-8",
    "origin": "https://www.mi.com",
    "referer": "https://www.mi.com/vn/imei-redemption/",
    "sec-ch-ua": '"Google Chrome";v="141", "Not?A_Brand";v="8", "Chromium";v="141"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"Windows"',
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36",
    "cookie": COOKIE
}

PRODUCTS = [
    {"goods_id": "4223714552", "act_id": "1399", "goods_name": "Xiaomi 15 Xanh lá 12 GB + 512 GB"},
    {"goods_id": "4223714554", "act_id": "1399", "goods_name": "Xiaomi 15 Đen 12 GB + 512 GB"},
    {"goods_id": "4223714549", "act_id": "1399", "goods_name": "Xiaomi 15 Trắng 12 GB+256 GB"},
]

with open("IMEI_canRedeem0.txt", encoding="utf-8") as f:
    lines = f.read().strip().splitlines()

for line in lines:
    try:
        imei = str(line)
        goods_id = str(4223714549)
        act_id = str(1399)
        goods_name = "Xiaomi 15 Trắng 12 GB+256 GB"
        # goods_id = str(4223714552)
        # act_id = str(1399)
        # goods_name = "Xiaomi 15 Xanh lá 12 GB + 512 GB"
        # goods_id = str(4223714554)
        # act_id = str(1399)
        # goods_name = "Xiaomi 15 Đen 12 GB + 512 GB"

        data = {
            "from": "pc",
            "goodsId": goods_id,
            "channel": "CellphoneS",
            "email": EMAIL,
            "tel": "",
            "captchaCode": CAPTCHA,
            "imei": imei,
            "activityId": act_id,
            "goodsName": goods_name,
            "invoiceUrl1": "",
            "invoiceUrl2": "",
            "invoiceUrl3": "",
            "isSubscribe": "0"
        }

        r = requests.post(URL, headers=HEADERS, data=data, timeout=15)
        res_text = r.text.strip()
        print(f"{imei} -> {res_text}")

        try:
            j = r.json()
            if j.get("code") == 313025 or j.get("code") == 313018:
                with open("FINAL_CODE_VALID.txt", "a", encoding="utf-8") as f_out:
                    f_out.write(imei + "\n")
            else:
                with open("NOT_VALID_IMEI.txt", "a", encoding="utf-8") as f_out:
                    f_out.write(imei + "\n")
        except Exception:
            pass

    except Exception as e:
        print("Error:", e)

    time.sleep(1.5)