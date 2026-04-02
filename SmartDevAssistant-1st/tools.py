import requests
from langchain.tools import tool

BASE_URL = "http://localhost:8081"
USER_TOKEN = "f7edee2af36c488ca1f91afda207f751"  # 你的新token


# ======================
# 1. 查询优惠券（正常）
# ======================
@tool
def query_vouchers() -> str:
    """查询当前可用的优惠券列表。不需要任何参数。"""
    try:
        headers = {"Authorization": USER_TOKEN}
        response = requests.get(f"{BASE_URL}/voucher/list/1", headers=headers, timeout=5)

        if response.status_code == 200:
            data = response.json()
            if data.get("success"):
                vouchers = data.get("data", [])
                if not vouchers:
                    return "当前没有可用的优惠券。"
                result = "优惠券列表：\n"
                for v in vouchers:
                    result += f"ID: {v['id']}, 名称: {v['title']}\n"
                return result
            else:
                return f"查询失败：{data.get('message')}"
        else:
            return f"请求失败：{response.status_code}"
    except Exception as e:
        return f"出错：{str(e)}"


# ======================
# 2. 秒杀优惠券（已修复！！！）
# ======================
@tool
def seckill_voucher(voucher_id: int) -> str:
    """
    调用黑马点评秒杀接口，抢购指定ID的优惠券
    :param voucher_id: 要秒杀的优惠券ID（数字）
    """
    try:
        #【关键修复】POST 必须加 Content-Type！！！
        cookie_str="JSESSIONID=6D0AF08A5D1BF7D658D3954ABC4BA8F6; Path=/; HttpOnly"
        headers = {
            "Authorization": USER_TOKEN,
            "Cookie": cookie_str
        }

        # 路径严格对齐你的接口
        url = f"{BASE_URL}/voucher-order/seckill/{voucher_id}"

        # POST 请求
        response = requests.post(url, params={"voucherId":voucher_id},headers=headers)

        if response.status_code == 200:
            data = response.json()
            if data.get("success"):
                return f"秒杀成功！ID：{voucher_id}"
            else:
                return f"失败：{data.get('message')}"
        else:
            return f"请求失败：{response.status_code}"
    except Exception as e:
        return f"秒杀出错：{str(e)}"