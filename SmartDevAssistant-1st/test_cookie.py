import browser_cookie3
import requests

print("1. 开始加载 Cookie...")
try:
    cj = browser_cookie3.chrome(domain_name='localhost')
    print(f"2. Cookie 加载成功，共 {len(cj)} 个 cookie")
except Exception as e:
    print(f"2. 加载 Cookie 失败: {e}")
    exit()

url = 'http://localhost:8081/voucher/seckill?voucherId=12'
print(f"3. 准备请求 URL: {url}")

try:
    # 注意：秒杀接口通常是 POST，不是 GET
    response = requests.post(url, cookies=cj, timeout=10)
    print(f"4. 响应状态码: {response.status_code}")
    print(f"5. 响应内容: {response.text}")
except Exception as e:
    print(f"请求异常: {e}")