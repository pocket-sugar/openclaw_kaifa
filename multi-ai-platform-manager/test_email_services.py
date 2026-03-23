#!/usr/bin/env python3
"""
测试邮箱服务
"""

import asyncio
import sys
from src.email_services import create_email_service_manager


async def test_service_health(manager):
    """测试服务健康状态"""
    print("=" * 50)
    print("测试邮箱服务健康状态")
    print("=" * 50)
    
    await manager.check_all_services_health()
    
    status_list = manager.get_all_status()
    for status in status_list:
        print(f"服务: {status['name']}")
        print(f"  健康: {'✅' if status['healthy'] else '❌'}")
        print(f"  失败次数: {status['failure_count']}")
        print(f"  最后检查: {status['last_checked']}")
        print()


async def test_email_generation(manager):
    """测试邮箱生成"""
    print("=" * 50)
    print("测试邮箱生成")
    print("=" * 50)
    
    for i in range(3):  # 测试3次
        print(f"\n尝试 {i+1}:")
        email = await manager.get_next_email()
        if email:
            print(f"✅ 成功生成邮箱: {email}")
            
            # 检查服务状态
            status_list = manager.get_all_status()
            for status in status_list:
                if status['name'] in email:
                    print(f"   使用服务: {status['name']}")
                    break
        else:
            print("❌ 生成邮箱失败")


async def test_all_services_individually():
    """单独测试每个服务"""
    print("=" * 50)
    print("单独测试每个邮箱服务")
    print("=" * 50)
    
    from src.email_services import (
        create_mails_org_service,
        create_maildrop_service,
        create_fakemail_service,
        create_guerrilla_mail_service
    )
    
    services = [
        ("mails_org", create_mails_org_service()),
        ("maildrop", create_maildrop_service()),
        ("fakemail", create_fakemail_service()),
        ("guerrilla_mail", create_guerrilla_mail_service())
    ]
    
    for name, service in services:
        print(f"\n测试服务: {name}")
        
        # 测试健康状态
        is_healthy = await service.is_available()
        print(f"  健康状态: {'✅' if is_healthy else '❌'}")
        
        if is_healthy:
            # 测试邮箱生成
            email = await service.get_new_email()
            print(f"  邮箱生成: {'✅' if email else '❌'}")
            if email:
                print(f"    邮箱地址: {email}")
        else:
            print(f"  服务不可用，跳过邮箱生成测试")
        
        # 清理
        if hasattr(service, 'session') and service.session:
            await service.session.close()


async def main():
    """主测试函数"""
    print("DeepSeek Auto Renew - 邮箱服务测试")
    print("=" * 50)
    
    # 创建服务管理器
    manager = create_email_service_manager()
    
    try:
        # 测试1: 服务健康状态
        await test_service_health(manager)
        
        # 测试2: 邮箱生成
        await test_email_generation(manager)
        
        # 测试3: 单独测试每个服务
        await test_all_services_individually()
        
        print("\n" + "=" * 50)
        print("测试完成!")
        print("=" * 50)
        
    except Exception as e:
        print(f"\n❌ 测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    finally:
        # 清理资源
        for service in manager.services:
            if hasattr(service, 'session') and service.session:
                await service.session.close()
    
    return 0


if __name__ == "__main__":
    # 运行异步测试
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\n测试被用户中断")
        sys.exit(1)