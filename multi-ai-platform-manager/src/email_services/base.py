"""
邮箱服务基础接口
定义所有邮箱服务必须实现的方法
"""

from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any
import asyncio
from datetime import datetime

# 尝试导入aiohttp，如果失败则使用备用方案
try:
    import aiohttp
    HAS_AIOHTTP = True
except ImportError:
    HAS_AIOHTTP = False
    print("警告: aiohttp未安装，网络功能将受限")


class EmailService(ABC):
    """邮箱服务抽象基类"""
    
    def __init__(self, name: str, base_url: str):
        self.name = name
        self.base_url = base_url
        self.session: Optional[aiohttp.ClientSession] = None
        self.is_healthy = True
        self.failure_count = 0
        self.max_failures = 3
        self.last_checked = None
        
    async def __aenter__(self):
        """异步上下文管理器入口"""
        if HAS_AIOHTTP:
            self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口"""
        if HAS_AIOHTTP and self.session:
            await self.session.close()
            
    @abstractmethod
    async def get_new_email(self) -> Optional[str]:
        """
        获取新的邮箱地址
        
        Returns:
            Optional[str]: 邮箱地址，如果获取失败返回None
        """
        pass
    
    @abstractmethod
    async def check_inbox(self, email: str) -> List[Dict[str, Any]]:
        """
        检查邮箱收件箱
        
        Args:
            email: 邮箱地址
            
        Returns:
            List[Dict]: 邮件列表，每个邮件包含subject, from, body等字段
        """
        pass
    
    @abstractmethod
    async def get_verification_link(self, email: str, keyword: str = "verify") -> Optional[str]:
        """
        从收件箱获取验证链接
        
        Args:
            email: 邮箱地址
            keyword: 搜索关键词，默认为"verify"
            
        Returns:
            Optional[str]: 验证链接，如果未找到返回None
        """
        pass
    
    async def is_available(self) -> bool:
        """
        检查服务是否可用
        
        Returns:
            bool: 服务是否可用
        """
        if self.failure_count >= self.max_failures:
            # 如果失败次数过多，暂时标记为不可用
            self.is_healthy = False
            return False
            
        try:
            if HAS_AIOHTTP:
                # 尝试访问服务首页
                if not self.session:
                    self.session = aiohttp.ClientSession()
                    
                async with self.session.get(self.base_url, timeout=10) as response:
                    self.is_healthy = response.status == 200
                    if self.is_healthy:
                        self.failure_count = 0
                    else:
                        self.failure_count += 1
                        
                    self.last_checked = datetime.now()
                    return self.is_healthy
            else:
                # 没有aiohttp，假设服务可用
                self.is_healthy = True
                self.failure_count = 0
                self.last_checked = datetime.now()
                return True
                
        except Exception as e:
            print(f"服务 {self.name} 健康检查失败: {e}")
            self.failure_count += 1
            self.is_healthy = False
            self.last_checked = datetime.now()
            return False
    
    def record_failure(self):
        """记录失败"""
        self.failure_count += 1
        if self.failure_count >= self.max_failures:
            self.is_healthy = False
            
    def record_success(self):
        """记录成功"""
        self.failure_count = 0
        self.is_healthy = True
        
    def should_retry(self) -> bool:
        """是否应该重试"""
        return self.is_healthy or (self.failure_count < self.max_failures)
        
    def get_status(self) -> Dict[str, Any]:
        """获取服务状态"""
        return {
            "name": self.name,
            "healthy": self.is_healthy,
            "failure_count": self.failure_count,
            "last_checked": self.last_checked.isoformat() if self.last_checked else None
        }


class EmailServiceManager:
    """邮箱服务管理器，负责轮换和故障转移"""
    
    def __init__(self):
        self.services: List[EmailService] = []
        self.current_index = 0
        self.rotation_enabled = True
        
    def add_service(self, service: EmailService):
        """添加邮箱服务"""
        self.services.append(service)
        
    def remove_service(self, service_name: str):
        """移除邮箱服务"""
        self.services = [s for s in self.services if s.name != service_name]
        
    async def get_healthy_services(self) -> List[EmailService]:
        """获取健康的服务列表"""
        healthy_services = []
        for service in self.services:
            if await service.is_available():
                healthy_services.append(service)
        return healthy_services
        
    async def get_next_email(self) -> Optional[str]:
        """
        获取下一个可用的邮箱地址
        
        Returns:
            Optional[str]: 邮箱地址，如果所有服务都失败返回None
        """
        if not self.services:
            return None
            
        # 如果启用了轮换，从当前索引开始
        start_index = self.current_index if self.rotation_enabled else 0
        attempts = 0
        
        while attempts < len(self.services):
            index = (start_index + attempts) % len(self.services)
            service = self.services[index]
            
            if service.should_retry():
                try:
                    email = await service.get_new_email()
                    if email:
                        # 成功获取邮箱，更新索引
                        if self.rotation_enabled:
                            self.current_index = (index + 1) % len(self.services)
                        service.record_success()
                        return email
                    else:
                        service.record_failure()
                except Exception as e:
                    print(f"服务 {service.name} 获取邮箱失败: {e}")
                    service.record_failure()
                    
            attempts += 1
            
        return None  # 所有服务都失败
        
    async def check_all_services_health(self):
        """检查所有服务的健康状态"""
        tasks = [service.is_available() for service in self.services]
        await asyncio.gather(*tasks, return_exceptions=True)
        
    def get_all_status(self) -> List[Dict[str, Any]]:
        """获取所有服务状态"""
        return [service.get_status() for service in self.services]