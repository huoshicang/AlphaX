import time
import random
import string
from urllib.parse import quote

def generate_cookie_string(exact_copy=False):
    """
    生成与示例结构相同的 Cookie 字符串
    :param exact_copy: True 表示完全复制示例中的固定值；False 表示动态生成随机值
    :return: Cookie 字符串
    """
    if exact_copy:
        # 精确复制（与用户提供的字符串完全一致）
        cookies = {
            "qgqp_b_id": "c32e54edfef011d159529ebced750ddf",
            "st_nvi": "ONCpFzU7rzcNrpES_wV2K7fe8",
            "st_si": "86569052095399",
            "websitepoptg_api_time": "1775627581854",
            "nid18": "0cca8a925df2af21e27d1da02e0fc350",
            "nid18_create_time": "1775627581930",
            "gviem": "D7kiC9IhSGrN7O6r37-g-ca9b",
            "gviem_create_time": "1775627581930",
            "fullscreengg": "1",
            "fullscreengg2": "1",
            "wsc_checkuser_ok": "1",
            "st_pvi": "12526172509365",
            "st_sp": "2026-04-08%2013%3A53%3A01",
            "st_inirUrl": "https%3A%2F%2Fcn.bing.com%2F",
            "st_sn": "5",
            "st_psi": "2026040814020578-113200301201-2013835824",
            "st_asi": "delete"
        }
    else:
        # 动态生成随机值
        now_ms = int(time.time() * 1000)
        now_str = time.strftime("%Y-%m-%d %H:%M:%S")
        now_str_encoded = quote(now_str)  # URL 编码

        def random_hex(len=32):
            return ''.join(random.choices(string.hexdigits.lower(), k=len))

        def random_digits(len):
            return ''.join(random.choices(string.digits, k=len))

        def random_str(len):
            return ''.join(random.choices(string.ascii_letters + string.digits + '-_', k=len))

        cookies = {
            "qgqp_b_id": random_hex(32),
            "st_nvi": random_str(22),
            "st_si": random_digits(14),
            "websitepoptg_api_time": str(now_ms),
            "nid18": random_hex(32),
            "nid18_create_time": str(now_ms),
            "gviem": random_str(20),
            "gviem_create_time": str(now_ms),
            "fullscreengg": "1",
            "fullscreengg2": "1",
            "wsc_checkuser_ok": "1",
            "st_pvi": random_digits(14),
            "st_sp": now_str_encoded,
            "st_inirUrl": quote("https://cn.bing.com/"),
            "st_sn": str(random.randint(1, 10)),
            "st_psi": f"{time.strftime('%Y%m%d%H%M%S')}-{random_digits(12)}-{random_digits(10)}",
            "st_asi": "delete"
        }

    # 拼接成 Cookie 字符串（键值对用 '=' 连接，之间用 '; ' 分隔）
    return '; '.join(f"{k}={v}" for k, v in cookies.items())

# 示例使用
if __name__ == "__main__":
    # 1. 生成精确复制的字符串（与用户提供的一模一样）
    exact_cookie = generate_cookie_string(exact_copy=True)
    print("=== 精确复制 ===\n", exact_cookie, "\n")

    # 2. 生成动态变化的字符串（每次运行结果不同）
    dynamic_cookie = generate_cookie_string(exact_copy=False)
    print("=== 动态生成 ===\n", dynamic_cookie)