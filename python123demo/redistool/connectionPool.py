import redis
class redisConnectionPool:
    def __init__(self):
        self.pool = redis.ConnectionPool(host="localhost", port=6379, password=123456)

    def getClient(self):
        r = redis.Redis(connection_pool=self.pool)
        return r
    def getConnection(self):
    	return redis.Redis(host="localhost", port=6379, password=123456)
