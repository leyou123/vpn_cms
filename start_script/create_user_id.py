import redis
import time
import logging
import pymysql
import datetime


HOST = "3.101.19.69"

pool0 = redis.ConnectionPool(host=HOST, port=6379, password="leyou2020", db=0)
r0 = redis.Redis(connection_pool=pool0)

# 64位ID的划分
WORKER_ID_BITS = 5
DATACENTER_ID_BITS = 5
SEQUENCE_BITS = 12

# 最大取值计算
MAX_WORKER_ID = -1 ^ (-1 << WORKER_ID_BITS)  # 2**5-1 0b11111
MAX_DATACENTER_ID = -1 ^ (-1 << DATACENTER_ID_BITS)

# 移位偏移计算
WOKER_ID_SHIFT = SEQUENCE_BITS
DATACENTER_ID_SHIFT = SEQUENCE_BITS + WORKER_ID_BITS
TIMESTAMP_LEFT_SHIFT = SEQUENCE_BITS + WORKER_ID_BITS + DATACENTER_ID_BITS

# 序号循环掩码
SEQUENCE_MASK = -1 ^ (-1 << SEQUENCE_BITS)

# Twitter元年时间戳
TWEPOCH = 1288834974657


class Session(object):
    # 初始化对象，产生一个mysql连接
    def __init__(self):
        self._ip = HOST
        self._user = "root"
        self._passwd = "Leyou2020"
        self._db = "vpn"
        self._port = 3306
        self._charset = 'utf8'
        self._conn = None
        self._cursor = None
        try:
            self._conn = pymysql.connect(
                host=self._ip,
                user=self._user,
                password=self._passwd,
                database=self._db,
                charset=self._charset,
                port=self._port,
                autocommit=True
            )
        except Exception as err:
            format_err = f"ERROR - {self._ip} session init failed: {err}" + "\n"
            raise Exception(format_err)

    def query(self, sql):
        """
        :param sql: 查询语句
        :return: result-查询结果;
        """
        cursor = self._conn.cursor(pymysql.cursors.DictCursor)
        try:
            result = []
            rows = cursor.execute(sql)
            if rows > 0:
                sql_result = cursor.fetchall()
                # result = [list(i) for i in sql_result]
                result = sql_result
            cursor.close()
            return result
        except Exception as err:
            format_err = f"ERROR - {self._ip} query failed: {err} - {sql}" + "\n"
            raise Exception(format_err)
        finally:
            cursor.close()


def query_user(uid):

    mysql_session = Session()
    sql1 = f"select * from users where uid={uid}"
    res = mysql_session.query(sql1)
    if res:
        return True
    else:
        return False


def get_user_id():
    """
        获取token
    """
    user_id = r0.lpop("user_id")
    new_user_id = ""
    if user_id:
        new_user_id = str(user_id, "utf-8")
    return new_user_id

class InvalidSystemClock(Exception):
    """
    时钟回拨异常
    """
    pass


class IdWorker(object):
    """
    用于生成IDs
    """

    def __init__(self, datacenter_id, worker_id, sequence=0):
        """
        初始化
        :param datacenter_id: 数据中心（机器区域）ID
        :param worker_id: 机器ID
        :param sequence: 其实序号
        """
        # sanity check
        if worker_id > MAX_WORKER_ID or worker_id < 0:
            raise ValueError('worker_id值越界')

        if datacenter_id > MAX_DATACENTER_ID or datacenter_id < 0:
            raise ValueError('datacenter_id值越界')

        self.worker_id = worker_id
        self.datacenter_id = datacenter_id
        self.sequence = sequence

        self.last_timestamp = -1  # 上次计算的时间戳

    def _gen_timestamp(self):
        """
        生成整数时间戳
        :return:int timestamp
        """
        return int(time.time() * 1000)

    def get_id(self):
        """
        获取新ID
        :return:
        """
        timestamp = self._gen_timestamp()

        # 时钟回拨
        if timestamp < self.last_timestamp:
            logging.error('clock is moving backwards. Rejecting requests until {}'.format(self.last_timestamp))
            raise InvalidSystemClock

        if timestamp == self.last_timestamp:
            self.sequence = (self.sequence + 1) & SEQUENCE_MASK
            if self.sequence == 0:
                timestamp = self._til_next_millis(self.last_timestamp)
        else:
            self.sequence = 0

        self.last_timestamp = timestamp

        new_id = ((timestamp - TWEPOCH) << TIMESTAMP_LEFT_SHIFT) | (self.datacenter_id << DATACENTER_ID_SHIFT) | \
                 (self.worker_id << WOKER_ID_SHIFT) | self.sequence
        return new_id

    def _til_next_millis(self, last_timestamp):
        """
        等到下一毫秒
        """
        timestamp = self._gen_timestamp()
        while timestamp <= last_timestamp:
            timestamp = self._gen_timestamp()
        return timestamp


def main():
    id_name = "user_id"
    # id_name = "test_user_id"

    user_len = r0.llen(id_name)
    user_min = 50000

    if user_len < user_min:
        worker = IdWorker(1, 2, 0)
        for j in range(15):
            id_list = []
            for i in range(1000):
                time.sleep(0.001)
                user_id = worker.get_id()
                id_list.append(user_id)

            res1 = r0.lpush(id_name,*id_list)
            print(id_list)



if __name__ == '__main__':
    while True:
        try:
            main()
        except Exception as e:
            print(e)
        print("等待60秒")
        time.sleep(60)
