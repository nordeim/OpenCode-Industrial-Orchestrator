class RedisError(Exception): pass
class RedisConnectionError(RedisError): pass
class RedisTimeoutError(RedisError): pass
class RedisCircuitOpenError(RedisError): pass
