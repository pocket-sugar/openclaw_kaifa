"""
FakeMail 邮箱服务实现
https://www.fakemail.net/
"""

import re
import random
import string
from typing import Optional, List, Dict, Any
from .base import EmailService


class FakeMailService(EmailService):
    """FakeMail 临时邮箱服务"""
    
    def __init__(self):
        super().__init__("fakemail", "https://www.fakemail.net")
        # FakeMail使用随机域名
        self.domains = [
            "fakemail.net",
            "tmpmail.net",
            "tempmail.net"
        ]
        
    async def get_new_email(self) -> Optional[str]:
        """
        获取新的FakeMail邮箱地址
        """
        try:
            # 生成随机用户名和选择域名
            username = self._generate_username()
            domain = random.choice(self.domains)
            email = f"{username}@{domain}"
            
            print(f"[FakeMail] 生成邮箱: {email}")
            return email
            
        except Exception as e:
            print(f"[FakeMail] 获取邮箱失败: {e}")
            self.record_failure()
            return None
    
    async def check_inbox(self, email: str) -> List[Dict[str, Any]]:
        """
        检查FakeMail收件箱
        """
        try:
            # 提取用户名和域名
            username = email.split("@")[0]
            domain = email.split("@")[1]
            
            # FakeMail的收件箱URL格式
            inbox_url = f"{self.base_url}/inbox/{domain}/{username}/"
            
            if not self.session:
                return []
                
            async with self.session.get(inbox_url, timeout=30) as response:
                if response.status != 200:
                    return []
                    
                html = await response.text()
                return self._parse_inbox_html(html, email)
                
        except Exception as e:
            print(f"[FakeMail] 检查收件箱失败: {e}")
            return []
    
    async def get_verification_link(self, email: str, keyword: str = "verify") -> Optional[str]:
        """
        从FakeMail收件箱获取验证链接
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
            print(f"[FakeMail] 获取验证链接失败: {e}")
            return None
    
    def _generate_username(self, length: int = 10) -> str:
        """生成随机用户名"""
        chars = string.ascii_lowercase + string.digits
        return ''.join(random.choice(chars) for _ in range(length))
    
    def _parse_inbox_html(self, html: str, email: str) -> List[Dict[str, Any]]:
        """
        解析FakeMail收件箱HTML
        """
        emails = []
        
        # 查找邮件列表
        # FakeMail的邮件通常在一个表格中
        email_pattern = r'<tr[^>]*class="[^"]*email-item[^"]*"[^>]*>(.*?)</tr>'
        email_matches = re.findall(email_pattern, html, re.DOTALL)
        
        for match in email_matches:
            # 提取主题
            subject_pattern = r'<td[^>]*class="[^"]*subject[^"]*"[^>]*>(.*?)</td>'
            subject_match = re.search(subject_pattern, match)
            subject = subject_match.group(1) if subject_match else "无主题"
            
            # 提取发件人
            from_pattern = r'<td[^>]*class="[^"]*from[^"]*"[^>]*>(.*?)</td>'
            from_match = re.search(from_pattern, match)
            from_addr = from_match.group(1) if from_match else "未知发件人"
            
            # 提取日期
            date_pattern = r'<td[^>]*class="[^"]*date[^"]*"[^>]*>(.*?)</td>'
            date_match = re.search(date_pattern, match)
            date = date_match.group(1) if date_match else ""
            
            # 邮件ID（用于查看完整邮件）
            id_pattern = r'data-email-id="([^"]+)"'
            id_match = re.search(id_pattern, match)
            email_id = id_match.group(1) if id_match else ""
            
            # 如果有邮件ID，可以获取完整邮件内容
            body = ""
            # 注意：这里不能直接调用异步函数，在实际使用时会处理
            # if email_id:
            #     body = await self._get_email_body(email, email_id)
            
            emails.append({
                "id": email_id,
                "subject": self._clean_html(subject),
                "from": self._clean_html(from_addr),
                "body": body,
                "date": self._clean_html(date),
                "service": self.name
            })
            
        return emails
    
    async def _get_email_body(self, email: str, email_id: str) -> str:
        """
        获取完整邮件内容
        """
        try:
            username = email.split("@")[0]
            domain = email.split("@")[1]
            
            body_url = f"{self.base_url}/email/{domain}/{username}/{email_id}/"
            
            if not self.session:
                return ""
                
            async with self.session.get(body_url, timeout=30) as response:
                if response.status != 200:
                    return ""
                    
                html = await response.text()
                
                # 提取邮件正文
                body_pattern = r'<div[^>]*class="[^"]*email-body[^"]*"[^>]*>(.*?)</div>'
                body_match = re.search(body_pattern, html, re.DOTALL)
                
                if body_match:
                    return self._clean_html(body_match.group(1))
                else:
                    return ""
                    
        except Exception as e:
            print(f"[FakeMail] 获取邮件正文失败: {e}")
            return ""
    
    def _clean_html(self, html: str) -> str:
        """清理HTML标签"""
        if not html:
            return ""
            
        # 移除脚本和样式
        html = re.sub(r'<script.*?>.*?</script>', '', html, flags=re.DOTALL)
        html = re.sub(r'<style.*?>.*?</style>', '', html, flags=re.DOTALL)
        
        # 移除HTML标签
        clean = re.compile('<.*?>')
        text = re.sub(clean, '', html)
        
        # 解码HTML实体
        import html
        text = html.unescape(text)
        
        # 清理多余空白
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text
    
    def _extract_links(self, text: str) -> List[str]:
        """从文本中提取链接"""
        url_pattern = r'https?://[^\s<>"]+|www\.[^\s<>"]+'
        return re.findall(url_pattern, text)


# 工厂函数
def create_fakemail_service() -> FakeMailService:
    """创建FakeMail服务实例"""
    return FakeMailService()