import redis
r = redis.Redis(host="localhost", port=6379, password=123456)
r.set('foo', 'Bar')
print(r.get('foo'))