#!/usr/bin/env python3
"""
简单浏览器测试 - 不依赖图像处理
"""

import asyncio
import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.browser_automation.deepseek_registrar import create_deepseek_registrar


async def test_browser_launch():
    """测试浏览器启动"""
    print("测试浏览器启动...")
    
    registrar = create_deepseek_registrar(headless=True)
    
    try:
        # 尝试启动浏览器
        success = await registrar.start()
        if success:
            print("✅ 浏览器启动成功")
            
            # 创建页面
            if await registrar.create_page():
                print("✅ 页面创建成功")
                
                # 访问一个简单页面
                await registrar.page.goto("https://httpbin.org/html", wait_until='networkidle')
                await asyncio.sleep(1)
                
                # 检查页面内容
                content = await registrar.page.content()
                if '<html>' in content:
                    print("✅ 页面访问成功")
                    
                    # 获取标题
                    title = await registrar.page.title()
                    print(f"✅ 页面标题: {title}")
                    
                    # 截图
                    await registrar.page.screenshot(path='test_browser_simple.png')
                    print("✅ 截图保存: test_browser_simple.png")
                    
                    return True
                else:
                    print("❌ 页面内容异常")
                    return False
            else:
                print("❌ 页面创建失败")
                return False
        else:
            print("❌ 浏览器启动失败")
            return False
            
    except Exception as e:
        print(f"❌ 浏览器测试出错: {e}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        await registrar.stop()


async def test_human_behavior():
    """测试人类行为模拟"""
    print("\n测试人类行为模拟...")
    
    registrar = create_deepseek_registrar(headless=True)
    
    try:
        if not await registrar.start():
            return False
            
        if not await registrar.create_page():
            return False
            
        # 访问测试页面
        await registrar.page.goto("https://httpbin.org/forms/post", wait_until='networkidle')
        await asyncio.sleep(1)
        
        # 测试人类延迟
        print("测试人类延迟...")
        start_time = asyncio.get_event_loop().time()
        await registrar.human_delay(500, 1000)
        elapsed = (asyncio.get_event_loop().time() - start_time) * 1000
        print(f"✅ 人类延迟测试: {elapsed:.0f}ms")
        
        # 查找输入框
        input_element = await registrar.page.query_selector("input[name='custname']")
        if input_element:
            # 测试随机鼠标移动
            print("测试随机鼠标移动...")
            await registrar.random_mouse_move(input_element)
            print("✅ 随机鼠标移动测试")
            
            # 测试点击和输入
            await input_element.click()
            await registrar.human_delay(200, 500)
            await input_element.fill("Test User")
            print("✅ 表单交互测试")
            
            return True
        else:
            print("❌ 未找到输入框")
            return False
            
    except Exception as e:
        print(f"❌ 人类行为测试出错: {e}")
        return False
        
    finally:
        await registrar.stop()


async def test_deepseek_page_structure():
    """测试DeepSeek页面结构分析"""
    print("\n测试DeepSeek页面结构分析...")
    
    registrar = create_deepseek_registrar(headless=True)
    
    try:
        if not await registrar.start():
            return False
            
        if not await registrar.create_page():
            return False
            
        # 访问DeepSeek首页
        print("访问DeepSeek首页...")
        await registrar.page.goto("https://www.deepseek.com", wait_until='networkidle')
        await asyncio.sleep(2)
        
        # 检查页面
        title = await registrar.page.title()
        print(f"✅ 页面标题: {title}")
        
        content = await registrar.page.content()
        
        # 检查关键元素
        checks = [
            ("DeepSeek", "页面包含DeepSeek"),
            ("AI", "页面包含AI相关"),
            ("model", "页面包含model"),
        ]
        
        all_checks_passed = True
        for keyword, description in checks:
            if keyword.lower() in content.lower():
                print(f"✅ {description}")
            else:
                print(f"⚠️  {description} 未找到")
                all_checks_passed = False
                
        # 截图
        await registrar.page.screenshot(path='test_deepseek_home.png')
        print("✅ 截图保存: test_deepseek_home.png")
        
        return all_checks_passed
        
    except Exception as e:
        print(f"❌ DeepSeek页面测试出错: {e}")
        return False
        
    finally:
        await registrar.stop()


async def main():
    """主测试函数"""
    print("=" * 60)
    print("DeepSeek Auto Renew - 简单浏览器测试")
    print("=" * 60)
    
    tests = [
        ("浏览器启动测试", test_browser_launch),
        ("人类行为模拟测试", test_human_behavior),
        ("DeepSeek页面测试", test_deepseek_page_structure),
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
        print("\n🎉 所有浏览器测试通过！第二阶段功能完整")
        print("系统已准备好进行实际注册测试")
        return 0
    else:
        print(f"\n⚠️  {total - passed} 个测试失败")
        print("可能需要安装浏览器或检查网络连接")
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