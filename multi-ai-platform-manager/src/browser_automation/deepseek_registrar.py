"""
DeepSeek注册自动化
负责通过浏览器自动化注册DeepSeek账号并获取API Key
"""

import asyncio
import re
import time
import os
from typing import Optional, Dict, Any, Tuple
from playwright.async_api import async_playwright, Page, Browser, BrowserContext
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DeepSeekRegistrar:
    """DeepSeek注册器"""
    
    def __init__(self, headless: bool = True):
        """
        初始化DeepSeek注册器
        
        Args:
            headless: 是否使用无头模式
        """
        self.headless = headless
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        self.playwright = None
        
        # DeepSeek URLs
        self.register_url = "https://platform.deepseek.com/signup"
        self.login_url = "https://platform.deepseek.com/login"
        self.api_keys_url = "https://platform.deepseek.com/api_keys"
        
        # 注册表单字段选择器
        self.selectors = {
            "email_input": "input[name='email'], input[type='email']",
            "password_input": "input[name='password'], input[type='password']",
            "confirm_password_input": "input[name='confirmPassword']",
            "agree_terms": "input[name='agreeTerms'], input[type='checkbox']",
            "submit_button": "button[type='submit'], button:has-text('注册'), button:has-text('Sign Up')",
            "verification_code_input": "input[name='verificationCode'], input[type='text']",
            "verify_button": "button:has-text('验证'), button:has-text('Verify')",
            "login_email": "input[name='email'], input[type='email']",
            "login_password": "input[name='password'], input[type='password']",
            "login_button": "button:has-text('登录'), button:has-text('Login')",
            "api_keys_section": "//*[contains(text(), 'API Keys') or contains(text(), 'API密钥')]",
            "create_api_key_button": "button:has-text('Create API Key'), button:has-text('创建API密钥')",
            "api_key_name_input": "input[name='keyName'], input[placeholder*='name']",
            "confirm_create_button": "button:has-text('Confirm'), button:has-text('确认')",
            "api_key_value": "//*[contains(@class, 'api-key-value') or contains(text(), 'sk-example-key')]",
            "copy_button": "button:has-text('Copy'), button:has-text('复制')",
        }
        
    async def __aenter__(self):
        """异步上下文管理器入口"""
        await self.start()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口"""
        await self.stop()
        
    async def start(self):
        """启动浏览器"""
        try:
            self.playwright = await async_playwright().start()
            
            # 尝试使用系统Chromium
            chromium_paths = [
                "/usr/bin/chromium",
                "/usr/bin/chromium-browser",
                "/usr/bin/google-chrome",
            ]
            
            executable_path = None
            for path in chromium_paths:
                if os.path.exists(path):
                    executable_path = path
                    print(f"✅ 找到系统浏览器: {path}")
                    break
            
            launch_args = {
                "headless": self.headless,
                "args": [
                    '--disable-blink-features=AutomationControlled',
                    '--disable-dev-shm-usage',
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                    '--disable-web-security',
                    '--disable-features=IsolateOrigins,site-per-process',
                    '--disable-site-isolation-trials',
                ]
            }
            
            if executable_path:
                launch_args["executable_path"] = executable_path
                print(f"使用系统浏览器: {executable_path}")
            else:
                print("使用Playwright内置浏览器")
            
            # 启动浏览器
            self.browser = await self.playwright.chromium.launch(**launch_args)
            
            # 创建上下文，模拟真实用户
            self.context = await self.browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                locale='zh-CN',
                timezone_id='Asia/Shanghai',
                permissions=['clipboard-read', 'clipboard-write'],
            )
            
            # 添加随机鼠标移动和点击延迟
            await self.context.add_init_script("""
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                });
                
                // 覆盖plugins属性
                Object.defineProperty(navigator, 'plugins', {
                    get: () => [1, 2, 3, 4, 5]
                });
                
                // 覆盖languages属性
                Object.defineProperty(navigator, 'languages', {
                    get: () => ['zh-CN', 'zh', 'en-US', 'en']
                });
            """)
            
            logger.info("浏览器启动成功")
            return True
            
        except Exception as e:
            logger.error(f"启动浏览器失败: {e}")
            await self.stop()
            return False
            
    async def stop(self):
        """停止浏览器"""
        try:
            if self.page:
                await self.page.close()
                self.page = None
                
            if self.context:
                await self.context.close()
                self.context = None
                
            if self.browser:
                await self.browser.close()
                self.browser = None
                
            if self.playwright:
                await self.playwright.stop()
                self.playwright = None
                
            logger.info("浏览器已停止")
            
        except Exception as e:
            logger.error(f"停止浏览器时出错: {e}")
            
    async def create_page(self) -> bool:
        """创建新页面"""
        try:
            if not self.context:
                logger.error("浏览器上下文未初始化")
                return False
                
            self.page = await self.context.new_page()
            
            # 设置页面超时
            self.page.set_default_timeout(30000)  # 30秒
            
            # 随机延迟，模拟人类行为
            await self.page.add_init_script("""
                // 随机延迟函数
                window.randomDelay = async (min=100, max=1000) => {
                    const delay = Math.floor(Math.random() * (max - min + 1)) + min;
                    await new Promise(resolve => setTimeout(resolve, delay));
                };
                
                // 随机鼠标移动
                window.randomMouseMove = async (element) => {
                    if (element) {
                        const rect = element.getBoundingClientRect();
                        const x = rect.left + Math.random() * rect.width;
                        const y = rect.top + Math.random() * rect.height;
                        
                        // 模拟鼠标移动轨迹
                        const steps = 5;
                        for (let i = 0; i <= steps; i++) {
                            const progress = i / steps;
                            const currentX = window.innerWidth * Math.random() * progress;
                            const currentY = window.innerHeight * Math.random() * progress;
                            
                            // 触发mousemove事件
                            const event = new MouseEvent('mousemove', {
                                view: window,
                                bubbles: true,
                                cancelable: true,
                                clientX: currentX,
                                clientY: currentY
                            });
                            element.dispatchEvent(event);
                            
                            await window.randomDelay(50, 200);
                        }
                    }
                };
            """)
            
            logger.info("页面创建成功")
            return True
            
        except Exception as e:
            logger.error(f"创建页面失败: {e}")
            return False
            
    async def human_delay(self, min_ms: int = 500, max_ms: int = 2000):
        """人类行为延迟"""
        delay = (max_ms - min_ms) * (hash(str(time.time())) % 100) / 100 + min_ms
        await asyncio.sleep(delay / 1000)
        
    async def random_mouse_move(self, element=None):
        """随机鼠标移动"""
        if element and self.page:
            try:
                # 获取元素位置
                box = await element.bounding_box()
                if box:
                    # 在元素周围随机移动
                    x = box['x'] + box['width'] * 0.3 + (hash(str(time.time())) % 100) * box['width'] * 0.004
                    y = box['y'] + box['height'] * 0.3 + (hash(str(time.time())) % 100) * box['height'] * 0.004
                    
                    # 移动鼠标
                    await self.page.mouse.move(x, y)
                    await self.human_delay(100, 300)
            except:
                pass  # 忽略鼠标移动错误
                
    async def navigate_to_register(self) -> bool:
        """导航到注册页面"""
        try:
            if not await self.create_page():
                return False
                
            logger.info(f"导航到注册页面: {self.register_url}")
            await self.page.goto(self.register_url, wait_until='networkidle')
            
            # 等待页面加载
            await self.page.wait_for_load_state('networkidle')
            await self.human_delay(1000, 3000)
            
            # 检查是否成功加载注册页面
            page_title = await self.page.title()
            logger.info(f"页面标题: {page_title}")
            
            # 检查是否有注册表单
            email_input = await self.page.query_selector(self.selectors["email_input"])
            if email_input:
                logger.info("注册页面加载成功")
                return True
            else:
                logger.warning("未找到注册表单，可能页面结构已变化")
                # 尝试截图
                await self.page.screenshot(path='debug_register_page.png')
                return False
                
        except Exception as e:
            logger.error(f"导航到注册页面失败: {e}")
            return False
            
    async def fill_registration_form(self, email: str, password: str) -> bool:
        """填写注册表单"""
        try:
            logger.info(f"填写注册表单 - 邮箱: {email}")
            
            # 等待表单加载
            await self.page.wait_for_selector(self.selectors["email_input"], state='visible')
            
            # 1. 填写邮箱
            email_input = await self.page.query_selector(self.selectors["email_input"])
            if email_input:
                await self.random_mouse_move(email_input)
                await email_input.click()
                await self.human_delay(200, 500)
                await email_input.fill(email)
                await self.human_delay(300, 800)
            else:
                logger.error("未找到邮箱输入框")
                return False
                
            # 2. 填写密码
            password_input = await self.page.query_selector(self.selectors["password_input"])
            if password_input:
                await self.random_mouse_move(password_input)
                await password_input.click()
                await self.human_delay(200, 500)
                await password_input.fill(password)
                await self.human_delay(300, 800)
            else:
                logger.error("未找到密码输入框")
                return False
                
            # 3. 确认密码（如果有）
            confirm_password_input = await self.page.query_selector(self.selectors["confirm_password_input"])
            if confirm_password_input:
                await self.random_mouse_move(confirm_password_input)
                await confirm_password_input.click()
                await self.human_delay(200, 500)
                await confirm_password_input.fill(password)
                await self.human_delay(300, 800)
                
            # 4. 同意条款（如果有）
            agree_terms = await self.page.query_selector(self.selectors["agree_terms"])
            if agree_terms:
                await self.random_mouse_move(agree_terms)
                await agree_terms.click()
                await self.human_delay(200, 500)
                
            logger.info("注册表单填写完成")
            return True
            
        except Exception as e:
            logger.error(f"填写注册表单失败: {e}")
            return False
            
    async def submit_registration(self) -> bool:
        """提交注册表单"""
        try:
            logger.info("提交注册表单")
            
            # 查找提交按钮
            submit_button = await self.page.query_selector(self.selectors["submit_button"])
            if not submit_button:
                # 尝试通过文本查找
                submit_button = await self.page.query_selector("button:has-text('注册')")
                if not submit_button:
                    submit_button = await self.page.query_selector("button:has-text('Sign Up')")
                    
            if submit_button:
                await self.random_mouse_move(submit_button)
                await submit_button.click()
                await self.human_delay(1000, 3000)
                
                # 等待响应
                try:
                    # 等待页面跳转或出现验证码输入框
                    await self.page.wait_for_load_state('networkidle', timeout=10000)
                    
                    # 检查是否出现验证码输入框
                    verification_input = await self.page.query_selector(self.selectors["verification_code_input"])
                    if verification_input:
                        logger.info("需要邮箱验证码")
                        return True
                        
                    # 检查是否注册成功（跳转到其他页面）
                    current_url = self.page.url
                    if 'login' in current_url or 'dashboard' in current_url:
                        logger.info("注册成功，已跳转")
                        return True
                        
                except:
                    pass  # 超时是正常的
                    
                logger.info("注册表单已提交")
                return True
            else:
                logger.error("未找到提交按钮")
                return False
                
        except Exception as e:
            logger.error(f"提交注册表单失败: {e}")
            return False
            
    async def enter_verification_code(self, code: str) -> bool:
        """输入验证码"""
        try:
            logger.info(f"输入验证码: {code}")
            
            # 等待验证码输入框
            verification_input = await self.page.wait_for_selector(
                self.selectors["verification_code_input"],
                state='visible',
                timeout=10000
            )
            
            if verification_input:
                await self.random_mouse_move(verification_input)
                await verification_input.click()
                await self.human_delay(200, 500)
                await verification_input.fill(code)
                await self.human_delay(300, 800)
                
                # 点击验证按钮
                verify_button = await self.page.query_selector(self.selectors["verify_button"])
                if verify_button:
                    await self.random_mouse_move(verify_button)
                    await verify_button.click()
                    await self.human_delay(2000, 5000)
                    
                    # 等待验证结果
                    try:
                        await self.page.wait_for_load_state('networkidle', timeout=10000)
                        logger.info("验证码提交成功")
                        return True
                    except:
                        logger.warning("验证码提交后页面未跳转")
                        return True
                else:
                    logger.error("未找到验证按钮")
                    return False
            else:
                logger.error("未找到验证码输入框")
                return False
                
        except Exception as e:
            logger.error(f"输入验证码失败: {e}")
            return False
            
    async def login(self, email: str, password: str) -> bool:
        """登录到DeepSeek"""
        try:
            logger.info(f"登录到DeepSeek - 邮箱: {email}")
            
            # 导航到登录页面
            await self.page.goto(self.login_url, wait_until='networkidle')
            await self.page.wait_for_load_state('networkidle')
            await self.human_delay(1000, 3000)
            
            # 填写登录表单
            email_input = await self.page.wait_for_selector(self.selectors["login_email"], state='visible')
            if email_input:
                await self.random_mouse_move(email_input)
                await email_input.click()
                await self.human_delay(200, 500)
                await email_input.fill(email)
                await self.human_delay(300, 800)
            else:
                logger.error("未找到登录邮箱输入框")
                return False
                
            password_input = await self.page.wait_for_selector(self.selectors["login_password"], state='visible')
            if password_input:
                await self.random_mouse_move(password_input)
                await password_input.click()
                await self.human_delay(200, 500)
                await password_input.fill(password)
                await self.human_delay(300, 800)
            else:
                logger.error("未找到登录密码输入框")
                return False
                
            # 点击登录按钮
            login_button = await self.page.query_selector(self.selectors["login_button"])
            if login_button:
                await self.random_mouse_move(login_button)
                await login_button.click()
                await self.human_delay(2000, 5000)
                
                # 等待登录成功
                try:
                    await self.page.wait_for_load_state('networkidle', timeout=10000)
                    
                    # 检查是否登录成功
                    current_url = self.page.url
                    if 'dashboard' in current_url or 'console' in current_url:
                        logger.info("登录成功")
                        return True
                    else:
                        # 检查是否有错误消息
                        error_element = await self.page.query_selector(".error-message, .alert-error, [role='alert']")
                        if error_element:
                            error_text = await error_element.text_content()
                            logger.error(f"登录失败: {error_text}")
                        return False
                except:
                    logger.warning("登录后页面未跳转，但可能已成功")
                    return True
            else:
                logger.error("未找到登录按钮")
                return False
                
        except Exception as e:
            logger.error(f"登录失败: {e}")
            return False
            
    async def navigate_to_api_keys(self) -> bool:
        """导航到API Keys页面"""
        try:
            logger.info("导航到API Keys页面")
            
            # 直接访问API Keys页面
            await self.page.goto(self.api_keys_url, wait_until='networkidle')
            await self.page.wait_for_load_state('networkidle')
            await self.human_delay(1000, 3000)
            
            # 检查是否在API Keys页面
            page_title = await self.page.title()
            page_content = await self.page.content()
            
            if 'API Key' in page_content or 'API密钥' in page_content:
                logger.info("API Keys页面加载成功")
                return True
            else:
                logger.warning("可能不在API Keys页面，尝试查找API Keys相关元素")
                # 尝试截图
                await self.page.screenshot(path='debug_api_keys_page.png')
                return False
                
        except Exception as e:
            logger.error(f"导航到API Keys页面失败: {e}")
            return False
            
    async def create_api_key(self, key_name: str = "AutoGenerated") -> Optional[str]:
        """创建API Key"""
        try:
            logger.info(f"创建API Key - 名称: {key_name}")
            
            # 查找创建API Key按钮
            create_button = await self.page.query_selector(self.selectors["create_api_key_button"])
            if not create_button:
                # 尝试通过文本查找
                create_button = await self.page.query_selector("button:has-text('Create')")
                if not create_button:
                    create_button = await self.page.query_selector("button:has-text('创建')")
                    
            if create_button:
                await self.random_mouse_move(create_button)
                await create_button.click()
                await self.human_delay(1000, 3000)
                
                # 等待创建对话框
                await self.human_delay(1000, 2000)
                
                # 填写API Key名称
                name_input = await self.page.query_selector(self.selectors["api_key_name_input"])
                if name_input:
                    await self.random_mouse_move(name_input)
                    await name_input.click()
                    await self.human_delay(200, 500)
                    await name_input.fill(key_name)
                    await self.human_delay(300, 800)
                else:
                    logger.warning("未找到API Key名称输入框，可能不需要填写")
                    
                # 点击确认按钮
                confirm_button = await self.page.query_selector(self.selectors["confirm_create_button"])
                if confirm_button:
                    await self.random_mouse_move(confirm_button)
                    await confirm_button.click()
                    await self.human_delay(2000, 5000)
                else:
                    # 尝试通过文本查找确认按钮
                    confirm_button = await self.page.query_selector("button:has-text('Confirm')")
                    if not confirm_button:
                        confirm_button = await self.page.query_selector("button:has-text('确认')")
                        
                    if confirm_button:
                        await self.random_mouse_move(confirm_button)
                        await confirm_button.click()
                        await self.human_delay(2000, 5000)
                        
                # 等待API Key显示
                await self.human_delay(2000, 4000)
                
                # 查找API Key值
                page_content = await self.page.content()
                
                # 使用正则表达式查找API Key
                import re
                api_key_pattern = r'sk-[a-zA-Z0-9]{32,}'
                matches = re.findall(api_key_pattern, page_content)
                
                if matches:
                    api_key = matches[0]
                    logger.info(f"找到API Key: {api_key[:10]}...")
                    
                    # 尝试复制API Key
                    copy_button = await self.page.query_selector(self.selectors["copy_button"])
                    if copy_button:
                        await self.random_mouse_move(copy_button)
                        await copy_button.click()
                        await self.human_delay(500, 1500)
                        
                        # 从剪贴板读取（如果允许）
                        try:
                            clipboard_content = await self.page.evaluate("navigator.clipboard.readText()")
                            if clipboard_content and 'sk-example-key' in clipboard_content:
                                logger.info("API Key已复制到剪贴板")
                        except:
                            pass  # 剪贴板访问可能被拒绝
                            
                    return api_key
                else:
                    logger.warning("未在页面中找到API Key，尝试其他方法")
                    
                    # 查找API Key显示元素
                    api_key_element = await self.page.query_selector(self.selectors["api_key_value"])
                    if api_key_element:
                        api_key_text = await api_key_element.text_content()
                        if api_key_text and 'sk-example-key' in api_key_text:
                            api_key = api_key_text.strip()
                            logger.info(f"从元素中找到API Key: {api_key[:10]}...")
                            return api_key
                            
                    # 截图以便调试
                    await self.page.screenshot(path='debug_api_key_creation.png')
                    return None
                    
            else:
                logger.error("未找到创建API Key按钮")
                return None
                
        except Exception as e:
            logger.error(f"创建API Key失败: {e}")
            return None
            
    async def register_and_get_api_key(self, email: str, password: str, verification_code: Optional[str] = None) -> Tuple[bool, Optional[str]]:
        """
        完整的注册流程并获取API Key
        
        Args:
            email: 邮箱地址
            password: 密码
            verification_code: 验证码（可选）
            
        Returns:
            Tuple[bool, Optional[str]]: (是否成功, API Key)
        """
        try:
            logger.info(f"开始完整注册流程 - 邮箱: {email}")
            
            # 1. 启动浏览器
            if not await self.start():
                return False, None
                
            # 2. 导航到注册页面
            if not await self.navigate_to_register():
                return False, None
                
            # 3. 填写注册表单
            if not await self.fill_registration_form(email, password):
                return False, None
                
            # 4. 提交注册
            if not await self.submit_registration():
                return False, None
                
            # 5. 如果需要验证码，输入验证码
            if verification_code:
                if not await self.enter_verification_code(verification_code):
                    logger.warning("验证码输入失败，尝试继续")
                    
            # 6. 登录（如果需要）
            await self.human_delay(3000, 6000)  # 等待注册完成
            
            # 检查是否已登录
            current_url = self.page.url
            if 'login' in current_url or 'signin' in current_url:
                # 需要登录
                if not await self.login(email, password):
                    logger.error("登录失败")
                    return False, None
                    
            # 7. 导航到API Keys页面
            if not await self.navigate_to_api_keys():
                # 尝试重新登录
                if not await self.login(email, password):
                    return False, None
                if not await self.navigate_to_api_keys():
                    return False, None
                    
            # 8. 创建API Key
            api_key = await self.create_api_key()
            
            if api_key:
                logger.info(f"🎉 注册成功！获取到API Key: {api_key[:15]}...")
                return True, api_key
            else:
                logger.error("注册成功但未获取到API Key")
                return True, None  # 注册成功但未获取API Key
                
        except Exception as e:
            logger.error(f"完整注册流程失败: {e}")
            return False, None
            
        finally:
            # 9. 清理资源
            await self.stop()
            
    async def quick_test(self):
        """快速测试浏览器功能"""
        try:
            logger.info("开始快速测试")
            
            if not await self.start():
                return False
                
            if not await self.create_page():
                return False
                
            # 访问DeepSeek首页
            await self.page.goto("https://deepseek.com", wait_until='networkidle')
            await self.human_delay(2000, 4000)
            
            title = await self.page.title()
            logger.info(f"页面标题: {title}")
            
            # 截图
            await self.page.screenshot(path='test_deepseek_home.png')
            
            await self.stop()
            logger.info("快速测试完成")
            return True
            
        except Exception as e:
            logger.error(f"快速测试失败: {e}")
            await self.stop()
            return False


# 工厂函数
def create_deepseek_registrar(headless: bool = True) -> DeepSeekRegistrar:
    """创建DeepSeek注册器实例"""
    return DeepSeekRegistrar(headless=headless)


async def demo():
    """演示函数"""
    registrar = create_deepseek_registrar(headless=False)  # 显示浏览器以便调试
    
    try:
        # 快速测试
        success = await registrar.quick_test()
        if success:
            print("✅ 浏览器测试成功")
        else:
            print("❌ 浏览器测试失败")
            
    except Exception as e:
        print(f"演示出错: {e}")
    finally:
        await registrar.stop()


if __name__ == "__main__":
    # 运行演示
    import asyncio
    asyncio.run(demo())