"""
日志配置模块
使用loguru统一管理项目日志
"""

import os
import sys
from datetime import datetime
from loguru import logger


class LoggerConfig:
    """日志配置类"""
    
    def __init__(self, log_dir: str = "logs"):
        """
        初始化日志配置
        
        Args:
            log_dir: 日志目录路径
        """
        self.log_dir = log_dir
        self._setup_logger()
    
    def _setup_logger(self):
        """配置loguru日志器"""
        # 移除默认配置
        logger.remove()
        
        # 创建日志目录
        os.makedirs(self.log_dir, exist_ok=True)
        
        # 日志文件路径
        log_file = os.path.join(
            self.log_dir, 
            f"app_{datetime.now().strftime('%Y%m%d')}.log"
        )
        
        # 控制台输出格式
        console_format = (
            "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
            "<level>{level}</level> | "
            "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
            "<level>{message}</level>"
        )
        
        # 文件输出格式
        file_format = (
            "{time:YYYY-MM-DD HH:mm:ss} | "
            "{level} | "
            "{name}:{function}:{line} | "
            "{message}"
        )
        
        # 控制台输出
        logger.add(
            sys.stderr,
            format=console_format,
            level="INFO",
            colorize=True,
            backtrace=True,
            diagnose=True
        )
        
        # 文件输出
        logger.add(
            log_file,
            format=file_format,
            level="DEBUG",
            rotation="10 MB",  # 日志文件大小达到10MB时轮转
            retention="30 days",  # 保留30天的日志
            compression="zip",  # 压缩旧日志
            encoding="utf-8",
            backtrace=True,
            diagnose=True
        )
        
        # 错误日志单独记录
        error_log_file = os.path.join(
            self.log_dir, 
            f"error_{datetime.now().strftime('%Y%m%d')}.log"
        )
        
        logger.add(
            error_log_file,
            format=file_format,
            level="ERROR",
            rotation="5 MB",
            retention="90 days",
            compression="zip",
            encoding="utf-8",
            backtrace=True,
            diagnose=True
        )


# 创建全局日志配置
log_config = LoggerConfig()

# 导出logger实例
log = logger

# 便捷装饰器
def log_function_call(func):
    """记录函数调用的装饰器"""
    def wrapper(*args, **kwargs):
        log.debug(f"调用函数: {func.__name__}, 参数: args={args}, kwargs={kwargs}")
        try:
            result = func(*args, **kwargs)
            log.debug(f"函数 {func.__name__} 执行成功")
            return result
        except Exception as e:
            log.error(f"函数 {func.__name__} 执行失败: {str(e)}")
            raise
    return wrapper


def setup_custom_logger(name: str, level: str = "INFO"):
    """
    设置自定义日志器
    
    Args:
        name: 日志器名称
        level: 日志级别
        
    Returns:
        配置好的日志器
    """
    return logger.bind(name=name).patch(lambda record: record.update(name=name))