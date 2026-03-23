"""
Guerrilla Mail 邮箱服务实现
https://www.guerrillamail.com/
"""

import re
import random
import string
import json
from typing import Optional, List, Dict, Any
from .base import EmailService


class GuerrillaMailService(EmailService):
    """Guerrilla Mail 临时邮箱服务（有API接口）"""
    
    def __init__(self):
        super().__init__("guerrilla_mail", "https://www.guerrillamail.com")
        self.api_base = "https://www.guerrillamail.com/ajax.php"
        self.email_domain = "guerrillamailblock.com"
        self.sid_token = None
        self.current_email = None
        
    async def get_new_email(self) -> Optional[str]:
        """
        获取新的Guerrilla Mail邮箱地址
        
        Guerrilla Mail提供JSON API
        """
        try:
            # API请求获取新邮箱
            params = {
                "f": "get_email_address"
            }
            
            if not self.session:
                return None
                
            async with self.session.get(
                self.api_base, 
                params=params, 
                timeout=30
            ) as response:
                
                if response.status != 200:
                    return None
                    
                data = await response.json()
                
                email_addr = data.get("email_addr")
                self.sid_token = data.get("sid_token")
                self.current_email = email_addr
                
                if email_addr:
                    print(f"[Guerrilla Mail] 获取邮箱: {email_addr}")
                    self.record_success()
                    return email_addr
                else:
                    self.record_failure()
                    return None
                    
        except Exception as e:
            print(f"[Guerrilla Mail] 获取邮箱失败: {e}")
            self.record_failure()
            return None
    
    async def check_inbox(self, email: str) -> List[Dict[str, Any]]:
        """
        检查Guerrilla Mail收件箱
        
        使用API获取邮件列表
        """
        try:
            if not self.sid_token:
                # 如果没有session token，先获取一个
                await self.get_new_email()
                if not self.sid_token:
                    return []
            
            # API请求获取邮件列表
            params = {
                "f": "get_email_list",
                "sid_token": self.sid_token,
                "offset": 0
            }
            
            if not self.session:
                return []
                
            async with self.session.get(
                self.api_base, 
                params=params, 
                timeout=30
            ) as response:
                
                if response.status != 200:
                    return []
                    
                data = await response.json()
                emails_data = data.get("list", [])
                emails = []
                
                for email_data in emails_data:
                    emails.append({
                        "id": email_data.get("mail_id"),
                        "subject": email_data.get("mail_subject", "无主题"),
                        "from": email_data.get("mail_from", "未知发件人"),
                        "excerpt": email_data.get("mail_excerpt", ""),
                        "date": email_data.get("mail_date", ""),
                        "read": email_data.get("read", 0) == 1,
                        "service": self.name
                    })
                    
                return emails
                
        except Exception as e:
            print(f"[Guerrilla Mail] 检查收件箱失败: {e}")
            return []
    
    async def get_email_body(self, email_id: str) -> Optional[str]:
        """
        获取邮件完整内容
        """
        try:
            if not self.sid_token:
                return None
                
            params = {
                "f": "fetch_email",
                "sid_token": self.sid_token,
                "email_id": email_id
            }
            
            if not self.session:
                return None
                
            async with self.session.get(
                self.api_base, 
                params=params, 
                timeout=30
            ) as response:
                
                if response.status != 200:
                    return None
                    
                data = await response.json()
                return data.get("mail_body", "")
                
        except Exception as e:
            print(f"[Guerrilla Mail] 获取邮件正文失败: {e}")
            return None
    
    async def get_verification_link(self, email: str, keyword: str = "verify") -> Optional[str]:
        """
        从Guerrilla Mail收件箱获取验证链接
        """
        try:
            emails = await self.check_inbox(email)
            
            for email_data in emails:
                subject = email_data.get("subject", "").lower()
                excerpt = email_data.get("excerpt", "").lower()
                
                # 查找包含关键词的邮件
                if keyword.lower() in subject or keyword.lower() in excerpt:
                    # 获取完整邮件内容
                    email_id = email_data.get("id")
                    if email_id:
                        body = await self.get_email_body(email_id)
                        if body:
                            # 从邮件正文中提取链接
                            links = self._extract_links(body)
                            for link in links:
                                if "verify" in link.lower() or "confirm" in link.lower():
                                    return link
                    
                    # 也可以从摘要中提取
                    links = self._extract_links(excerpt)
                    for link in links:
                        if "verify" in link.lower() or "confirm" in link.lower():
                            return link
                            
            return None
            
        except Exception as e:
            print(f"[Guerrilla Mail] 获取验证链接失败: {e}")
            return None
    
    async def extend_email_lifetime(self) -> bool:
        """
        延长邮箱生命周期
        
        Guerrilla Mail邮箱默认1小时，可以延长
        """
        try:
            if not self.sid_token:
                return False
                
            params = {
                "f": "extend",
                "sid_token": self.sid_token
            }
            
            if not self.session:
                return False
                
            async with self.session.get(
                self.api_base, 
                params=params, 
                timeout=30
            ) as response:
                
                if response.status != 200:
                    return False
                    
                data = await response.json()
                return data.get("success", 0) == 1
                
        except Exception as e:
            print(f"[Guerrilla Mail] 延长邮箱生命周期失败: {e}")
            return False
    
    def _extract_links(self, text: str) -> List[str]:
        """从文本中提取链接"""
        url_pattern = r'https?://[^\s<>"]+|www\.[^\s<>"]+'
        return re.findall(url_pattern, text)
    
    async def is_available(self) -> bool:
        """
        重写健康检查，使用API检查
        """
        try:
            # 尝试获取一个测试邮箱
            test_email = await self.get_new_email()
            if test_email:
                self.is_healthy = True
                self.failure_count = 0
                return True
            else:
                self.is_healthy = False
                self.failure_count += 1
                return False
                
        except Exception as e:
            print(f"[Guerrilla Mail] 健康检查失败: {e}")
            self.is_healthy = False
            self.failure_count += 1
            return False


# 工厂函数
def create_guerrilla_mail_service() -> GuerrillaMailService:
    """创建Guerrilla Mail服务实例"""
    return GuerrillaMailService()