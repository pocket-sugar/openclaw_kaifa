"""
MailDrop 邮箱服务实现
https://maildrop.cc/
"""

import re
import random
import string
from typing import Optional, List, Dict, Any
from .base import EmailService


class MailDropService(EmailService):
    """MailDrop 临时邮箱服务"""
    
    def __init__(self):
        super().__init__("maildrop", "https://maildrop.cc")
        self.email_domain = "maildrop.cc"
        self.api_base = "https://api.maildrop.cc/graphql"
        
    async def get_new_email(self) -> Optional[str]:
        """
        获取新的MailDrop邮箱地址
        
        MailDrop允许用户自定义邮箱用户名
        """
        try:
            # 生成随机用户名
            username = self._generate_username()
            email = f"{username}@{self.email_domain}"
            
            print(f"[MailDrop] 生成邮箱: {email}")
            return email
            
        except Exception as e:
            print(f"[MailDrop] 获取邮箱失败: {e}")
            self.record_failure()
            return None
    
    async def check_inbox(self, email: str) -> List[Dict[str, Any]]:
        """
        检查MailDrop收件箱
        
        MailDrop提供GraphQL API
        """
        try:
            # 提取用户名
            username = email.split("@")[0]
            
            # GraphQL查询
            query = """
            query GetInbox($mailbox: String!) {
                inbox(mailbox: $mailbox) {
                    id
                    mailfrom
                    subject
                    html
                    text
                    date
                }
            }
            """
            
            payload = {
                "query": query,
                "variables": {"mailbox": username}
            }
            
            if not self.session:
                return []
                
            headers = {
                "Content-Type": "application/json",
                "Accept": "application/json"
            }
            
            async with self.session.post(
                self.api_base, 
                json=payload, 
                headers=headers, 
                timeout=30
            ) as response:
                
                if response.status != 200:
                    # 如果API失败，尝试使用网页版
                    return await self._check_inbox_web(email)
                    
                data = await response.json()
                
                if "errors" in data:
                    print(f"[MailDrop] GraphQL错误: {data['errors']}")
                    return await self._check_inbox_web(email)
                    
                emails_data = data.get("data", {}).get("inbox", [])
                emails = []
                
                for email_data in emails_data:
                    emails.append({
                        "id": email_data.get("id", ""),
                        "subject": email_data.get("subject", "无主题"),
                        "from": email_data.get("mailfrom", "未知发件人"),
                        "body": email_data.get("text", "") or email_data.get("html", ""),
                        "date": email_data.get("date", ""),
                        "service": self.name
                    })
                    
                return emails
                
        except Exception as e:
            print(f"[MailDrop] 检查收件箱失败: {e}")
            return await self._check_inbox_web(email)
    
    async def _check_inbox_web(self, email: str) -> List[Dict[str, Any]]:
        """
        使用网页版检查收件箱（备用方案）
        """
        try:
            username = email.split("@")[0]
            inbox_url = f"{self.base_url}/inbox/{username}"
            
            if not self.session:
                return []
                
            async with self.session.get(inbox_url, timeout=30) as response:
                if response.status != 200:
                    return []
                    
                html = await response.text()
                return self._parse_inbox_html(html)
                
        except Exception as e:
            print(f"[MailDrop] 网页版收件箱检查失败: {e}")
            return []
    
    async def get_verification_link(self, email: str, keyword: str = "verify") -> Optional[str]:
        """
        从MailDrop收件箱获取验证链接
        """
        try:
            emails = await self.check_inbox(email)
            
            for email_data in emails:
                subject = email_data.get("subject", "").lower()
                body = email_data.get("body", "").lower()
                
                # 查找包含关键词的邮件
                if keyword.lower() in subject or keyword.lower() in body:
                    # 从邮件正文中提取链接
                    links = self._extract_links(email_data.get("body", ""))
                    for link in links:
                        if "verify" in link.lower() or "confirm" in link.lower():
                            return link
                            
            return None
            
        except Exception as e:
            print(f"[MailDrop] 获取验证链接失败: {e}")
            return None
    
    def _generate_username(self, length: int = 12) -> str:
        """生成随机用户名"""
        chars = string.ascii_lowercase + string.digits
        return ''.join(random.choice(chars) for _ in range(length))
    
    def _parse_inbox_html(self, html: str) -> List[Dict[str, Any]]:
        """
        解析网页版收件箱HTML
        """
        emails = []
        
        # 查找邮件列表
        # 根据MailDrop的实际HTML结构调整
        email_pattern = r'<div[^>]*class="[^"]*message[^"]*"[^>]*>(.*?)</div>'
        email_matches = re.findall(email_pattern, html, re.DOTALL)
        
        for match in email_matches:
            # 提取主题
            subject_pattern = r'<div[^>]*class="[^"]*subject[^"]*"[^>]*>(.*?)</div>'
            subject_match = re.search(subject_pattern, match)
            subject = subject_match.group(1) if subject_match else "无主题"
            
            # 提取发件人
            from_pattern = r'<div[^>]*class="[^"]*from[^"]*"[^>]*>(.*?)</div>'
            from_match = re.search(from_pattern, match)
            from_addr = from_match.group(1) if from_match else "未知发件人"
            
            # 提取正文
            body_pattern = r'<div[^>]*class="[^"]*body[^"]*"[^>]*>(.*?)</div>'
            body_match = re.search(body_pattern, match)
            body = body_match.group(1) if body_match else ""
            
            emails.append({
                "subject": self._clean_html(subject),
                "from": self._clean_html(from_addr),
                "body": self._clean_html(body),
                "service": self.name
            })
            
        return emails
    
    def _clean_html(self, html: str) -> str:
        """清理HTML标签"""
        clean = re.compile('<.*?>')
        return re.sub(clean, '', html).strip()
    
    def _extract_links(self, text: str) -> List[str]:
        """从文本中提取链接"""
        url_pattern = r'https?://[^\s<>"]+|www\.[^\s<>"]+'
        return re.findall(url_pattern, text)


# 工厂函数
def create_maildrop_service() -> MailDropService:
    """创建MailDrop服务实例"""
    return MailDropService()