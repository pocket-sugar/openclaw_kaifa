"""
mails.org 邮箱服务实现
https://mails.org/cn/
"""

import re
import random
import string
from typing import Optional, List, Dict, Any
from .base import EmailService


class MailsOrgService(EmailService):
    """mails.org 临时邮箱服务"""
    
    def __init__(self):
        super().__init__("mails_org", "https://mails.org/cn/")
        self.email_domain = "mails.org"
        
    async def get_new_email(self) -> Optional[str]:
        """
        获取新的mails.org邮箱地址
        
        注意：mails.org可能需要通过浏览器自动化来获取邮箱，
        这里先实现一个简单的随机生成版本
        """
        try:
            # 生成随机用户名
            username = self._generate_username()
            email = f"{username}@{self.email_domain}"
            
            # 在实际实现中，这里应该：
            # 1. 访问 mails.org/cn/
            # 2. 点击"生成邮箱"按钮
            # 3. 从页面提取邮箱地址
            
            print(f"[mails.org] 生成邮箱: {email}")
            return email
            
        except Exception as e:
            print(f"[mails.org] 获取邮箱失败: {e}")
            self.record_failure()
            return None
    
    async def check_inbox(self, email: str) -> List[Dict[str, Any]]:
        """
        检查mails.org收件箱
        
        Args:
            email: 邮箱地址
            
        Returns:
            List[Dict]: 邮件列表
        """
        try:
            # 提取用户名
            username = email.split("@")[0]
            
            # 构建收件箱URL
            inbox_url = f"{self.base_url}inbox/{username}/"
            
            if not self.session:
                return []
                
            async with self.session.get(inbox_url, timeout=30) as response:
                if response.status != 200:
                    print(f"[mails.org] 访问收件箱失败: {response.status}")
                    return []
                    
                html = await response.text()
                
                # 解析邮件列表
                # 这里需要根据mails.org的实际HTML结构来解析
                # 暂时返回空列表，实际实现时需要完善
                emails = self._parse_inbox_html(html)
                return emails
                
        except Exception as e:
            print(f"[mails.org] 检查收件箱失败: {e}")
            return []
    
    async def get_verification_link(self, email: str, keyword: str = "verify") -> Optional[str]:
        """
        从mails.org收件箱获取验证链接
        
        Args:
            email: 邮箱地址
            keyword: 搜索关键词
            
        Returns:
            Optional[str]: 验证链接
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
            print(f"[mails.org] 获取验证链接失败: {e}")
            return None
    
    def _generate_username(self, length: int = 12) -> str:
        """生成随机用户名"""
        chars = string.ascii_lowercase + string.digits
        return ''.join(random.choice(chars) for _ in range(length))
    
    def _parse_inbox_html(self, html: str) -> List[Dict[str, Any]]:
        """
        解析收件箱HTML
        
        注意：这需要根据mails.org的实际HTML结构来调整
        这里只是一个示例实现
        """
        emails = []
        
        # 简单的正则匹配示例
        # 实际实现时需要使用更健壮的HTML解析库如BeautifulSoup
        
        # 查找邮件项
        email_pattern = r'<div class="email-item".*?>(.*?)</div>'
        email_matches = re.findall(email_pattern, html, re.DOTALL)
        
        for match in email_matches:
            # 提取主题
            subject_pattern = r'<span class="subject">(.*?)</span>'
            subject_match = re.search(subject_pattern, match)
            subject = subject_match.group(1) if subject_match else "无主题"
            
            # 提取发件人
            from_pattern = r'<span class="from">(.*?)</span>'
            from_match = re.search(from_pattern, match)
            from_addr = from_match.group(1) if from_match else "未知发件人"
            
            # 提取正文（简化版）
            body_pattern = r'<div class="body">(.*?)</div>'
            body_match = re.search(body_pattern, match)
            body = body_match.group(1) if body_match else ""
            
            emails.append({
                "subject": subject.strip(),
                "from": from_addr.strip(),
                "body": body.strip(),
                "service": self.name
            })
            
        return emails
    
    def _extract_links(self, text: str) -> List[str]:
        """从文本中提取链接"""
        url_pattern = r'https?://[^\s<>"]+|www\.[^\s<>"]+'
        return re.findall(url_pattern, text)


# 工厂函数
def create_mails_org_service() -> MailsOrgService:
    """创建mails.org服务实例"""
    return MailsOrgService()