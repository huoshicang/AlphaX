"""
配置管理模块
统一管理项目配置，提供配置读取和验证功能
"""

import os
import yaml
from typing import Dict, Any, Optional
from .logger import log


class ConfigManager:
    """配置管理器"""
    
    def __init__(self, config_file: str = None):
        """
        初始化配置管理器
        
        Args:
            config_file: 配置文件路径，如果为None则使用默认路径
        """
        if config_file is None:
            # 默认配置文件路径：当前模块所在目录的config.yaml
            self.config_file = os.path.join(
                os.path.dirname(os.path.abspath(__file__)),
                "config.yaml"
            )
        else:
            self.config_file = config_file
        
        self._config_cache: Optional[Dict[str, Any]] = None
        log.info(f"配置管理器初始化完成，配置文件: {self.config_file}")
    
    def load_config(self) -> dict[str, Any] | None:
        """
        加载配置文件
        
        Returns:
            配置字典，如果文件不存在或读取失败返回空字典
        """
        if self._config_cache is not None:
            return self._config_cache
            
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            # 确保返回的是字典类型，处理可能的None值
            self._config_cache = config if isinstance(config, dict) else {}
            log.debug(f"配置文件加载成功: {self.config_file}")
            return self._config_cache
        except FileNotFoundError:
            log.warning(f"配置文件不存在: {self.config_file}，使用默认配置")
            self._config_cache = {}
            return self._config_cache
        except yaml.YAMLError as e:
            log.error(f"配置文件格式错误: {str(e)}，使用默认配置")
            self._config_cache = {}
            return self._config_cache
        except Exception as e:
            log.error(f"读取配置文件失败: {str(e)}，使用默认配置")
            self._config_cache = {}
            return self._config_cache
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        获取配置值
        
        Args:
            key: 配置键名
            default: 默认值
            
        Returns:
            配置值，如果不存在则返回默认值
        """
        config = self.load_config()
        value = config.get(key, default)
        log.debug(f"获取配置项 {key} = {value}")
        return value
    
    def get_data_dir(self) -> str:
        """
        获取数据目录路径
        
        Returns:
            数据目录的绝对路径
        """
        data_dir = self.get('data_dir', '../data')
        
        # 判断是否为绝对路径
        if os.path.isabs(data_dir):
            data_path = data_dir
        else:
            # 相对路径：相对于配置文件所在目录
            config_dir = os.path.dirname(self.config_file)
            data_path = os.path.join(config_dir, data_dir)
        
        # 自动创建数据文件夹
        os.makedirs(data_path, exist_ok=True)
        log.debug(f"数据目录路径: {data_path}")
        return data_path
    
    def reload(self):
        """重新加载配置文件"""
        log.info("重新加载配置文件")
        self._config_cache = None
        return self.load_config()


# 创建全局配置管理器实例
config_manager = ConfigManager()

# 便捷函数
def get_config() -> Dict[str, Any]:
    """获取配置字典"""
    return config_manager.load_config()

def get_data_dir() -> str:
    """获取数据目录路径"""
    return config_manager.get_data_dir()

def get_config_value(key: str, default: Any = None) -> Any:
    """获取配置值"""
    return config_manager.get(key, default)