#!/usr/bin/env python3
"""
简化集成测试 - 不依赖图像处理
"""

import asyncio
import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("=" * 60)
print("DeepSeek Auto Renew - 第二阶段简化测试")
print("=" * 60)

async def test_module_imports():
    """测试模块导入"""
    print("\n1. 测试模块导入...")
    
    modules_to_test = [
        ("src.email_services", "邮箱服务模块"),
        ("src.browser_automation.deepseek_registrar", "DeepSeek注册器"),
        ("src.browser_automation.captcha_solver", "验证码识别器"),
        ("src.main", "主程序模块"),
    ]
    
    all_passed = True
    for module_path, description in modules_to_test:
        try:
            __import__(module_path)
            print(f"  ✅ {description} 导入成功")
        except ImportError as e:
            print(f"  ❌ {description} 导入失败: {e}")
            all_passed = False
            
    return all_passed

async def test_class_creation():
    """测试类创建"""
    print("\n2. 测试类创建...")
    
    tests = []
    
    try:
        from src.email_services import create_email_service_manager
        manager = create_email_service_manager()
        tests.append(("邮箱服务管理器", True))
    except Exception as e:
        tests.append(("邮箱服务管理器", False, str(e)))
        
    try:
        from src.browser_automation.deepseek_registrar import create_deepseek_registrar
        registrar = create_deepseek_registrar(headless=True)
        tests.append(("DeepSeek注册器", True))
    except Exception as e:
        tests.append(("DeepSeek注册器", False, str(e)))
        
    try:
        from src.browser_automation.captcha_solver import create_default_captcha_manager
        captcha_manager = create_default_captcha_manager()
        tests.append(("验证码管理器", True))
    except Exception as e:
        tests.append(("验证码管理器", False, str(e)))
        
    # 输出结果
    all_passed = True
    for test_name, success, *error in tests:
        if success:
            print(f"  ✅ {test_name} 创建成功")
        else:
            print(f"  ❌ {test_name} 创建失败: {error[0] if error else '未知错误'}")
            all_passed = False
            
    return all_passed

async def test_config_loading():
    """测试配置加载"""
    print("\n3. 测试配置加载...")
    
    try:
        import json
        
        config_files = [
            ("config/settings.json", "主配置"),
            ("config/email_services.json", "邮箱服务配置"),
        ]
        
        all_passed = True
        for file_path, description in config_files:
            if os.path.exists(file_path):
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        config = json.load(f)
                    print(f"  ✅ {description} 加载成功 ({len(json.dumps(config))} 字节)")
                except Exception as e:
                    print(f"  ❌ {description} 加载失败: {e}")
                    all_passed = False
            else:
                print(f"  ❌ {description} 文件不存在: {file_path}")
                all_passed = False
                
        return all_passed
        
    except Exception as e:
        print(f"  ❌ 配置加载测试失败: {e}")
        return False

async def test_main_program_structure():
    """测试主程序结构"""
    print("\n4. 测试主程序结构...")
    
    try:
        from src.main import DeepSeekAutoRenew
        
        # 创建实例
        system = DeepSeekAutoRenew(config_path="config/settings.json")
        
        # 检查配置
        config = system.config
        required_keys = ["threshold_percent", "check_interval_minutes", "headless"]
        
        all_present = True
        for key in required_keys:
            if key in config:
                print(f"  ✅ 配置项 '{key}' 存在: {config[key]}")
            else:
                print(f"  ❌ 配置项 '{key}' 缺失")
                all_present = False
                
        if all_present:
            print("  ✅ 主程序结构测试通过")
            return True
        else:
            print("  ❌ 主程序结构测试失败")
            return False
            
    except Exception as e:
        print(f"  ❌ 主程序结构测试失败: {e}")
        return False

async def test_playwright_availability():
    """测试Playwright可用性"""
    print("\n5. 测试Playwright可用性...")
    
    try:
        import playwright
        
        # 检查版本
        try:
            from playwright._repo_version import version as playwright_version
            print(f"  ✅ Playwright版本: {playwright_version}")
        except:
            print("  ✅ Playwright已安装（版本信息不可用）")
            
        # 检查浏览器类型
        from playwright.async_api import async_playwright
        
        print("  ✅ Playwright API可用")
        return True
        
    except ImportError as e:
        print(f"  ❌ Playwright未安装: {e}")
        return False
    except Exception as e:
        print(f"  ❌ Playwright测试失败: {e}")
        return False

async def main():
    """主测试函数"""
    print("开始第二阶段简化测试...")
    print("=" * 60)
    
    test_results = []
    
    # 运行各个测试
    tests = [
        ("模块导入", test_module_imports),
        ("类创建", test_class_creation),
        ("配置加载", test_config_loading),
        ("主程序结构", test_main_program_structure),
        ("Playwright可用性", test_playwright_availability),
    ]
    
    for test_name, test_func in tests:
        try:
            success = await test_func()
            test_results.append((test_name, success))
            status = "✅ 通过" if success else "❌ 失败"
            print(f"\n{test_name}: {status}")
        except Exception as e:
            print(f"\n{test_name}: ❌ 出错 - {e}")
            test_results.append((test_name, False))
            
    # 汇总结果
    print("\n" + "=" * 60)
    print("测试结果汇总")
    print("=" * 60)
    
    passed = sum(1 for _, success in test_results if success)
    total = len(test_results)
    
    for test_name, success in test_results:
        status = "✅ 通过" if success else "❌ 失败"
        print(f"{test_name:20} {status}")
        
    print(f"\n总计: {passed}/{total} 通过 ({passed/total*100:.1f}%)")
    
    if passed == total:
        print("\n🎉 所有简化测试通过！第二阶段代码结构完整")
        print("可以开始运行完整的功能测试")
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