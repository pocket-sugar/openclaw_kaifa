#!/usr/bin/env python3
"""
DeepSeek Auto Renew - 第二阶段完整测试套件
"""

import asyncio
import json
import os
import sys
import time
from datetime import datetime

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("=" * 70)
print("DeepSeek Auto Renew - 第二阶段完整测试套件")
print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("=" * 70)


class TestRunner:
    """测试运行器"""
    
    def __init__(self):
        self.results = []
        self.start_time = time.time()
        
    def log_test(self, name, success, message=""):
        """记录测试结果"""
        elapsed = time.time() - self.start_time
        result = {
            "name": name,
            "success": success,
            "message": message,
            "elapsed": f"{elapsed:.2f}s"
        }
        self.results.append(result)
        
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"[{status}] {name:40} {elapsed:6.2f}s {message}")
        return success
        
    def print_summary(self):
        """打印测试摘要"""
        print("\n" + "=" * 70)
        print("测试结果摘要")
        print("=" * 70)
        
        passed = sum(1 for r in self.results if r["success"])
        total = len(self.results)
        
        for result in self.results:
            status = "✅" if result["success"] else "❌"
            print(f"{status} {result['name']:40} {result['elapsed']:>8}")
            if result["message"] and not result["success"]:
                print(f"    └─ {result['message']}")
                
        print(f"\n总计: {passed}/{total} 通过 ({passed/total*100:.1f}%)")
        
        if passed == total:
            print("\n🎉 所有测试通过！第二阶段开发完成")
            return True
        else:
            print(f"\n⚠️  {total - passed} 个测试失败")
            return False


async def run_comprehensive_tests():
    """运行完整测试"""
    runner = TestRunner()
    
    print("\n1. 环境检查测试")
    print("-" * 40)
    
    # 测试1: Python版本
    python_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    runner.log_test(
        "Python版本检查",
        sys.version_info >= (3, 7),
        f"当前版本: {python_version}"
    )
    
    # 测试2: 必要模块导入
    required_modules = [
        ("asyncio", "异步编程"),
        ("json", "JSON处理"),
        ("os", "操作系统接口"),
        ("sys", "系统接口"),
    ]
    
    for module_name, description in required_modules:
        try:
            __import__(module_name)
            runner.log_test(f"模块导入: {description}", True)
        except ImportError:
            runner.log_test(f"模块导入: {description}", False, f"未安装: {module_name}")
    
    print("\n2. 项目模块测试")
    print("-" * 40)
    
    # 测试项目模块
    project_modules = [
        ("src.email_services", "邮箱服务模块"),
        ("src.browser_automation.deepseek_registrar", "DeepSeek注册器"),
        ("src.browser_automation.captcha_solver", "验证码识别器"),
        ("src.main", "主程序模块"),
    ]
    
    for module_path, description in project_modules:
        try:
            __import__(module_path)
            runner.log_test(f"项目模块: {description}", True)
        except ImportError as e:
            runner.log_test(f"项目模块: {description}", False, str(e))
    
    print("\n3. 配置文件测试")
    print("-" * 40)
    
    # 测试配置文件
    config_files = [
        ("config/settings.json", "主配置文件"),
        ("config/email_services.json", "邮箱服务配置"),
    ]
    
    for file_path, description in config_files:
        if os.path.exists(file_path):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                size = os.path.getsize(file_path)
                runner.log_test(f"配置文件: {description}", True, f"{size} 字节")
            except Exception as e:
                runner.log_test(f"配置文件: {description}", False, str(e))
        else:
            runner.log_test(f"配置文件: {description}", False, f"文件不存在: {file_path}")
    
    print("\n4. 类实例化测试")
    print("-" * 40)
    
    # 测试类实例化
    try:
        from src.email_services import create_email_service_manager
        email_manager = create_email_service_manager()
        runner.log_test("邮箱服务管理器实例化", True)
    except Exception as e:
        runner.log_test("邮箱服务管理器实例化", False, str(e))
    
    try:
        from src.browser_automation.deepseek_registrar import create_deepseek_registrar
        registrar = create_deepseek_registrar(headless=True)
        runner.log_test("DeepSeek注册器实例化", True)
    except Exception as e:
        runner.log_test("DeepSeek注册器实例化", False, str(e))
    
    try:
        from src.browser_automation.captcha_solver import create_default_captcha_manager
        captcha_manager = create_default_captcha_manager()
        runner.log_test("验证码管理器实例化", True)
    except Exception as e:
        runner.log_test("验证码管理器实例化", False, str(e))
    
    try:
        from src.main import DeepSeekAutoRenew
        system = DeepSeekAutoRenew(config_path="config/settings.json")
        runner.log_test("主系统实例化", True)
        
        # 检查配置
        config = system.config
        required_configs = ["threshold_percent", "check_interval_minutes", "headless"]
        for key in required_configs:
            if key in config:
                runner.log_test(f"配置检查: {key}", True, f"值: {config[key]}")
            else:
                runner.log_test(f"配置检查: {key}", False, f"缺失配置项")
                
    except Exception as e:
        runner.log_test("主系统实例化", False, str(e))
    
    print("\n5. 第三方依赖测试")
    print("-" * 40)
    
    # 测试第三方依赖
    third_party_deps = [
        ("playwright", "Playwright浏览器自动化"),
        ("PIL", "Pillow图像处理"),
        ("numpy", "NumPy数值计算"),
    ]
    
    for module_name, description in third_party_deps:
        import_name = "PIL" if module_name == "PIL" else module_name
        try:
            __import__(import_name)
            
            # 特殊处理Playwright版本检查
            if module_name == "playwright":
                try:
                    from playwright._repo_version import version as playwright_version
                    runner.log_test(f"第三方依赖: {description}", True, f"版本: {playwright_version}")
                except:
                    runner.log_test(f"第三方依赖: {description}", True, "版本信息不可用")
            else:
                runner.log_test(f"第三方依赖: {description}", True)
                
        except ImportError as e:
            runner.log_test(f"第三方依赖: {description}", False, str(e))
    
    print("\n6. 功能方法测试")
    print("-" * 40)
    
    # 测试功能方法
    try:
        from src.main import DeepSeekAutoRenew
        system = DeepSeekAutoRenew()
        
        # 测试密码生成
        password = system.generate_password()
        runner.log_test("密码生成功能", bool(password), f"示例: {password[:10]}...")
        
        # 测试配置保存路径
        api_key_file = system.config.get("api_key_storage", "")
        runner.log_test("API Key存储路径", bool(api_key_file), f"路径: {api_key_file}")
        
    except Exception as e:
        runner.log_test("功能方法测试", False, str(e))
    
    print("\n7. 目录结构测试")
    print("-" * 40)
    
    # 检查必要的目录
    required_dirs = [
        ("src", "源代码目录"),
        ("src/browser_automation", "浏览器自动化目录"),
        ("src/email_services", "邮箱服务目录"),
        ("config", "配置目录"),
        ("logs", "日志目录"),
    ]
    
    for dir_path, description in required_dirs:
        if os.path.exists(dir_path):
            runner.log_test(f"目录检查: {description}", True)
        else:
            runner.log_test(f"目录检查: {description}", False, f"目录不存在: {dir_path}")
    
    print("\n8. 测试文件检查")
    print("-" * 40)
    
    # 检查测试文件
    test_files = [
        ("test_simple_integration.py", "简化集成测试"),
        ("test_browser_simple.py", "简单浏览器测试"),
        ("test_browser_automation.py", "完整浏览器测试"),
        ("test_email_services.py", "邮箱服务测试"),
    ]
    
    for file_path, description in test_files:
        if os.path.exists(file_path):
            size = os.path.getsize(file_path)
            runner.log_test(f"测试文件: {description}", True, f"{size} 字节")
        else:
            runner.log_test(f"测试文件: {description}", False, f"文件不存在: {file_path}")
    
    print("\n9. Git状态检查")
    print("-" * 40)
    
    # 检查Git状态
    try:
        import subprocess
        result = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=os.path.dirname(os.path.abspath(__file__)),
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            if result.stdout.strip():
                runner.log_test("Git状态检查", False, "有未提交的更改")
            else:
                runner.log_test("Git状态检查", True, "工作区干净")
        else:
            runner.log_test("Git状态检查", False, f"Git命令失败: {result.stderr}")
            
    except Exception as e:
        runner.log_test("Git状态检查", False, str(e))
    
    print("\n10. 浏览器可用性测试")
    print("-" * 40)
    
    # 测试浏览器可用性
    try:
        from playwright.async_api import async_playwright
        
        # 检查浏览器是否安装
        browser_paths = [
            "/root/.cache/ms-playwright/chromium-1208",
            "/root/.cache/ms-playwright/chromium_headless_shell-1208",
        ]
        
        browser_installed = False
        for path in browser_paths:
            if os.path.exists(path):
                browser_installed = True
                runner.log_test("浏览器安装检查", True, f"找到: {os.path.basename(path)}")
                break
                
        if not browser_installed:
            runner.log_test("浏览器安装检查", False, "未找到已安装的浏览器")
            
        # 尝试启动Playwright（不实际启动浏览器）
        try:
            playwright = await async_playwright().start()
            await playwright.stop()
            runner.log_test("Playwright API测试", True)
        except Exception as e:
            runner.log_test("Playwright API测试", False, str(e))
            
    except ImportError as e:
        runner.log_test("浏览器可用性测试", False, f"Playwright未安装: {e}")
    except Exception as e:
        runner.log_test("浏览器可用性测试", False, str(e))
    
    # 打印最终摘要
    return runner.print_summary()


async def main():
    """主函数"""
    try:
        success = await run_comprehensive_tests()
        return 0 if success else 1
        
    except KeyboardInterrupt:
        print("\n\n测试被用户中断")
        return 1
    except Exception as e:
        print(f"\n测试程序出错: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n程序被用户中断")
        sys.exit(1)