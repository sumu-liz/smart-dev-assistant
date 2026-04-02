from tools import seckill_voucher

# 测试秒杀ID=11的优惠券
print(seckill_voucher.invoke({"voucher_id": 11}))