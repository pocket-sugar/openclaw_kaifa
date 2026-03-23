#!/usr/bin/env python3
"""
基本测试 - 验证项目结构
"""

import os
import sys

print("DeepSeek Auto Renew - 项目结构验证")
print("=" * 50)

# 检查目录结构
required_dirs = [
    "src",
    "src/email_services", 
    "src/browser_automation",
    "src/utils",
    "config",
    "logs"
]

print("检查目录结构:")
for dir_path in required_dirs:
    if os.path.exists(dir_path):
        print(f"  ✅ {dir_path}")
    else:
        print(f"  ❌ {dir_path}")

# 检查关键文件
required_files = [
    "README.md",
    "requirements.txt",
    "config/settings.json",
    "src/email_services/__init__.py",
    "src/email_services/base.py"
]

print("\n检查关键文件:")
for file_path in required_files:
    if os.path.exists(file_path):
        size = os.path.getsize(file_path)
        print(f"  ✅ {file_path} ({size} bytes)")
    else:
        print(f"  ❌ {file_path}")

# 检查Python模块导入
print("\n测试Python模块导入:")
try:
    # 添加src到Python路径
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))
    
    # 测试导入基础模块
    from email_services.base import EmailService, EmailServiceManager
    print("  ✅ 成功导入EmailService和EmailServiceManager")
    
    # 测试创建管理器
    manager = EmailServiceManager()
    print(f"  ✅ 成功创建EmailServiceManager，包含 {len(manager.services)} 个服务")
    
except ImportError as e:
    print(f"  ❌ 导入失败: {e}")
except Exception as e:
    print(f"  ❌ 其他错误: {e}")

print("\n" + "=" * 50)
print("项目结构验证完成!")
print("=" * 50)