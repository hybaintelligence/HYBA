import redis
from redis.exceptions import ConnectionError

class RedisQuantumSubstrateRegistry:
    def __init__(self, host, port, db, password):
        self.host = host
        self.port = port
        self.db = db
        self.password = password
        self.available = False
        self.client = None  # Ensure client is defined
        self._initialize()

    def _initialize(self):
        try:
            self.client = redis.Redis(host=self.host, port=self.port, db=self.db, password=self.password)
            self.client.ping()
            self.available = True
        except ConnectionError:
            print("Redis connection failed. Running without Redis.")
            self.client = None
            self.available = False

    # 其他方法...
