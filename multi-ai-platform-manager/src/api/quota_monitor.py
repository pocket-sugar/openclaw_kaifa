"""
DeepSeek API额度监控模块
监控API使用情况，实现自动切换和续期
"""

import asyncio
import json
import logging
import time
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List, Tuple
import aiohttp

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class QuotaMonitor:
    """额度监控器"""
    
    def __init__(self, api_keys_file: str = "config/api_keys.json"):
        """
        初始化额度监控器
        
        Args:
            api_keys_file: API Key存储文件路径
        """
        self.api_keys_file = api_keys_file
        self.api_keys = self.load_api_keys()
        self.session: Optional[aiohttp.ClientSession] = None
        self.monitoring_interval = 300  # 监控间隔（秒），默认5分钟
        self.alert_threshold = 10  # 警报阈值（百分比），默认10%
        self.last_check_time = None
        
    def load_api_keys(self) -> List[Dict[str, Any]]:
        """加载API Keys"""
        try:
            if not self.api_keys_file or not os.path.exists(self.api_keys_file):
                logger.warning(f"API Key文件不存在: {self.api_keys_file}")
                return []
                
            with open(self.api_keys_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            # 只返回活跃的API Keys
            active_keys = [key for key in data if key.get("is_active", True)]
            logger.info(f"加载了 {len(active_keys)} 个活跃API Key")
            return active_keys
            
        except Exception as e:
            logger.error(f"加载API Keys失败: {e}")
            return []
            
    def save_api_keys(self):
        """保存API Keys"""
        try:
            os.makedirs(os.path.dirname(self.api_keys_file), exist_ok=True)
            with open(self.api_keys_file, 'w', encoding='utf-8') as f:
                json.dump(self.api_keys, f, indent=2, ensure_ascii=False)
            logger.debug(f"API Keys已保存到: {self.api_keys_file}")
        except Exception as e:
            logger.error(f"保存API Keys失败: {e}")
            
    async def check_quota(self, api_key: str) -> Optional[Dict[str, Any]]:
        """
        检查单个API Key的额度
        
        Args:
            api_key: DeepSeek API Key
            
        Returns:
            Optional[Dict]: 额度信息，包含总额度、已使用额度、剩余额度等
        """
        try:
            if not self.session:
                self.session = aiohttp.ClientSession()
                
            # DeepSeek API端点
            # 注意：实际API端点可能需要根据DeepSeek文档调整
            api_url = "https://api.deepseek.com/v1/usage"
            
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }
            
            async with self.session.get(api_url, headers=headers, timeout=30) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    # 解析额度信息
                    # 实际字段名需要根据DeepSeek API响应调整
                    quota_info = {
                        "api_key": api_key[:10] + "...",  # 只显示前10位
                        "total_quota": data.get("total_quota", 0),
                        "used_quota": data.get("used_quota", 0),
                        "remaining_quota": data.get("remaining_quota", 0),
                        "percentage_used": data.get("percentage_used", 0),
                        "percentage_remaining": data.get("percentage_remaining", 100),
                        "last_updated": datetime.now().isoformat(),
                        "status": "active"
                    }
                    
                    # 计算百分比（如果API未提供）
                    if quota_info["total_quota"] > 0:
                        if quota_info["percentage_used"] == 0:
                            quota_info["percentage_used"] = (quota_info["used_quota"] / quota_info["total_quota"]) * 100
                            quota_info["percentage_remaining"] = 100 - quota_info["percentage_used"]
                    
                    logger.info(f"API Key {api_key[:10]}... 额度: {quota_info['percentage_remaining']:.1f}% 剩余")
                    return quota_info
                    
                elif response.status == 401:
                    logger.warning(f"API Key无效或已过期: {api_key[:10]}...")
                    return {"api_key": api_key[:10] + "...", "status": "invalid", "error": "认证失败"}
                    
                elif response.status == 429:
                    logger.warning(f"API请求频率限制: {api_key[:10]}...")
                    return {"api_key": api_key[:10] + "...", "status": "rate_limited", "error": "请求频率限制"}
                    
                else:
                    logger.error(f"API请求失败 ({response.status}): {api_key[:10]}...")
                    return {"api_key": api_key[:10] + "...", "status": "error", "error": f"HTTP {response.status}"}
                    
        except asyncio.TimeoutError:
            logger.error(f"API请求超时: {api_key[:10]}...")
            return {"api_key": api_key[:10] + "...", "status": "timeout", "error": "请求超时"}
            
        except Exception as e:
            logger.error(f"检查额度失败 ({api_key[:10]}...): {e}")
            return {"api_key": api_key[:10] + "...", "status": "error", "error": str(e)}
            
    async def check_all_quotas(self) -> List[Dict[str, Any]]:
        """
        检查所有API Keys的额度
        
        Returns:
            List[Dict]: 所有API Keys的额度信息
        """
        if not self.api_keys:
            logger.warning("没有可用的API Key")
            return []
            
        logger.info(f"开始检查 {len(self.api_keys)} 个API Key的额度...")
        
        tasks = []
        for key_data in self.api_keys:
            api_key = key_data.get("api_key")
            if api_key:
                tasks.append(self.check_quota(api_key))
                
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 处理结果
        quota_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"检查额度时出错: {result}")
                continue
                
            if result:
                quota_results.append(result)
                
                # 更新API Key数据
                if i < len(self.api_keys):
                    self.api_keys[i]["quota_info"] = result
                    self.api_keys[i]["last_checked"] = datetime.now().isoformat()
                    
                    # 标记无效的API Key
                    if result.get("status") == "invalid":
                        self.api_keys[i]["is_active"] = False
                        logger.warning(f"标记API Key为无效: {result.get('api_key')}")
        
        # 保存更新后的数据
        self.save_api_keys()
        
        self.last_check_time = datetime.now()
        logger.info(f"额度检查完成: {len(quota_results)}/{len(self.api_keys)} 个成功")
        
        return quota_results
        
    def needs_renewal(self, quota_info: Dict[str, Any]) -> bool:
        """
        判断是否需要续期
        
        Args:
            quota_info: 额度信息
            
        Returns:
            bool: 是否需要续期
        """
        if quota_info.get("status") != "active":
            return True  # 无效或错误的API Key需要续期
            
        remaining_percent = quota_info.get("percentage_remaining", 100)
        return remaining_percent <= self.alert_threshold
        
    def get_key_needing_renewal(self) -> Optional[Dict[str, Any]]:
        """
        获取需要续期的API Key
        
        Returns:
            Optional[Dict]: 需要续期的API Key信息
        """
        for key_data in self.api_keys:
            quota_info = key_data.get("quota_info")
            if quota_info and self.needs_renewal(quota_info):
                return key_data
        return None
        
    def get_best_available_key(self) -> Optional[Dict[str, Any]]:
        """
        获取最佳可用API Key（剩余额度最多的）
        
        Returns:
            Optional[Dict]: 最佳API Key信息
        """
        available_keys = []
        
        for key_data in self.api_keys:
            if not key_data.get("is_active", True):
                continue
                
            quota_info = key_data.get("quota_info")
            if quota_info and quota_info.get("status") == "active":
                remaining = quota_info.get("percentage_remaining", 0)
                available_keys.append((remaining, key_data))
                
        if not available_keys:
            return None
            
        # 按剩余额度降序排序
        available_keys.sort(key=lambda x: x[0], reverse=True)
        return available_keys[0][1]
        
    async def monitor_loop(self, callback=None):
        """
        监控循环
        
        Args:
            callback: 回调函数，当需要续期时调用
        """
        logger.info("启动额度监控循环...")
        
        try:
            while True:
                logger.info(f"开始监控周期 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                
                # 检查所有额度
                quota_results = await self.check_all_quotas()
                
                # 检查是否需要续期
                key_needing_renewal = self.get_key_needing_renewal()
                if key_needing_renewal:
                    logger.warning(f"检测到需要续期的API Key: {key_needing_renewal.get('email', '未知')}")
                    
                    if callback:
                        await callback(key_needing_renewal)
                    else:
                        logger.info("需要续期，但未设置回调函数")
                        
                # 获取最佳可用Key
                best_key = self.get_best_available_key()
                if best_key:
                    quota_info = best_key.get("quota_info", {})
                    remaining = quota_info.get("percentage_remaining", 0)
                    logger.info(f"当前最佳API Key: {best_key.get('email', '未知')} - 剩余 {remaining:.1f}%")
                else:
                    logger.warning("没有可用的API Key")
                    
                # 等待下一个监控周期
                logger.info(f"等待 {self.monitoring_interval} 秒后进行下一次检查...")
                await asyncio.sleep(self.monitoring_interval)
                
        except KeyboardInterrupt:
            logger.info("监控循环被中断")
        except Exception as e:
            logger.error(f"监控循环出错: {e}")
        finally:
            if self.session:
                await self.session.close()
                
    def get_summary(self) -> Dict[str, Any]:
        """获取监控摘要"""
        total_keys = len(self.api_keys)
        active_keys = sum(1 for k in self.api_keys if k.get("is_active", True))
        
        # 统计额度情况
        quota_stats = {
            "excellent": 0,  # > 50%
            "good": 0,       # 20-50%
            "low": 0,        # 5-20%
            "critical": 0,   # < 5%
            "invalid": 0,    # 无效
        }
        
        for key_data in self.api_keys:
            if not key_data.get("is_active", True):
                quota_stats["invalid"] += 1
                continue
                
            quota_info = key_data.get("quota_info")
            if not quota_info:
                continue
                
            remaining = quota_info.get("percentage_remaining", 0)
            if remaining > 50:
                quota_stats["excellent"] += 1
            elif remaining > 20:
                quota_stats["good"] += 1
            elif remaining > 5:
                quota_stats["low"] += 1
            else:
                quota_stats["critical"] += 1
                
        return {
            "total_keys": total_keys,
            "active_keys": active_keys,
            "inactive_keys": total_keys - active_keys,
            "quota_stats": quota_stats,
            "last_check": self.last_check_time.isoformat() if self.last_check_time else None,
            "next_check_in": self.monitoring_interval,
            "alert_threshold": self.alert_threshold,
        }


class MockQuotaMonitor(QuotaMonitor):
    """模拟额度监控器（用于测试）"""
    
    async def check_quota(self, api_key: str) -> Optional[Dict[str, Any]]:
        """模拟检查额度"""
        logger.info(f"模拟检查API Key额度: {api_key[:10]}...")
        
        # 模拟API响应
        await asyncio.sleep(0.5)  # 模拟网络延迟
        
        # 生成随机额度数据
        import random
        total_quota = 1000000  # 1M tokens
        used_quota = random.randint(100000, 900000)
        remaining_quota = total_quota - used_quota
        percentage_used = (used_quota / total_quota) * 100
        percentage_remaining = 100 - percentage_used
        
        # 模拟10%的概率API Key无效
        if random.random() < 0.1:
            return {
                "api_key": api_key[:10] + "...",
                "status": "invalid",
                "error": "模拟：API Key无效"
            }
            
        return {
            "api_key": api_key[:10] + "...",
            "total_quota": total_quota,
            "used_quota": used_quota,
            "remaining_quota": remaining_quota,
            "percentage_used": percentage_used,
            "percentage_remaining": percentage_remaining,
            "last_updated": datetime.now().isoformat(),
            "status": "active"
        }


# 工厂函数
def create_quota_monitor(api_keys_file: str = "config/api_keys.json", mock: bool = False) -> QuotaMonitor:
    """创建额度监控器"""
    if mock:
        return MockQuotaMonitor(api_keys_file)
    return QuotaMonitor(api_keys_file)


async def demo():
    """演示函数"""
    print("额度监控模块演示")
    print("=" * 50)
    
    # 创建模拟监控器
    monitor = create_quota_monitor(mock=True)
    
    # 添加一些模拟API Keys
    monitor.api_keys = [
        {
            "email": "test1@example.com",
            "api_key": "sk-example-key",
            "is_active": True,
            "created_at": datetime.now().isoformat()
        },
        {
            "email": "test2@example.com",
            "api_key": "sk-example-key",
            "is_active": True,
            "created_at": datetime.now().isoformat()
        }
    ]
    
    # 检查额度
    print("检查API Key额度...")
    results = await monitor.check_all_quotas()
    
    for result in results:
        if result.get("status") == "active":
            remaining = result.get("percentage_remaining", 0)
            print(f"  ✅ {result['api_key']}: {remaining:.1f}% 剩余")
        else:
            print(f"  ❌ {result['api_key']}: {result.get('error', '未知错误')}")
    
    # 获取摘要
    summary = monitor.get_summary()
    print(f"\n监控摘要:")
    print(f"  总Key数: {summary['total_keys']}")
    print(f"  活跃Key数: {summary['active_keys']}")
    print(f"  额度状况: {summary['quota_stats']}")
    
    # 检查是否需要续期
    key_needing_renewal = monitor.get_key_needing_renewal()
    if key_needing_renewal:
        print(f"\n⚠️  需要续期: {key_needing_renewal.get('email')}")
    else:
        print(f"\n✅ 所有API Key额度充足")
        
    # 获取最佳可用Key
    best_key = monitor.get_best_available_key()
    if best_key:
        print(f"🎯 最佳可用Key: {best_key.get('email')}")


if __name__ == "__main__":
    import os
    import sys
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    
    # 运行演示
    asyncio.run(demo())