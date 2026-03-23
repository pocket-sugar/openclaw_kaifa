"""
智谱AI平台插件
支持智谱AI的自动化注册、API Key获取和额度管理
"""

from .registrar import ZhipuRegistrar
from .quota_monitor import ZhipuQuotaMonitor
from .config import ZhipuConfig

__all__ = ['ZhipuRegistrar', 'ZhipuQuotaMonitor', 'ZhipuConfig']

__version__ = '1.0.0'

def create_zhipu_platform(config_path=None):
    """
    创建智谱AI平台实例
    
    Args:
        config_path: 配置文件路径
        
    Returns:
        dict: 包含平台组件的字典
    """
    config = ZhipuConfig(config_path)
    
    return {
        'config': config,
        'registrar': ZhipuRegistrar(config),
        'quota_monitor': ZhipuQuotaMonitor(config),
        'name': '智谱AI',
        'version': __version__
    }