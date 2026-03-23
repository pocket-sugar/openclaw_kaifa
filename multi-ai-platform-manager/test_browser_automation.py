#!/usr/bin/env python3
"""
测试浏览器自动化功能
"""

import asyncio
import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.browser_automation.deepseek_registrar import create_deepseek_registrar
from src.browser_automation.captcha_solver import create_default_captcha_manager


async def test_browser_quick():
    """快速浏览器测试"""
    print("=" * 50)
    print("测试浏览器快速功能")
    print("=" * 50)
    
    registrar = create_deepseek_registrar(headless=False)  # 显示浏览器以便观察
    
    try:
        success = await registrar.quick_test()
        if success:
            print("✅ 浏览器快速测试通过")
            return True
        else:
            print("❌ 浏览器快速测试失败")
            return False
            
    except Exception as e:
        print(f"❌ 浏览器快速测试出错: {e}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        await registrar.stop()


async def test_captcha_solver():
    """测试验证码识别器"""
    print("\n" + "=" * 50)
    print("测试验证码识别器")
    print("=" * 50)
    
    manager = create_default_captcha_manager()
    
    # 创建一个简单的测试图像
    from PIL import Image, ImageDraw
    import io
    
    # 创建数字4的图像
    image = Image.new('RGB', (100, 50), color='white')
    draw = ImageDraw.Draw(image)
    
    # 尝试使用字体
    try:
        from PIL import ImageFont
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 40)
        draw.text((30, 5), "4", fill='black', font=font)
    except:
        # 使用默认字体
        draw.text((30, 5), "4", fill='black')
    
    # 转换为字节数据
    img_byte_arr = io.BytesIO()
    image.save(img_byte_arr, format='PNG')
    image_data = img_byte_arr.getvalue()
    
    # 测试识别
    result = await manager.solve_captcha(image_data, "digit")
    
    print(f"验证码识别结果: {result}")
    print(f"统计信息: {manager.get_all_stats()}")
    
    if result:
        print("✅ 验证码识别测试通过")
        return True
    else:
        print("⚠️ 验证码识别测试结果为空")
        return False


async def test_deepseek_navigation():
    """测试DeepSeek页面导航"""
    print("\n" + "=" * 50)
    print("测试DeepSeek页面导航")
    print("=" * 50)
    
    registrar = create_deepseek_registrar(headless=False)
    
    try:
        # 启动浏览器
        if not await registrar.start():
            print("❌ 浏览器启动失败")
            return False
            
        # 创建页面
        if not await registrar.create_page():
            print("❌ 页面创建失败")
            return False
            
        # 访问DeepSeek平台
        print("访问DeepSeek平台...")
        await registrar.page.goto("https://platform.deepseek.com", wait_until='networkidle')
        await asyncio.sleep(3)
        
        # 获取页面标题
        title = await registrar.page.title()
        print(f"页面标题: {title}")
        
        # 截图
        await registrar.page.screenshot(path='test_deepseek_platform.png')
        print("截图已保存: test_deepseek_platform.png")
        
        # 检查页面内容
        content = await registrar.page.content()
        if 'DeepSeek' in content or 'deepseek' in content.lower():
            print("✅ DeepSeek页面访问成功")
            
            # 尝试查找注册/登录链接
            register_link = await registrar.page.query_selector("a[href*='signup'], a[href*='register']")
            login_link = await registrar.page.query_selector("a[href*='login'], a[href*='signin']")
            
            if register_link:
                register_text = await register_link.text_content()
                print(f"找到注册链接: {register_text.strip()}")
                
            if login_link:
                login_text = await login_link.text_content()
                print(f"找到登录链接: {login_text.strip()}")
                
            return True
        else:
            print("❌ 可能未正确加载DeepSeek页面")
            return False
            
    except Exception as e:
        print(f"❌ DeepSeek导航测试出错: {e}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        await registrar.stop()


async def test_form_interaction():
    """测试表单交互"""
    print("\n" + "=" * 50)
    print("测试表单交互")
    print("=" * 50)
    
    registrar = create_deepseek_registrar(headless=False)
    
    try:
        # 启动浏览器并访问测试页面
        if not await registrar.start():
            return False
            
        if not await registrar.create_page():
            return False
            
        # 访问一个包含表单的测试页面
        print("访问测试表单页面...")
        await registrar.page.goto("https://httpbin.org/forms/post", wait_until='networkidle')
        await asyncio.sleep(2)
        
        # 查找表单元素
        name_input = await registrar.page.query_selector("input[name='custname']")
        if name_input:
            print("找到姓名输入框")
            
            # 模拟人类输入
            await registrar.random_mouse_move(name_input)
            await name_input.click()
            await asyncio.sleep(0.5)
            await name_input.fill("Test User")
            await asyncio.sleep(0.5)
            
            print("✅ 表单输入测试通过")
            
            # 截图
            await registrar.page.screenshot(path='test_form_interaction.png')
            print("截图已保存: test_form_interaction.png")
            
            return True
        else:
            print("❌ 未找到表单元素")
            return False
            
    except Exception as e:
        print(f"❌ 表单交互测试出错: {e}")
        return False
        
    finally:
        await registrar.stop()


async def main():
    """主测试函数"""
    print("DeepSeek Auto Renew - 第二阶段测试")
    print("=" * 50)
    
    tests = [
        ("浏览器快速测试", test_browser_quick),
        ("验证码识别测试", test_captcha_solver),
        ("DeepSeek导航测试", test_deepseek_navigation),
        ("表单交互测试", test_form_interaction),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n运行测试: {test_name}")
        try:
            success = await test_func()
            results.append((test_name, success))
            print(f"{'✅' if success else '❌'} {test_name} {'通过' if success else '失败'}")
        except Exception as e:
            print(f"❌ {test_name} 出错: {e}")
            results.append((test_name, False))
            
    print("\n" + "=" * 50)
    print("测试结果汇总")
    print("=" * 50)
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for test_name, success in results:
        status = "✅ 通过" if success else "❌ 失败"
        print(f"{test_name}: {status}")
        
    print(f"\n总计: {passed}/{total} 通过 ({passed/total*100:.1f}%)")
    
    if passed == total:
        print("\n🎉 所有测试通过！第二阶段开发完成")
        return 0
    else:
        print(f"\n⚠️  {total - passed} 个测试失败，需要修复")
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