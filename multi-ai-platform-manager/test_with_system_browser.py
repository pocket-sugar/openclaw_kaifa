#!/usr/bin/env python3
"""
使用系统Chromium进行测试
"""

import asyncio
import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.browser_automation.deepseek_registrar import DeepSeekRegistrar


class SystemBrowserRegistrar(DeepSeekRegistrar):
    """使用系统Chromium的注册器"""
    
    async def start(self):
        """启动系统Chromium浏览器"""
        try:
            from playwright.async_api import async_playwright
            
            self.playwright = await async_playwright().start()
            
            # 使用系统Chromium
            self.browser = await self.playwright.chromium.launch(
                executable_path="/usr/bin/chromium",
                headless=self.headless,
                args=[
                    '--disable-blink-features=AutomationControlled',
                    '--disable-dev-shm-usage',
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                ]
            )
            
            # 创建上下文
            self.context = await self.browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                locale='zh-CN',
            )
            
            print("✅ 系统Chromium启动成功")
            return True
            
        except Exception as e:
            print(f"❌ 启动系统Chromium失败: {e}")
            await self.stop()
            return False


async def test_system_browser():
    """测试系统浏览器"""
    print("测试系统Chromium浏览器...")
    
    registrar = SystemBrowserRegistrar(headless=True)
    
    try:
        # 启动浏览器
        if not await registrar.start():
            return False
            
        # 创建页面
        if not await registrar.create_page():
            return False
            
        # 访问测试页面
        print("访问测试页面...")
        await registrar.page.goto("https://httpbin.org/html", wait_until='networkidle')
        await asyncio.sleep(2)
        
        # 检查页面
        title = await registrar.page.title()
        print(f"✅ 页面标题: {title}")
        
        content = await registrar.page.content()
        if '<html>' in content and '</html>' in content:
            print("✅ 页面内容正常")
            
            # 截图
            await registrar.page.screenshot(path='test_system_browser.png')
            print("✅ 截图保存: test_system_browser.png")
            
            return True
        else:
            print("❌ 页面内容异常")
            return False
            
    except Exception as e:
        print(f"❌ 测试出错: {e}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        await registrar.stop()


async def test_deepseek_with_system_browser():
    """使用系统浏览器测试DeepSeek页面"""
    print("\n测试DeepSeek页面访问...")
    
    registrar = SystemBrowserRegistrar(headless=True)
    
    try:
        if not await registrar.start():
            return False
            
        if not await registrar.create_page():
            return False
            
        # 访问DeepSeek
        print("访问DeepSeek...")
        await registrar.page.goto("https://www.deepseek.com", wait_until='networkidle')
        await asyncio.sleep(3)
        
        # 检查页面
        title = await registrar.page.title()
        print(f"✅ 页面标题: {title}")
        
        # 检查关键内容
        content = await registrar.page.content()
        checks = [
            ("deepseek", "包含DeepSeek"),
            ("ai", "包含AI"),
            ("model", "包含model"),
        ]
        
        all_passed = True
        for keyword, description in checks:
            if keyword in content.lower():
                print(f"✅ {description}")
            else:
                print(f"⚠️  {description}")
                all_passed = False
                
        # 截图
        await registrar.page.screenshot(path='test_deepseek_system_browser.png')
        print("✅ 截图保存: test_deepseek_system_browser.png")
        
        return all_passed
        
    except Exception as e:
        print(f"❌ DeepSeek测试出错: {e}")
        return False
        
    finally:
        await registrar.stop()


async def test_form_interaction():
    """测试表单交互"""
    print("\n测试表单交互...")
    
    registrar = SystemBrowserRegistrar(headless=True)
    
    try:
        if not await registrar.start():
            return False
            
        if not await registrar.create_page():
            return False
            
        # 访问表单测试页面
        print("访问表单测试页面...")
        await registrar.page.goto("https://httpbin.org/forms/post", wait_until='networkidle')
        await asyncio.sleep(2)
        
        # 查找表单元素
        name_input = await registrar.page.query_selector("input[name='custname']")
        if not name_input:
            print("❌ 未找到表单输入框")
            return False
            
        # 测试人类行为
        print("测试人类行为模拟...")
        
        # 随机鼠标移动
        await registrar.random_mouse_move(name_input)
        
        # 点击
        await name_input.click()
        await registrar.human_delay(200, 500)
        
        # 输入文本
        await name_input.fill("Test User")
        await registrar.human_delay(300, 800)
        
        # 检查输入结果
        value = await name_input.input_value()
        if value == "Test User":
            print("✅ 表单输入测试通过")
            
            # 截图
            await registrar.page.screenshot(path='test_form_system_browser.png')
            print("✅ 截图保存: test_form_system_browser.png")
            
            return True
        else:
            print(f"❌ 输入值不匹配: {value}")
            return False
            
    except Exception as e:
        print(f"❌ 表单交互测试出错: {e}")
        return False
        
    finally:
        await registrar.stop()


async def main():
    """主测试函数"""
    print("=" * 60)
    print("使用系统Chromium进行完整测试")
    print("=" * 60)
    
    tests = [
        ("系统浏览器启动测试", test_system_browser),
        ("DeepSeek页面测试", test_deepseek_with_system_browser),
        ("表单交互测试", test_form_interaction),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n{'='*40}")
        print(f"运行测试: {test_name}")
        print('='*40)
        
        try:
            success = await test_func()
            results.append((test_name, success))
            status = "✅ 通过" if success else "❌ 失败"
            print(f"\n{test_name}: {status}")
        except Exception as e:
            print(f"\n{test_name}: ❌ 出错 - {e}")
            import traceback
            traceback.print_exc()
            results.append((test_name, False))
            
    # 汇总结果
    print("\n" + "=" * 60)
    print("测试结果汇总")
    print("=" * 60)
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for test_name, success in results:
        status = "✅ 通过" if success else "❌ 失败"
        print(f"{test_name:25} {status}")
        
    print(f"\n总计: {passed}/{total} 通过 ({passed/total*100:.1f}%)")
    
    if passed == total:
        print("\n🎉 所有系统浏览器测试通过！")
        print("第二阶段功能完整，可以使用系统Chromium运行")
        return 0
    else:
        print(f"\n⚠️  {total - passed} 个测试失败")
        return 1


if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n测试被用户中断")
        sys.exit(1)
    except Exception as e:
        print(f"测试程序出错: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)