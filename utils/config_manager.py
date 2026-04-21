"""
配置管理模块
统一管理项目配置，提供配置读取和验证功能
"""

import os
from typing import Dict, Any, Optional
from .logger import log


class ConfigManager:
    """配置管理器"""
    
    def __init__(self):
        """
        初始化配置管理器
        """
        # 项目根目录：utils目录的父目录
        self.project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        log.info(f"配置管理器初始化完成，项目根目录: {self.project_root}")
    
    def get_data_dir(self) -> str:
        """
        获取数据目录路径
        
        Returns:
            数据目录的绝对路径
        """
        # 固定数据目录：项目根目录下的data目录
        data_path = os.path.join(self.project_root, 'data')
        
        # 自动创建数据文件夹
        os.makedirs(data_path, exist_ok=True)
        log.debug(f"数据目录路径: {data_path}")
        return data_path


# 创建全局配置管理器实例
config_manager = ConfigManager()

# 便捷函数
def get_data_dir() -> str:
    """获取数据目录路径"""
    return config_manager.get_data_dir()