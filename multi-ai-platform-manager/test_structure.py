#!/usr/bin/env python3
"""
只测试项目结构，不测试具体实现
"""

import os
import sys

def test_directory_structure():
    """测试目录结构"""
    print("测试目录结构:")
    print("-" * 30)
    
    dirs_to_check = [
        ("src", True),
        ("src/email_services", True),
        ("src/browser_automation", False),  # 第二阶段创建
        ("src/utils", False),  # 第二阶段创建
        ("config", True),
        ("logs", True),
    ]
    
    all_passed = True
    for dir_path, required in dirs_to_check:
        exists = os.path.exists(dir_path)
        status = "✅" if exists else "❌"
        requirement = "(必需)" if required else "(可选)"
        
        if required and not exists:
            all_passed = False
            
        print(f"  {status} {dir_path} {requirement}")
    
    return all_passed

def test_file_structure():
    """测试文件结构"""
    print("\n测试文件结构:")
    print("-" * 30)
    
    files_to_check = [
        ("README.md", True),
        ("requirements.txt", True),
        ("config/settings.json", True),
        ("src/__init__.py", False),
        ("src/email_services/__init__.py", True),
        ("src/email_services/base.py", True),
        ("src/email_services/mails_org.py", True),
        ("src/email_services/maildrop.py", True),
        ("src/email_services/fakemail.py", True),
        ("src/email_services/guerrilla_mail.py", True),
    ]
    
    all_passed = True
    for file_path, required in files_to_check:
        exists = os.path.exists(file_path)
        status = "✅" if exists else "❌"
        requirement = "(必需)" if required else "(可选)"
        
        if required and not exists:
            all_passed = False
            
        if exists:
            size = os.path.getsize(file_path)
            print(f"  {status} {file_path} ({size} bytes) {requirement}")
        else:
            print(f"  {status} {file_path} {requirement}")
    
    return all_passed

def test_git_status():
    """测试Git状态"""
    print("\n测试Git状态:")
    print("-" * 30)
    
    if os.path.exists(".git"):
        print("  ✅ Git仓库已初始化")
        
        # 检查提交历史
        import subprocess
        try:
            result = subprocess.run(
                ["git", "log", "--oneline", "-5"],
                capture_output=True,
                text=True,
                cwd=os.path.dirname(__file__)
            )
            
            if result.returncode == 0:
                commits = result.stdout.strip().split('\n')
                print(f"  ✅ 最近提交 ({len(commits)} 个):")
                for commit in commits[:3]:  # 只显示前3个
                    print(f"     {commit}")
            else:
                print("  ⚠️  无法获取Git提交历史")
                
        except Exception as e:
            print(f"  ⚠️  检查Git状态时出错: {e}")
    else:
        print("  ❌ Git仓库未初始化")
        return False
    
    return True

def main():
    """主测试函数"""
    print("DeepSeek Auto Renew - 项目结构测试")
    print("=" * 50)
    
    # 测试目录结构
    dirs_ok = test_directory_structure()
    
    # 测试文件结构
    files_ok = test_file_structure()
    
    # 测试Git状态
    git_ok = test_git_status()
    
    print("\n" + "=" * 50)
    print("测试结果汇总:")
    print(f"  目录结构: {'✅ 通过' if dirs_ok else '❌ 失败'}")
    print(f"  文件结构: {'✅ 通过' if files_ok else '❌ 失败'}")
    print(f"  Git状态: {'✅ 通过' if git_ok else '❌ 失败'}")
    
    overall = dirs_ok and files_ok and git_ok
    print(f"\n总体结果: {'✅ 所有测试通过!' if overall else '❌ 部分测试失败'}")
    print("=" * 50)
    
    return 0 if overall else 1

if __name__ == "__main__":
    sys.exit(main())