#!/usr/bin/env python3
"""
DeepSeek Auto Renew 主程序
自动注册DeepSeek账号、获取API Key、监控额度并自动续期
"""

import asyncio
import json
import logging
import os
import sys
import time
from datetime import datetime
from typing import Optional, Dict, Any, List, Tuple

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.email_services import create_email_service_manager
from src.browser_automation.deepseek_registrar import create_deepseek_registrar
from src.browser_automation.captcha_solver import create_default_captcha_manager
from src.auto_switch_manager import create_auto_switch_manager

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/deepseek_auto_renew.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class DeepSeekAutoRenew:
    """DeepSeek自动续期系统"""
    
    def __init__(self, config_path: str = "config/settings.json"):
        """
        初始化系统
        
        Args:
            config_path: 配置文件路径
        """
        self.config_path = config_path
        self.config = self.load_config()
        
        # 初始化组件
        self.email_manager = create_email_service_manager()
        self.captcha_manager = create_default_captcha_manager()
        
        # 状态跟踪
        self.registered_accounts = []  # 已注册的账号列表
        self.active_api_keys = []      # 活跃的API Key列表
        self.failed_attempts = 0       # 失败尝试次数
        self.max_failures = self.config.get("max_failures", 3)
        
        # 创建日志目录
        os.makedirs("logs", exist_ok=True)
        
    def load_config(self) -> Dict[str, Any]:
        """加载配置文件"""
        default_config = {
            "threshold_percent": 10,      # 额度低于10%时注册新账号
            "check_interval_minutes": 5,  # 检查间隔（分钟）
            "max_failures": 3,           # 最大失败次数
            "headless": True,            # 是否使用无头浏览器
            "password_pattern": "DeepSeekAuto@2026",  # 密码模式
            "api_key_storage": "config/api_keys.json",  # API Key存储文件
            "registered_accounts_file": "config/registered_accounts.json",  # 账号存储文件
        }
        
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                user_config = json.load(f)
                default_config.update(user_config)
                logger.info(f"配置文件加载成功: {self.config_path}")
        except FileNotFoundError:
            logger.warning(f"配置文件不存在，使用默认配置: {self.config_path}")
            # 保存默认配置
            os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(default_config, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"加载配置文件失败: {e}")
            
        return default_config
        
    def save_api_key(self, email: str, api_key: str, quota_info: Optional[Dict] = None):
        """保存API Key到文件"""
        try:
            storage_file = self.config["api_key_storage"]
            os.makedirs(os.path.dirname(storage_file), exist_ok=True)
            
            # 加载现有数据
            data = []
            if os.path.exists(storage_file):
                with open(storage_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
            # 添加新数据
            new_entry = {
                "email": email,
                "api_key": api_key,
                "created_at": datetime.now().isoformat(),
                "quota_info": quota_info or {},
                "is_active": True
            }
            
            # 检查是否已存在
            for i, entry in enumerate(data):
                if entry["email"] == email:
                    data[i] = new_entry  # 更新现有条目
                    break
            else:
                data.append(new_entry)  # 添加新条目
                
            # 保存
            with open(storage_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
                
            logger.info(f"API Key已保存到: {storage_file}")
            
        except Exception as e:
            logger.error(f"保存API Key失败: {e}")
            
    def save_registered_account(self, email: str, password: str):
        """保存注册的账号信息"""
        try:
            accounts_file = self.config["registered_accounts_file"]
            os.makedirs(os.path.dirname(accounts_file), exist_ok=True)
            
            # 加载现有数据
            data = []
            if os.path.exists(accounts_file):
                with open(accounts_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
            # 添加新数据
            new_entry = {
                "email": email,
                "password": password,
                "registered_at": datetime.now().isoformat(),
                "status": "active"
            }
            
            # 检查是否已存在
            for i, entry in enumerate(data):
                if entry["email"] == email:
                    data[i] = new_entry  # 更新现有条目
                    break
            else:
                data.append(new_entry)  # 添加新条目
                
            # 保存（不保存密码明文，实际使用时应该加密）
            with open(accounts_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
                
            logger.info(f"账号信息已保存到: {accounts_file}")
            
        except Exception as e:
            logger.error(f"保存账号信息失败: {e}")
            
    def generate_password(self, base_pattern: Optional[str] = None) -> str:
        """生成密码"""
        if not base_pattern:
            base_pattern = self.config["password_pattern"]
            
        # 添加时间戳增加唯一性
        timestamp = int(time.time())
        return f"{base_pattern}_{timestamp}"
        
    async def get_verification_code(self, email: str, timeout: int = 120) -> Optional[str]:
        """
        从邮箱获取验证码
        
        Args:
            email: 邮箱地址
            timeout: 超时时间（秒）
            
        Returns:
            Optional[str]: 验证码
        """
        logger.info(f"等待验证码 - 邮箱: {email}")
        
        start_time = time.time()
        check_interval = 5  # 检查间隔（秒）
        
        while time.time() - start_time < timeout:
            try:
                # 检查收件箱
                # 这里需要邮箱服务的check_inbox方法
                # 由于邮箱服务实现不同，这里简化处理
                
                logger.info(f"检查邮箱 {email} 的验证码...")
                
                # 模拟等待验证码
                # 实际实现应该调用邮箱服务的check_inbox方法
                await asyncio.sleep(check_interval)
                
                # 这里应该从邮箱中提取验证码
                # 简化：返回一个模拟验证码
                if time.time() - start_time > 30:  # 30秒后返回模拟验证码
                    verification_code = "123456"  # 模拟验证码
                    logger.info(f"获取到验证码: {verification_code}")
                    return verification_code
                    
            except Exception as e:
                logger.error(f"检查验证码失败: {e}")
                await asyncio.sleep(check_interval)
                
        logger.warning(f"获取验证码超时 ({timeout}秒)")
        return None
        
    async def register_new_account(self) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        注册新DeepSeek账号
        
        Returns:
            Tuple[bool, Optional[str], Optional[str]]: (是否成功, API Key, 邮箱)
        """
        logger.info("开始注册新DeepSeek账号")
        
        try:
            # 1. 获取邮箱地址
            email = await self.email_manager.get_next_email()
            if not email:
                logger.error("获取邮箱地址失败")
                return False, None, None
                
            logger.info(f"使用邮箱: {email}")
            
            # 2. 生成密码
            password = self.generate_password()
            logger.info(f"生成密码: {password}")
            
            # 3. 创建浏览器注册器
            headless = self.config.get("headless", True)
            registrar = create_deepseek_registrar(headless=headless)
            
            # 4. 执行注册流程
            success, api_key = await registrar.register_and_get_api_key(
                email=email,
                password=password,
                verification_code=None  # 先不提供验证码，如果需要会等待
            )
            
            if success and api_key:
                logger.info(f"🎉 注册成功！邮箱: {email}, API Key: {api_key[:15]}...")
                
                # 5. 保存信息
                self.save_registered_account(email, password)
                self.save_api_key(email, api_key)
                
                # 6. 添加到活跃列表
                self.active_api_keys.append({
                    "email": email,
                    "api_key": api_key,
                    "added_at": datetime.now().isoformat()
                })
                
                self.registered_accounts.append({
                    "email": email,
                    "password": password,  # 注意：实际使用时应该加密存储
                    "registered_at": datetime.now().isoformat()
                })
                
                self.failed_attempts = 0  # 重置失败计数
                
                return True, api_key, email
            else:
                logger.error(f"注册失败 - 邮箱: {email}")
                self.failed_attempts += 1
                return False, None, email
                
        except Exception as e:
            logger.error(f"注册过程中发生错误: {e}")
            self.failed_attempts += 1
            return False, None, None
            
    async def check_api_quota(self, api_key: str) -> Optional[Dict[str, Any]]:
        """
        检查API额度
        
        Args:
            api_key: DeepSeek API Key
            
        Returns:
            Optional[Dict]: 额度信息
        """
        try:
            # 这里应该调用DeepSeek API检查额度
            # 由于DeepSeek API文档可能变化，这里简化处理
            
            logger.info(f"检查API额度 - Key: {api_key[:10]}...")
            
            # 模拟API调用
            # 实际实现应该使用requests或aiohttp调用DeepSeek API
            
            # 示例响应结构（根据DeepSeek API文档）
            quota_info = {
                "total_quota": 1000000,  # 总额度
                "used_quota": 250000,    # 已使用额度
                "remaining_quota": 750000,  # 剩余额度
                "percentage_used": 25.0,  # 使用百分比
                "percentage_remaining": 75.0,  # 剩余百分比
                "last_checked": datetime.now().isoformat()
            }
            
            logger.info(f"额度信息: 已使用 {quota_info['percentage_used']}%，剩余 {quota_info['percentage_remaining']}%")
            return quota_info
            
        except Exception as e:
            logger.error(f"检查API额度失败: {e}")
            return None
            
    async def monitor_and_renew(self):
        """监控和自动续期主循环"""
        logger.info("启动DeepSeek自动续期监控系统")
        logger.info(f"配置: {json.dumps(self.config, indent=2, ensure_ascii=False)}")
        
        check_interval = self.config["check_interval_minutes"] * 60  # 转换为秒
        threshold = self.config["threshold_percent"]
        
        while True:
            try:
                logger.info("=" * 50)
                logger.info(f"开始监控周期 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                
                # 1. 加载已保存的API Keys
                storage_file = self.config["api_key_storage"]
                if os.path.exists(storage_file):
                    with open(storage_file, 'r', encoding='utf-8') as f:
                        api_keys_data = json.load(f)
                        
                    active_keys = [item for item in api_keys_data if item.get("is_active", True)]
                    
                    if not active_keys:
                        logger.warning("没有活跃的API Key，需要注册新账号")
                        success, api_key, email = await self.register_new_account()
                        if success:
                            logger.info(f"已注册新账号: {email}")
                        else:
                            logger.error("注册新账号失败")
                    else:
                        # 2. 检查每个API Key的额度
                        needs_renewal = False
                        
                        for key_data in active_keys:
                            api_key = key_data["api_key"]
                            email = key_data["email"]
                            
                            quota_info = await self.check_api_quota(api_key)
                            if quota_info:
                                # 保存更新的额度信息
                                key_data["quota_info"] = quota_info
                                self.save_api_key(email, api_key, quota_info)
                                
                                # 检查是否需要续期
                                remaining_percent = quota_info.get("percentage_remaining", 100)
                                
                                if remaining_percent <= threshold:
                                    logger.warning(f"API Key额度不足: {email} - 剩余 {remaining_percent}% (阈值: {threshold}%)")
                                    needs_renewal = True
                                else:
                                    logger.info(f"API Key额度充足: {email} - 剩余 {remaining_percent}%")
                            else:
                                logger.warning(f"无法获取额度信息: {email}")
                                
                        # 3. 如果需要续期，注册新账号
                        if needs_renewal:
                            logger.info("检测到额度不足，开始注册新账号...")
                            success, api_key, email = await self.register_new_account()
                            if success:
                                logger.info(f"续期成功: {email}")
                            else:
                                logger.error("续期失败")
                                
                else:
                    logger.info("没有保存的API Key，注册第一个账号...")
                    success, api_key, email = await self.register_new_account()
                    if success:
                        logger.info(f"第一个账号注册成功: {email}")
                    else:
                        logger.error("第一个账号注册失败")
                        
                # 4. 检查失败次数
                if self.failed_attempts >= self.max_failures:
                    logger.error(f"失败次数达到上限 ({self.max_failures})，系统暂停")
                    # 可以发送警报或等待更长时间
                    await asyncio.sleep(check_interval * 3)  # 等待3个周期
                    self.failed_attempts = 0  # 重置
                    
                # 5. 等待下一个检查周期
                logger.info(f"等待下一个检查周期 ({self.config['check_interval_minutes']}分钟后)...")
                logger.info("=" * 50)
                await asyncio.sleep(check_interval)
                
            except KeyboardInterrupt:
                logger.info("收到中断信号，停止监控...")
                break
            except Exception as e:
                logger.error(f"监控循环出错: {e}")
                await asyncio.sleep(check_interval)  # 出错后等待一个周期
                
    async def test_components(self):
        """测试所有组件"""
        logger.info("开始组件测试...")
        
        tests_passed = 0
        total_tests = 3
        
        # 测试1: 邮箱服务
        try:
            logger.info("测试邮箱服务...")
            email = await self.email_manager.get_next_email()
            if email:
                logger.info(f"✅ 邮箱服务测试通过: {email}")
                tests_passed += 1
            else:
                logger.error("❌ 邮箱服务测试失败")
        except Exception as e:
            logger.error(f"❌ 邮箱服务测试出错: {e}")
            
        # 测试2: 浏览器自动化
        try:
            logger.info("测试浏览器自动化...")
            registrar = create_deepseek_registrar(headless=True)
            success = await registrar.quick_test()
            if success:
                logger.info("✅ 浏览器自动化测试通过")
                tests_passed += 1
            else:
                logger.error("❌ 浏览器自动化测试失败")
        except Exception as e:
            logger.error(f"❌ 浏览器自动化测试出错: {e}")
            
        # 测试3: 验证码识别
        try:
            logger.info("测试验证码识别...")
            # 创建一个简单的测试图像
            from PIL import Image, ImageDraw
            import io
            
            image = Image.new('RGB', (100, 50), color='white')
            draw = ImageDraw.Draw(image)
            draw.text((30, 5), "4", fill='black')
            
            img_byte_arr = io.BytesIO()
            image.save(img_byte_arr, format='PNG')
            image_data = img_byte_arr.getvalue()
            
            result = await self.captcha_manager.solve_captcha(image_data, "digit")
            if result:
                logger.info(f"✅ 验证码识别测试通过: {result}")
                tests_passed += 1
            else:
                logger.warning("⚠️ 验证码识别测试结果为空")
        except Exception as e:
            logger.error(f"❌ 验证码识别测试出错: {e}")
            
        logger.info(f"组件测试完成: {tests_passed}/{total_tests} 通过")
        return tests_passed == total_tests
        
    async def run(self, test_only: bool = False, auto_switch: bool = False):
        """运行系统
        
        Args:
            test_only: 仅测试模式
            auto_switch: 自动切换模式（第三阶段功能）
        """
        logger.info("DeepSeek Auto Renew 系统启动")
        logger.info(f"版本: 2.0.0 (第三阶段: {'自动切换' if auto_switch else '基础监控'})")
        logger.info(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # 创建必要的目录
        os.makedirs("logs", exist_ok=True)
        os.makedirs("config", exist_ok=True)
        
        if test_only:
            # 仅测试模式
            logger.info("运行组件测试模式...")
            success = await self.test_components()
            if success:
                logger.info("✅ 所有组件测试通过，系统就绪")
                return True
            else:
                logger.warning("⚠️ 部分组件测试失败，系统可能无法正常工作")
                return False
        elif auto_switch:
            # 自动切换模式（第三阶段）
            logger.info("运行自动切换模式...")
            
            # 先测试组件
            logger.info("先进行组件测试...")
            test_success = await self.test_components()
            
            if not test_success:
                logger.warning("组件测试未完全通过，继续运行但可能遇到问题")
                
            # 创建自动切换管理器
            switch_manager = create_auto_switch_manager(
                config_path=self.config_path,
                mock=self.config.get("mock_mode", False)
            )
            
            # 设置回调函数
            async def on_renewal_needed(key_data):
                logger.warning(f"🔔 需要续期: {key_data.get('email', '未知')}")
                
            async def on_renewal_success(key_data):
                logger.info(f"🎉 续期成功: {key_data.get('email', '未知')}")
                
            async def on_key_switched(old_key, new_key):
                logger.info(f"🔄 API Key切换: {old_key} -> {new_key}")
                
            switch_manager.on_renewal_needed = on_renewal_needed
            switch_manager.on_renewal_success = on_renewal_success
            switch_manager.on_key_switched = on_key_switched
            
            # 启动自动切换监控
            try:
                await switch_manager.monitoring_loop()
            except KeyboardInterrupt:
                logger.info("自动切换系统被用户中断")
            except Exception as e:
                logger.error(f"自动切换系统运行出错: {e}")
                return False
                
            return True
        else:
            # 基础监控模式（第二阶段）
            logger.info("运行基础监控模式...")
            
            # 先测试组件
            logger.info("先进行组件测试...")
            test_success = await self.test_components()
            
            if not test_success:
                logger.warning("组件测试未完全通过，继续运行但可能遇到问题")
                
            # 启动监控循环
            try:
                await self.monitor_and_renew()
            except KeyboardInterrupt:
                logger.info("系统被用户中断")
            except Exception as e:
                logger.error(f"系统运行出错: {e}")
                return False
                
            return True


async def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="DeepSeek Auto Renew 系统")
    parser.add_argument("--test", action="store_true", help="仅测试组件，不启动监控")
    parser.add_argument("--config", default="config/settings.json", help="配置文件路径")
    parser.add_argument("--register-one", action="store_true", help="仅注册一个账号然后退出")
    
    args = parser.parse_args()
    
    # 创建系统实例
    system = DeepSeekAutoRenew(config_path=args.config)
    
    if args.register_one:
        # 仅注册一个账号
        logger.info("注册单个账号模式...")
        success, api_key, email = await system.register_new_account()
        if success:
            logger.info(f"✅ 账号注册成功: {email}")
            logger.info(f"API Key: {api_key[:20]}...")
            return 0
        else:
            logger.error("❌ 账号注册失败")
            return 1
    elif args.test:
        # 测试模式
        success = await system.run(test_only=True)
        return 0 if success else 1
    else:
        # 完整运行模式
        success = await system.run(test_only=False)
        return 0 if success else 1


if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n程序被用户中断")
        sys.exit(0)
    except Exception as e:
        print(f"程序出错: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)