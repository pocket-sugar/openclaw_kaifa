"""
自动切换管理器
当API Key额度不足时自动注册新账号并切换
"""

import asyncio
import json
import logging
import os
import time
from datetime import datetime
from typing import Optional, Dict, Any, List, Callable

from src.api.quota_monitor import create_quota_monitor
from src.main import DeepSeekAutoRenew

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AutoSwitchManager:
    """自动切换管理器"""
    
    def __init__(self, config_path: str = "config/settings.json"):
        """
        初始化自动切换管理器
        
        Args:
            config_path: 配置文件路径
        """
        self.config_path = config_path
        self.config = self.load_config()
        
        # 初始化组件
        self.quota_monitor = create_quota_monitor(
            api_keys_file=self.config.get("api_key_storage", "config/api_keys.json"),
            mock=self.config.get("mock_mode", False)  # 测试模式下使用模拟器
        )
        
        self.auto_renew_system = DeepSeekAutoRenew(config_path)
        
        # 状态跟踪
        self.is_running = False
        self.total_renewals = 0
        self.successful_renewals = 0
        self.failed_renewals = 0
        self.last_renewal_time = None
        
        # 回调函数
        self.on_renewal_needed = None
        self.on_renewal_success = None
        self.on_renewal_failed = None
        self.on_key_switched = None
        
    def load_config(self) -> Dict[str, Any]:
        """加载配置"""
        default_config = {
            "monitoring_interval": 300,  # 监控间隔（秒）
            "alert_threshold": 10,       # 警报阈值（百分比）
            "min_usable_keys": 1,        # 最小可用Key数量
            "max_concurrent_renewals": 1, # 最大并发续期数
            "retry_attempts": 3,         # 重试次数
            "retry_delay": 60,           # 重试延迟（秒）
            "mock_mode": False,          # 模拟模式
            "enable_auto_switch": True,  # 启用自动切换
        }
        
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                user_config = json.load(f)
                default_config.update(user_config)
        except FileNotFoundError:
            logger.warning(f"配置文件不存在: {self.config_path}")
        except Exception as e:
            logger.error(f"加载配置文件失败: {e}")
            
        return default_config
        
    def save_config(self):
        """保存配置"""
        try:
            os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
            logger.debug(f"配置已保存到: {self.config_path}")
        except Exception as e:
            logger.error(f"保存配置失败: {e}")
            
    async def check_and_renew(self):
        """检查并续期"""
        logger.info("开始检查并续期流程...")
        
        # 检查所有API Key的额度
        quota_results = await self.quota_monitor.check_all_quotas()
        
        # 检查是否需要续期
        key_needing_renewal = self.quota_monitor.get_key_needing_renewal()
        
        if key_needing_renewal:
            logger.warning(f"检测到需要续期的API Key: {key_needing_renewal.get('email', '未知')}")
            
            # 触发续期需要的回调
            if self.on_renewal_needed:
                await self.on_renewal_needed(key_needing_renewal)
                
            # 执行续期
            success = await self.perform_renewal(key_needing_renewal)
            
            if success:
                logger.info("✅ 续期成功")
                self.successful_renewals += 1
                
                if self.on_renewal_success:
                    await self.on_renewal_success(key_needing_renewal)
            else:
                logger.error("❌ 续期失败")
                self.failed_renewals += 1
                
                if self.on_renewal_failed:
                    await self.on_renewal_failed(key_needing_renewal)
                    
            self.total_renewals += 1
            self.last_renewal_time = datetime.now()
            
        else:
            logger.info("✅ 所有API Key额度充足，无需续期")
            
        # 获取最佳可用Key
        best_key = self.quota_monitor.get_best_available_key()
        if best_key:
            quota_info = best_key.get("quota_info", {})
            remaining = quota_info.get("percentage_remaining", 0)
            logger.info(f"当前最佳API Key: {best_key.get('email', '未知')} - 剩余 {remaining:.1f}%")
            
            # 触发Key切换回调
            if self.on_key_switched and hasattr(self, 'last_best_key'):
                if self.last_best_key != best_key.get('email'):
                    await self.on_key_switched(self.last_best_key, best_key.get('email'))
                    
            self.last_best_key = best_key.get('email')
            
        return key_needing_renewal is not None
        
    async def perform_renewal(self, old_key_data: Dict[str, Any]) -> bool:
        """
        执行续期
        
        Args:
            old_key_data: 需要续期的旧Key数据
            
        Returns:
            bool: 续期是否成功
        """
        logger.info(f"开始续期流程 - 旧Key: {old_key_data.get('email', '未知')}")
        
        retry_attempts = self.config.get("retry_attempts", 3)
        retry_delay = self.config.get("retry_delay", 60)
        
        for attempt in range(retry_attempts):
            try:
                logger.info(f"续期尝试 {attempt + 1}/{retry_attempts}")
                
                # 注册新账号
                success, new_api_key, new_email = await self.auto_renew_system.register_new_account()
                
                if success and new_api_key:
                    logger.info(f"🎉 新账号注册成功: {new_email}")
                    
                    # 标记旧Key为不活跃
                    for i, key_data in enumerate(self.quota_monitor.api_keys):
                        if key_data.get("api_key") == old_key_data.get("api_key"):
                            self.quota_monitor.api_keys[i]["is_active"] = False
                            self.quota_monitor.api_keys[i]["deactivated_at"] = datetime.now().isoformat()
                            self.quota_monitor.api_keys[i]["deactivation_reason"] = "额度不足，自动续期"
                            logger.info(f"标记旧Key为不活跃: {old_key_data.get('email')}")
                            break
                    
                    # 保存更新
                    self.quota_monitor.save_api_keys()
                    
                    # 重新加载API Keys以包含新Key
                    self.quota_monitor.api_keys = self.quota_monitor.load_api_keys()
                    
                    return True
                else:
                    logger.warning(f"注册新账号失败，尝试 {attempt + 1}/{retry_attempts}")
                    
            except Exception as e:
                logger.error(f"续期过程中出错 (尝试 {attempt + 1}): {e}")
                
            # 如果不是最后一次尝试，等待后重试
            if attempt < retry_attempts - 1:
                logger.info(f"等待 {retry_delay} 秒后重试...")
                await asyncio.sleep(retry_delay)
                
        logger.error(f"续期失败，已达到最大重试次数 ({retry_attempts})")
        return False
        
    async def ensure_minimum_keys(self):
        """确保有最小数量的可用Key"""
        min_keys = self.config.get("min_usable_keys", 1)
        
        # 获取活跃Key数量
        active_keys = sum(1 for k in self.quota_monitor.api_keys if k.get("is_active", True))
        
        if active_keys < min_keys:
            logger.warning(f"活跃Key数量不足: {active_keys}/{min_keys}")
            
            # 需要注册新Key
            keys_to_register = min_keys - active_keys
            logger.info(f"需要注册 {keys_to_register} 个新Key")
            
            for i in range(keys_to_register):
                logger.info(f"注册第 {i + 1}/{keys_to_register} 个新Key...")
                
                success, api_key, email = await self.auto_renew_system.register_new_account()
                if success:
                    logger.info(f"✅ 新Key注册成功: {email}")
                else:
                    logger.error(f"❌ 新Key注册失败")
                    
            # 重新加载API Keys
            self.quota_monitor.api_keys = self.quota_monitor.load_api_keys()
            
        else:
            logger.info(f"活跃Key数量充足: {active_keys}/{min_keys}")
            
    async def monitoring_loop(self):
        """监控循环"""
        logger.info("启动自动切换监控循环...")
        logger.info(f"配置: {json.dumps(self.config, indent=2, ensure_ascii=False)}")
        
        self.is_running = True
        
        try:
            # 确保有最小数量的Key
            await self.ensure_minimum_keys()
            
            while self.is_running:
                logger.info(f"开始监控周期 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                
                # 检查并续期
                renewal_needed = await self.check_and_renew()
                
                if renewal_needed:
                    logger.info("续期完成，等待下一个监控周期")
                else:
                    logger.info("无需续期，继续监控")
                
                # 获取监控摘要
                summary = self.quota_monitor.get_summary()
                logger.info(f"监控摘要: {summary}")
                
                # 等待下一个监控周期
                interval = self.config.get("monitoring_interval", 300)
                logger.info(f"等待 {interval} 秒后进行下一次检查...")
                await asyncio.sleep(interval)
                
        except KeyboardInterrupt:
            logger.info("监控循环被用户中断")
        except Exception as e:
            logger.error(f"监控循环出错: {e}")
        finally:
            self.is_running = False
            logger.info("监控循环已停止")
            
    def stop(self):
        """停止监控"""
        logger.info("停止自动切换监控...")
        self.is_running = False
        
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {
            "is_running": self.is_running,
            "total_renewals": self.total_renewals,
            "successful_renewals": self.successful_renewals,
            "failed_renewals": self.failed_renewals,
            "success_rate": self.successful_renewals / self.total_renewals if self.total_renewals > 0 else 0,
            "last_renewal_time": self.last_renewal_time.isoformat() if self.last_renewal_time else None,
            "config": {
                "monitoring_interval": self.config.get("monitoring_interval"),
                "alert_threshold": self.config.get("alert_threshold"),
                "min_usable_keys": self.config.get("min_usable_keys"),
            }
        }


class MockAutoSwitchManager(AutoSwitchManager):
    """模拟自动切换管理器（用于测试）"""
    
    async def perform_renewal(self, old_key_data: Dict[str, Any]) -> bool:
        """模拟续期"""
        logger.info(f"模拟续期 - 旧Key: {old_key_data.get('email', '未知')}")
        
        # 模拟网络延迟
        await asyncio.sleep(2)
        
        # 90%的成功率
        import random
        success = random.random() < 0.9
        
        if success:
            logger.info("✅ 模拟续期成功")
            
            # 添加模拟的新Key
            new_key = {
                "email": f"mock_{int(time.time())}@example.com",
                "api_key": f"sk-mock{random.randint(100000, 999999)}",
                "is_active": True,
                "created_at": datetime.now().isoformat(),
                "quota_info": {
                    "percentage_remaining": 100,
                    "status": "active"
                }
            }
            
            self.quota_monitor.api_keys.append(new_key)
            self.quota_monitor.save_api_keys()
            
            return True
        else:
            logger.info("❌ 模拟续期失败")
            return False


# 工厂函数
def create_auto_switch_manager(config_path: str = "config/settings.json", mock: bool = False) -> AutoSwitchManager:
    """创建自动切换管理器"""
    if mock:
        return MockAutoSwitchManager(config_path)
    return AutoSwitchManager(config_path)


async def demo():
    """演示函数"""
    print("自动切换管理器演示")
    print("=" * 50)
    
    # 创建模拟管理器
    manager = create_auto_switch_manager(mock=True)
    
    # 设置回调函数
    async def on_renewal_needed(key_data):
        print(f"🔔 需要续期: {key_data.get('email')}")
        
    async def on_renewal_success(key_data):
        print(f"🎉 续期成功: {key_data.get('email')}")
        
    async def on_key_switched(old_key, new_key):
        print(f"🔄 Key切换: {old_key} -> {new_key}")
        
    manager.on_renewal_needed = on_renewal_needed
    manager.on_renewal_success = on_renewal_success
    manager.on_key_switched = on_key_switched
    
    # 添加一些模拟API Keys
    import random
    manager.quota_monitor.api_keys = [
        {
            "email": f"user{i}@example.com",
            "api_key": f"sk-test{i}{random.randint(1000, 9999)}",
            "is_active": True,
            "created_at": datetime.now().isoformat(),
            "quota_info": {
                "percentage_remaining": random.randint(5, 100),  # 模拟不同额度
                "status": "active"
            }
        }
        for i in range(3)
    ]
    
    print("初始API Keys:")
    for key in manager.quota_monitor.api_keys:
        remaining = key.get("quota_info", {}).get("percentage_remaining", 0)
        print(f"  • {key['email']}: {remaining}% 剩余")
    
    print("\n运行一次检查并续期...")
    await manager.check_and_renew()
    
    print("\n获取统计信息:")
    stats = manager.get_stats()
    for key, value in stats.items():
        if key != "config":
            print(f"  {key}: {value}")
            
    print("\n✅ 演示完成")


if __name__ == "__main__":
    import sys
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    
    # 运行演示
    asyncio.run(demo())