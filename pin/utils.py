import os
from pathlib import Path, PurePath
from loguru import logger
import sys

def create_dir(save_dir):
    """创建目录"""
    try:
        # 使用 Path 对象处理路径,它会自动处理不同操作系统的路径格式
        path = Path(save_dir)
        path.mkdir(parents=True, exist_ok=True)
    except OSError:
        logger.error("路径太长(2045字节)。建议使用 -d <其他路径> 或 -c <文件夹和文件名的最大长度>")
        raise

def sanitize(path):
    """清理文件路径"""
    path = path.replace('<', '').replace('>', '').replace('"', '\'').replace('?', '')\
           .replace('*', '').replace('/', '_').replace('\\', '_').replace('|', '_')\
           .replace(':', '_').replace('.', '_').strip()
    path = ' '.join(path.split())
    p = PurePath(path)
    return p.parts[-1] if p.parts else ''

def sort_func(x):
    """
    排序函数

    用于文件名排序，根据文件名前缀的数字进行排序。
    如果前缀不是数字，则返回0作为排序值。

    参数:
        x (str): 输入字符串，通常是文件名

    返回:
        int: 排序用的数
    """
    prefix = x.split('.')[0].split('_')[0]
    return int(prefix) if prefix.isdigit() else 0

def setup_logger():
    """配置日志记录器"""
    # 移除默认的处理器
    logger.remove()

    # 添加新的处理器
    logger.add(
        sys.stderr,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        level="INFO",
        colorize=True
    )

    return logger

# 创建全局logger实例
logger = setup_logger()