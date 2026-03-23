"""
邮箱服务模块
提供多临时邮箱服务的轮换和故障转移
"""

from .base import EmailService, EmailServiceManager
from .mails_org import create_mails_org_service
from .maildrop import create_maildrop_service
from .fakemail import create_fakemail_service
from .guerrilla_mail import create_guerrilla_mail_service

__all__ = [
    "EmailService",
    "EmailServiceManager",
    "create_mails_org_service",
    "create_maildrop_service",
    "create_fakemail_service",
    "create_guerrilla_mail_service"
]


def create_email_service_manager() -> EmailServiceManager:
    """
    创建并配置邮箱服务管理器
    
    Returns:
        EmailServiceManager: 配置好的服务管理器
    """
    manager = EmailServiceManager()
    
    # 添加所有可用的邮箱服务
    manager.add_service(create_mails_org_service())
    manager.add_service(create_maildrop_service())
    manager.add_service(create_fakemail_service())
    manager.add_service(create_guerrilla_mail_service())
    
    return manager