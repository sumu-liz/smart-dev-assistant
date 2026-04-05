# 黑马点评项目知识
## 秒杀功能
- 使用Redis预减库存，提高并发性能
- 用Redis分布式锁防止超卖
- 一人一单：根据用户ID做锁
- 异步下单消息队列削峰
## 优惠券规则
- 一个用户一天只能抢一张
- 库存不足直接秒杀失败
- 支付超时自动取消订单
## 技术栈
SpringBoot, MySQL, Redis, RabbitMQ, MyBatis-Plus
