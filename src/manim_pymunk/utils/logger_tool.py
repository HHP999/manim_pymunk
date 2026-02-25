
__all__ = ["manim_pymunk_logger"]

import logging
import threading


class SingletonLogger:
    _instance_lock = threading.Lock()
    _instance = None

    def __new__(cls, *args, **kwargs):
        # 双重检查锁定，确保线程安全
        if not cls._instance:
            with cls._instance_lock:
                if not cls._instance:
                    cls._instance = super(SingletonLogger, cls).__new__(cls)
                    cls._instance._inherited_init()
        return cls._instance

    def _inherited_init(self):
        """在这里配置你的日志逻辑"""
        self.logger = logging.getLogger("MySingletonLogger")
        self.logger.setLevel(logging.DEBUG)
        self.logger.propagate = False

        # 避免重复添加处理器
        if not self.logger.handlers:
            # 1. 定义格式
            log_format = "manim-pymunk:[%(levelname)s]:%(asctime)s:%(filename)s:%(message)s"
            date_format = "%Y-%m-%d %H-%M-%S"
            formatter = logging.Formatter(log_format, date_format)

            # 2. 控制台处理器
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(formatter)
            self.logger.addHandler(console_handler)

    def get_logger(self):
        return self.logger

# 为了方便使用，可以直接实例化一个全局对象
manim_pymunk_logger = SingletonLogger().get_logger()
