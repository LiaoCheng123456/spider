import redis
class redisConnectionPool:
    def __init__(self):
        self.pool = redis.ConnectionPool(host="localhost", port=6379, password=123456)

    def getClient(self):
        r = redis.Redis(connection_pool=self.pool)
        return r


redispoot = redisConnectionPool()
r = redispoot.getClient()
r.set("hello","world")
print(r.get("hello"))

# r.sadd("urllist","www.baidu.com","www.juejin.com")
# print(r.spop("urllist"))
print(r.sadd("urlist","www.baidu.com"))
