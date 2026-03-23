"""
智谱AI注册器
自动化注册智谱AI账号并获取API Key
"""

import asyncio
import json
import logging
import re
import time
from typing import Optional, Dict, Any, Tuple
from datetime import datetime

logger = logging.getLogger(__name__)


class ZhipuRegistrar:
    """智谱AI注册器"""
    
    def __init__(self, config):
        """
        初始化智谱AI注册器
        
        Args:
            config: 配置对象
        """
        self.config = config
        self.browser = None
        self.page = None
        
        # 智谱AI特定配置
        self.base_url = "https://open.bigmodel.cn"
        self.register_url = f"{self.base_url}/usercenter/regist"
        self.login_url = f"{self.base_url}/usercenter/login"
        self.api_keys_url = f"{self.base_url}/usercenter/apikeys"
        
        # 注册成功率跟踪
        self.success_count = 0
        self.failure_count = 0
        self.last_registration_time = None
    
    async def start_browser(self):
        """启动浏览器"""
        try:
            # 使用现有的浏览器自动化框架
            from src.browser_automation.deepseek_registrar import create_deepseek_registrar
            
            self.browser = create_deepseek_registrar(headless=True)
            if await self.browser.start():
                logger.info("✅ 浏览器启动成功")
                return True
            else:
                logger.error("❌ 浏览器启动失败")
                return False
        except Exception as e:
            logger.error(f"❌ 浏览器启动异常: {e}")
            return False
    
    async def create_page(self):
        """创建页面"""
        try:
            if self.browser and await self.browser.create_page():
                self.page = self.browser.page
                logger.info("✅ 页面创建成功")
                return True
            return False
        except Exception as e:
            logger.error(f"❌ 页面创建失败: {e}")
            return False
    
    async def stop_browser(self):
        """停止浏览器"""
        try:
            if self.browser:
                await self.browser.stop()
                logger.info("✅ 浏览器已停止")
        except Exception as e:
            logger.error(f"❌ 浏览器停止异常: {e}")
    
    async def register_account(self, email: str, password: str) -> Tuple[bool, Optional[str]]:
        """
        注册智谱AI账号
        
        Args:
            email: 邮箱地址
            password: 密码
            
        Returns:
            Tuple[bool, Optional[str]]: (是否成功, 错误信息/API Key)
        """
        logger.info(f"开始注册智谱AI账号: {email}")
        
        try:
            # 1. 访问注册页面
            logger.info("1. 访问注册页面...")
            await self.page.goto(self.register_url, wait_until='networkidle')
            await asyncio.sleep(3)
            
            # 2. 填写注册表单
            logger.info("2. 填写注册表单...")
            
            # 查找邮箱输入框
            email_input = await self.page.query_selector('input[type="email"], input[name="email"]')
            if not email_input:
                # 尝试其他选择器
                email_input = await self.page.query_selector('input[placeholder*="邮箱"], input[placeholder*="email"]')
            
            if email_input:
                await email_input.fill(email)
                logger.info("   ✅ 填写邮箱")
                await asyncio.sleep(0.5)
            else:
                logger.warning("   ⚠️ 未找到邮箱输入框，尝试文本输入框")
                # 尝试所有输入框
                all_inputs = await self.page.query_selector_all('input[type="text"]')
                for input_elem in all_inputs[:3]:  # 尝试前3个
                    placeholder = await input_elem.get_attribute('placeholder') or ''
                    if '邮箱' in placeholder or 'email' in placeholder.lower():
                        await input_elem.fill(email)
                        logger.info("   ✅ 通过placeholder找到邮箱输入框")
                        break
            
            # 查找密码输入框
            password_input = await self.page.query_selector('input[type="password"]')
            if password_input:
                await password_input.fill(password)
                logger.info("   ✅ 填写密码")
                await asyncio.sleep(0.5)
            
            # 查找确认密码输入框
            confirm_password = await self.page.query_selector('input[type="password"]:nth-of-type(2)')
            if confirm_password:
                await confirm_password.fill(password)
                logger.info("   ✅ 填写确认密码")
                await asyncio.sleep(0.5)
            
            # 3. 处理验证码（如果有）
            logger.info("3. 处理验证码...")
            captcha_input = await self.page.query_selector('input[placeholder*="验证码"], input[placeholder*="code"]')
            if captcha_input:
                logger.warning("   ⚠️ 检测到验证码输入框，需要验证码识别")
                # 这里可以集成验证码识别
                # 暂时跳过，假设不需要验证码
                await asyncio.sleep(1)
            
            # 4. 同意条款
            logger.info("4. 同意条款...")
            agreement_checkbox = await self.page.query_selector('input[type="checkbox"]')
            if agreement_checkbox:
                await agreement_checkbox.click()
                logger.info("   ✅ 勾选同意条款")
                await asyncio.sleep(0.5)
            
            # 5. 提交注册
            logger.info("5. 提交注册...")
            submit_button = await self.page.query_selector('button[type="submit"], button:has-text("注册")')
            if submit_button:
                await submit_button.click()
                logger.info("   ✅ 点击注册按钮")
                await asyncio.sleep(5)  # 等待注册完成
            else:
                logger.warning("   ⚠️ 未找到注册按钮，尝试回车提交")
                await self.page.keyboard.press('Enter')
                await asyncio.sleep(5)
            
            # 6. 检查注册结果
            logger.info("6. 检查注册结果...")
            current_url = self.page.url
            
            # 判断注册是否成功
            if 'success' in current_url.lower() or 'complete' in current_url.lower():
                logger.info("   ✅ 注册成功（根据URL判断）")
                success = True
            else:
                # 检查页面内容
                content = await self.page.content()
                if '注册成功' in content or 'success' in content.lower():
                    logger.info("   ✅ 注册成功（根据页面内容判断）")
                    success = True
                elif '验证邮件' in content or 'verify' in content.lower():
                    logger.info("   ⚠️ 需要邮箱验证")
                    success = True  # 假设验证会成功
                else:
                    logger.warning("   ⚠️ 注册状态不确定")
                    success = True  # 暂时假设成功
            
            if success:
                # 7. 登录获取API Key
                logger.info("7. 登录获取API Key...")
                api_key = await self.get_api_key(email, password)
                
                if api_key:
                    self.success_count += 1
                    self.last_registration_time = datetime.now()
                    logger.info(f"🎉 智谱AI账号注册成功: {email}")
                    logger.info(f"   API Key: {api_key[:20]}...")
                    return True, api_key
                else:
                    logger.warning(f"⚠️  注册成功但获取API Key失败: {email}")
                    return False, "获取API Key失败"
            else:
                self.failure_count += 1
                logger.error(f"❌ 智谱AI账号注册失败: {email}")
                return False, "注册失败"
                
        except Exception as e:
            self.failure_count += 1
            logger.error(f"❌ 注册过程异常: {e}")
            return False, str(e)
    
    async def get_api_key(self, email: str, password: str) -> Optional[str]:
        """
        获取API Key
        
        Args:
            email: 邮箱
            password: 密码
            
        Returns:
            Optional[str]: API Key
        """
        try:
            # 1. 访问登录页面
            await self.page.goto(self.login_url, wait_until='networkidle')
            await asyncio.sleep(3)
            
            # 2. 填写登录表单
            email_input = await self.page.query_selector('input[type="email"], input[name="email"]')
            if email_input:
                await email_input.fill(email)
                await asyncio.sleep(0.5)
            
            password_input = await self.page.query_selector('input[type="password"]')
            if password_input:
                await password_input.fill(password)
                await asyncio.sleep(0.5)
            
            # 3. 提交登录
            submit_button = await self.page.query_selector('button[type="submit"], button:has-text("登录")')
            if submit_button:
                await submit_button.click()
                await asyncio.sleep(5)
            
            # 4. 访问API Keys页面
            await self.page.goto(self.api_keys_url, wait_until='networkidle')
            await asyncio.sleep(3)
            
            # 5. 提取API Key
            content = await self.page.content()
            
            # 尝试多种方式提取API Key
            api_key = self.extract_api_key(content)
            
            if api_key:
                logger.info(f"✅ 成功提取API Key: {api_key[:20]}...")
                return api_key
            else:
                logger.warning("⚠️ 未找到API Key，尝试创建新Key")
                # 尝试创建新API Key
                new_api_key = await self.create_api_key()
                return new_api_key
                
        except Exception as e:
            logger.error(f"❌ 获取API Key失败: {e}")
            return None
    
    def extract_api_key(self, content: str) -> Optional[str]:
        """
        从页面内容提取API Key
        
        Args:
            content: 页面HTML内容
            
        Returns:
            Optional[str]: API Key
        """
        # 智谱AI API Key模式
        patterns = [
            r'[a-zA-Z0-9]{32}\.[a-zA-Z0-9]{5,}',  # 智谱AI格式: 32位.5位+
            r'api[_-]?key["\']?\s*[:=]\s*["\']([a-zA-Z0-9\.]+)["\']',
            r'<code[^>]*>([a-zA-Z0-9\.]{40,})</code>',
            r'<pre[^>]*>([a-zA-Z0-9\.]{40,})</pre>',
            r'["\']([a-zA-Z0-9\.]{40,})["\']',
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, content)
            for match in matches:
                if isinstance(match, tuple):
                    match = match[0]
                # 验证可能是API Key
                if len(match) >= 30 and '.' in match:
                    logger.debug(f"找到可能的API Key: {match[:30]}...")
                    return match
        
        return None
    
    async def create_api_key(self) -> Optional[str]:
        """
        创建新的API Key
        
        Returns:
            Optional[str]: 新创建的API Key
        """
        try:
            # 查找创建API Key的按钮
            create_button = await self.page.query_selector('button:has-text("创建"), button:has-text("生成"), button:has-text("新建")')
            if create_button:
                await create_button.click()
                await asyncio.sleep(3)
                
                # 获取新创建的API Key
                content = await self.page.content()
                api_key = self.extract_api_key(content)
                
                if api_key:
                    logger.info(f"✅ 成功创建API Key: {api_key[:20]}...")
                    return api_key
                else:
                    logger.warning("⚠️ 创建了API Key但无法提取")
                    return None
            else:
                logger.warning("⚠️ 未找到创建API Key的按钮")
                return None
                
        except Exception as e:
            logger.error(f"❌ 创建API Key失败: {e}")
            return None
    
    async def test_registration_flow(self) -> bool:
        """
        测试注册流程
        
        Returns:
            bool: 测试是否成功
        """
        logger.info("🧪 测试智谱AI注册流程...")
        
        try:
            # 启动浏览器
            if not await self.start_browser():
                return False
            
            if not await self.create_page():
                await self.stop_browser()
                return False
            
            # 使用测试数据
            test_email = f"test_{int(time.time())}@test.com"
            test_password = "TestPassword123!"
            
            # 执行注册
            success, result = await self.register_account(test_email, test_password)
            
            # 停止浏览器
            await self.stop_browser()
            
            if success:
                logger.info(f"✅ 注册流程测试成功！API Key: {result[:20]}...")
                return True
            else:
                logger.error(f"❌ 注册流程测试失败: {result}")
                return False
                
        except Exception as e:
            logger.error(f"❌ 测试过程异常: {e}")
            await self.stop_browser()
            return False
    
    def get_stats(self) -> Dict[str, Any]:
        """
        获取统计信息
        
        Returns:
            Dict: 统计信息
        """
        total = self.success_count + self.failure_count
        success_rate = self.success_count / total if total > 0 else 0
        
        return {
            'success_count': self.success_count,
            'failure_count': self.failure_count,
            'total_attempts': total,
            'success_rate': success_rate,
            'last_registration_time': self.last_registration_time,
            'platform': '智谱AI'
        }