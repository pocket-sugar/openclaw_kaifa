#!/usr/bin/env python3
"""
简单测试邮箱服务逻辑（不依赖网络）
"""

import sys
import os

# 添加src目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from email_services.base import EmailService, EmailServiceManager


class MockEmailService(EmailService):
    """模拟邮箱服务，用于测试"""
    
    def __init__(self, name):
        super().__init__(name, f"https://{name}.example.com")
        self.email_counter = 0
        
    async def get_new_email(self):
        self.email_counter += 1
        return f"test{self.email_counter}@{self.name}.com"
    
    async def check_inbox(self, email):
        return []
    
    async def get_verification_link(self, email, keyword="verify"):
        return None


async def test_manager_logic():
    """测试管理器逻辑"""
    print("测试邮箱服务管理器逻辑")
    print("=" * 50)
    
    manager = EmailServiceManager()
    
    # 添加模拟服务
    for i in range(3):
        service = MockEmailService(f"service_{i+1}")
        manager.add_service(service)
    
    print(f"已添加 {len(manager.services)} 个服务")
    
    # 测试轮换获取邮箱
    print("\n测试邮箱轮换获取:")
    for i in range(5):
        email = await manager.get_next_email()
        print(f"  尝试 {i+1}: {email if email else '失败'}")
    
    # 测试服务状态
    print("\n服务状态:")
    for status in manager.get_all_status():
        print(f"  {status['name']}: 健康={status['healthy']}, 失败次数={status['failure_count']}")
    
    print("\n✅ 逻辑测试完成!")


if __name__ == "__main__":
    import asyncio
    
    try:
        asyncio.run(test_manager_logic())
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)