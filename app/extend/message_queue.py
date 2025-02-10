"""消息队列，控制消息发送频率"""

import asyncio
from queue import Queue
from time import sleep

from loguru import logger

from app.core.config import Config
from app.util.decorator import Singleton


class MQ(metaclass=Singleton):
    __launched: bool = False
    __message_queue: Queue = Queue(maxsize=0)
    __limit: float

    def __init__(self, limit: float = 1.5):
        """初始化消息队列

        :param limit: 频率(秒)
        """
        self.__limit = limit

    @property
    def limit(self):
        return self.__limit

    def put(self, msg):
        """写入消息"""
        self.__message_queue.put(msg)

    @staticmethod
    async def send(message):
        try:
            await message()
        except Exception as e:
            logger.exception(e)
            logger.error("消息发送失败")

    def __process(self, loop):
        while True:
            message = self.__message_queue.get()
            asyncio.run_coroutine_threadsafe(self.send(message), loop)
            self.__message_queue.task_done()
            sleep(self.limit)

    def start(self, loop):
        if not self.__launched:
            self.__launched = True
            logger.success("消息队列启动成功！")
            try:
                self.__process(loop)
            except Exception as e:
                logger.exception(e)
                logger.error("消息队列异常停止！")
        else:
            logger.warning("消息队列已启动！")

    async def stop(self):
        logger.info("等待剩余消息发送完毕")
        for p in self.__message_queue.queue:
            await self.send(p)
            await asyncio.sleep(1.3)
        logger.success("消息队列已停止")


mq = MQ(limit=Config.message_queue.limit)
