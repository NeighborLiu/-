import hashlib
import random
import time
import requests

def youdao_translate(text, from_lang="auto", to_lang="zh-CHS"):
    """
    调用有道智云翻译 API 进行文本翻译。
    :param text: 待翻译的文本（str 或 bytes）
    :param from_lang: 源语言代码，默认为 "auto"（自动检测）
    :param to_lang: 目标语言代码，默认为 "zh-CHS"（简体中文）
    :return: 翻译结果（str）
    """
    # 确保 text 是 str 类型
    if isinstance(text, bytes):
        text = text.decode("utf-8", errors="ignore")
    elif not isinstance(text, str):
        raise TypeError("Input must be a string or bytes.")

    url = 'https://openapi.youdao.com/api'
    app_key = '659395bdeef4d8dc'  # 替换成你的 APP_KEY
    app_secret = 'fH7tEDa7GCeokl0AiUkD7CmvyRijf9vU'  # 替换成你的 APP_SECRET

    # 生成随机数和当前时间戳
    salt = str(random.randint(10000, 99999))
    cur_time = str(int(time.time()))

    # 计算签名（SHA-256）
    sign_str = app_key + text + salt + cur_time + app_secret
    sign = hashlib.sha256(sign_str.encode("utf-8")).hexdigest()

    # 构造请求参数
    params = {
        "q": text,
        "from": from_lang,
        "to": to_lang,
        "appKey": app_key,
        "salt": salt,
        "sign": sign,
        "signType": "v3",
        "curtime": cur_time,
    }

    # 发送 GET 请求（POST 也可以）
    response = requests.get(url, params=params)
    result = response.json()

    # 解析返回结果
    if result.get("errorCode") == "0":
        return result["translation"][0]
    else:
        error_code = result.get("errorCode")
        error_msg = result.get("message", "Unknown error")
        raise Exception(f"Translation failed! Error {error_code}: {error_msg}")

# 测试
if __name__ == "__main__":
    try:
        translated_text = youdao_translate("hello", from_lang="en", to_lang="zh-CHS")
        print("翻译结果:", translated_text)  # 应该返回 "你好" 或类似翻译
    except Exception as e:
        print("出错:", e)