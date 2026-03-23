"""
智谱AI额度监控器
监控智谱AI API使用情况，实现智能续期
"""

import asyncio
import json
import logging
import time
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
import aiohttp

logger = logging.getLogger(__name__)


class ZhipuQuotaMonitor:
    """智谱AI额度监控器"""
    
    def __init__(self, config):
        """
        初始化额度监控器
        
        Args:
            config: 配置对象
        """
        self.config = config
        self.session: Optional[aiohttp.ClientSession] = None
        
        # 监控配置
        self.check_interval = 300  # 检查间隔（秒），默认5分钟
        self.alert_threshold = 10  # 警报阈值（百分比），默认10%
        self.min_quota_for_task = 10000  # 执行任务所需的最小额度
        
        # 历史数据
        self.quota_history = []
        self.last_check_time = None
        
        # 智谱AI API端点
        self.api_base = "https://open.bigmodel.cn/api/paas/v4"
        self.usage_endpoint = f"{self.api_base}/dashboard/usage"  # 需要确认实际端点
    
    async def check_quota(self, api_key: str) -> Optional[Dict[str, Any]]:
        """
        检查单个API Key的额度
        
        Args:
            api_key: 智谱AI API Key
            
        Returns:
            Optional[Dict]: 额度信息
        """
        try:
            if not self.session:
                self.session = aiohttp.ClientSession()
            
            # 智谱AI API调用（需要确认实际API）
            # 这里使用模拟数据，实际需要调用智谱AI的额度查询API
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }
            
            # 尝试调用额度查询API
            # 注意：需要确认智谱AI的实际额度查询端点
            async with self.session.get(self.usage_endpoint, headers=headers, timeout=30) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    # 解析智谱AI的额度信息
                    quota_info = self.parse_zhipu_quota(data, api_key)
                    
                    # 记录历史
                    self.record_quota_check(quota_info)
                    
                    return quota_info
                else:
                    logger.warning(f"❌ 额度查询失败: {response.status}")
                    
                    # 返回模拟数据（用于测试）
                    return self.get_mock_quota(api_key)
                    
        except Exception as e:
            logger.error(f"❌ 额度检查异常: {e}")
            
            # 返回模拟数据（用于测试）
            return self.get_mock_quota(api_key)
    
    def parse_zhipu_quota(self, data: Dict[str, Any], api_key: str) -> Dict[str, Any]:
        """
        解析智谱AI额度数据
        
        Args:
            data: API响应数据
            api_key: API Key
            
        Returns:
            Dict: 格式化的额度信息
        """
        # 智谱AI额度数据结构（需要根据实际API调整）
        # 假设返回格式：
        # {
        #   "total_quota": 1000000,
