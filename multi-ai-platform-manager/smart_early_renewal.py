#!/usr/bin/env python3
"""
智能提前执行系统
在API Key额度足够执行自动化任务时提前注册新Key
避免等到额度耗尽才行动
"""

import asyncio
import json
import logging
import os
import sys
import time
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
import math

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.email_services import create_email_service_manager
from src.browser_automation.deepseek_registrar import create_deepseek_registrar
from src.browser_automation.captcha_solver import create_default_captcha_manager

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/smart_renewal.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class SmartEarlyRenewalSystem:
    """智能提前执行系统"""
    
    def __init__(self, config_path: str = "config/smart_settings.json"):
        """
        初始化智能提前执行系统
        
        Args:
            config_path: 配置文件路径
        """
        self.config_path = config_path
        self.config = self.load_config()
        
        # 初始化组件
        self.email_manager = create_email_service_manager()
        self.registrar = create_deepseek_registrar(headless=True)
        self.captcha_manager = create_default_captcha_manager()
        
        # 智能策略配置
        self.task_cost_estimate = self.config.get('task_cost_estimate', 6000)  # 默认任务成本
        self.safety_buffer = self.config.get('safety_buffer', 1.5)  # 安全缓冲区系数
        self.min_quota_for_task = self.task_cost_estimate * self.safety_buffer
        
        # 状态跟踪
        self.execution_history = []
        self.success_rate = 0.8  # 初始成功率
        self.adaptive_threshold = self.min_quota_for_task
        
    def load_config(self) -> Dict[str, Any]:
        """加载配置"""
        default_config = {
            'task_cost_estimate': 6000,  # 任务成本估算（tokens）
            'safety_buffer': 1.5,        # 安全缓冲区系数
            'check_interval_minutes': 30, # 检查间隔（分钟）
            'max_concurrent_tasks': 1,   # 最大并发任务数
            'enable_adaptive_threshold': True,  # 启用自适应阈值
            'min_success_rate': 0.6,     # 最小成功率
            'max_retry_attempts': 3,     # 最大重试次数
            'retry_delay_minutes': 5,    # 重试延迟（分钟）
            'notify_on_critical': True,  # 关键情况通知
            'log_detailed_stats': True,  # 记录详细统计
        }
        
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    user_config = json.load(f)
                    default_config.update(user_config)
            else:
                logger.warning(f"配置文件不存在，使用默认配置: {self.config_path}")
        except Exception as e:
            logger.error(f"加载配置文件失败: {e}")
            
        return default_config
    
    def save_config(self):
        """保存配置"""
        try:
            os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
            logger.debug(f"配置已保存到: {self.config_path}")
        except Exception as e:
            logger.error(f"保存配置失败: {e}")
    
    def analyze_api_key_status(self, api_key_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        分析API Key状态，判断是否需要提前执行
        
        Args:
            api_key_info: API Key信息
            
        Returns:
            Dict: 分析结果
        """
        current_quota = api_key_info.get('remaining_quota', 0)
        percentage = api_key_info.get('percentage_remaining', 0)
        
        # 计算动态阈值
        dynamic_threshold = self.calculate_dynamic_threshold(current_quota)
        
        # 判断状态
        status = self.determine_status(current_quota, dynamic_threshold)
        
        # 计算建议执行时间
        suggested_time = self.suggest_execution_time(current_quota, dynamic_threshold)
        
        return {
            'api_key': api_key_info.get('api_key', '')[:10] + '...',
            'email': api_key_info.get('email', ''),
            'current_quota': current_quota,
            'percentage_remaining': percentage,
            'dynamic_threshold': dynamic_threshold,
            'status': status,
            'suggested_execution': suggested_time,
            'quota_surplus': current_quota - dynamic_threshold,
            'can_execute_task': current_quota >= self.min_quota_for_task,
        }
    
    def calculate_dynamic_threshold(self, current_quota: int) -> int:
        """
        计算动态阈值
        
        Args:
            current_quota: 当前额度
            
        Returns:
            int: 动态阈值
        """
        if not self.config.get('enable_adaptive_threshold', True):
            return self.min_quota_for_task
        
        # 基础阈值
        base_threshold = self.min_quota_for_task
        
        # 根据历史成功率调整
        adaptive_factor = 1.0 + (1.0 - self.success_rate)  # 成功率越低，阈值越高
        adaptive_threshold = int(base_threshold * adaptive_factor)
        
        # 考虑使用趋势（如果历史数据可用）
        if hasattr(self, 'usage_history') and len(self.usage_history) > 1:
            avg_daily_usage = self.calculate_average_usage()
            if avg_daily_usage > 0:
                # 确保至少还有2天的使用量
                days_remaining = current_quota / avg_daily_usage
                if days_remaining < 3:  # 少于3天
                    adaptive_threshold = max(adaptive_threshold, int(avg_daily_usage * 2))
        
        # 更新自适应阈值
        self.adaptive_threshold = adaptive_threshold
        
        return adaptive_threshold
    
    def determine_status(self, current_quota: int, threshold: int) -> str:
        """
        确定状态
        
        Args:
            current_quota: 当前额度
            threshold: 阈值
            
        Returns:
            str: 状态描述
        """
        if current_quota < self.min_quota_for_task:
            return 'CRITICAL'  # 额度不足以执行任务
        elif current_quota < threshold:
            return 'URGENT'    # 需要尽快执行
        elif current_quota < threshold * 2:
            return 'WARNING'   # 需要关注
        else:
            return 'HEALTHY'   # 健康
    
    def suggest_execution_time(self, current_quota: int, threshold: int) -> Optional[datetime]:
        """
        建议执行时间
        
        Args:
            current_quota: 当前额度
            threshold: 阈值
            
        Returns:
            Optional[datetime]: 建议执行时间
        """
        if current_quota >= threshold * 2:
            return None  # 无需立即执行
        
        # 估算每日使用量
        avg_daily_usage = self.calculate_average_usage() or (current_quota * 0.1)
        
        if avg_daily_usage <= 0:
            return datetime.now() + timedelta(hours=24)  # 默认24小时后
        
        # 计算剩余天数
        days_until_threshold = (current_quota - threshold) / avg_daily_usage
        
        if days_until_threshold <= 0:
            return datetime.now()  # 立即执行
        elif days_until_threshold <= 1:
            return datetime.now() + timedelta(hours=6)  # 6小时内执行
        elif days_until_threshold <= 3:
            return datetime.now() + timedelta(days=1)   # 1天内执行
        else:
            return datetime.now() + timedelta(days=2)   # 2天内执行
    
    def calculate_average_usage(self) -> float:
        """计算平均使用量"""
        if not hasattr(self, 'usage_history') or len(self.usage_history) < 2:
            return 0
        
        total_usage = 0
        for i in range(1, len(self.usage_history)):
            usage = self.usage_history[i-1]['quota'] - self.usage_history[i]['quota']
            time_diff = (self.usage_history[i-1]['timestamp'] - 
                        self.usage_history[i]['timestamp']).total_seconds() / 86400  # 转换为天
            if time_diff > 0:
                total_usage += usage / time_diff
        
        return total_usage / (len(self.usage_history) - 1) if len(self.usage_history) > 1 else 0
    
    async def execute_early_renewal(self, api_key_info: Dict[str, Any]) -> bool:
        """
        执行提前续期
        
        Args:
            api_key_info: 需要续期的API Key信息
            
        Returns:
            bool: 是否成功
        """
        logger.info(f"开始提前续期: {api_key_info.get('email', '')}")
        
        try:
            # 1. 生成新邮箱
            new_email = self.email_manager.generate_email()
            logger.info(f"生成新邮箱: {new_email}")
            
            # 2. 启动浏览器
            if not await self.registrar.start():
                logger.error("浏览器启动失败")
                return False
            
            # 3. 执行注册流程
            success = await self.perform_registration(new_email)
            
            # 4. 关闭浏览器
            await self.registrar.stop()
            
            if success:
                logger.info(f"提前续期成功: {new_email}")
                self.record_success()
                return True
            else:
                logger.warning(f"提前续期失败: {new_email}")
                self.record_failure()
                return False
                
        except Exception as e:
            logger.error(f"提前续期异常: {e}")
            self.record_failure()
            return False
    
    async def perform_registration(self, email: str) -> bool:
        """
        执行注册流程
        
        Args:
            email: 邮箱地址
            
        Returns:
            bool: 是否成功
        """
        # 这里应该实现完整的DeepSeek注册流程
        # 包括：访问注册页面、填写表单、解决验证码、获取API Key等
        
        # 模拟实现
        logger.info(f"模拟注册流程: {email}")
        await asyncio.sleep(2)  # 模拟注册时间
        
        # 80%的成功率（模拟）
        import random
        return random.random() < 0.8
    
    def record_success(self):
        """记录成功"""
        self.execution_history.append({
            'timestamp': datetime.now(),
            'success': True,
            'type': 'early_renewal'
        })
        self.update_success_rate()
    
    def record_failure(self):
        """记录失败"""
        self.execution_history.append({
            'timestamp': datetime.now(),
            'success': False,
            'type': 'early_renewal'
        })
        self.update_success_rate()
    
    def update_success_rate(self):
        """更新成功率"""
        if not self.execution_history:
            return
        
        recent_history = [h for h in self.execution_history 
                         if h['timestamp'] > datetime.now() - timedelta(days=7)]
        
        if recent_history:
            successes = sum(1 for h in recent_history if h['success'])
            self.success_rate = successes / len(recent_history)
    
    def generate_report(self, analysis_results: List[Dict[str, Any]]) -> str:
        """
        生成报告
        
        Args:
            analysis_results: 分析结果列表
            
        Returns:
            str: 报告文本
        """
        report = []
        report.append("=" * 70)
        report.append("智能提前执行系统 - 分析报告")
        report.append(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("=" * 70)
        report.append("")
        
        # 汇总统计
        critical_count = sum(1 for r in analysis_results if r['status'] == 'CRITICAL')
        urgent_count = sum(1 for r in analysis_results if r['status'] == 'URGENT')
        warning_count = sum(1 for r in analysis_results if r['status'] == 'WARNING')
        healthy_count = sum(1 for r in analysis_results if r['status'] == 'HEALTHY')
        
        report.append("📊 状态汇总:")
        report.append(f"  🔴 CRITICAL (立即执行): {critical_count}")
        report.append(f"  🟠 URGENT (尽快执行): {urgent_count}")
        report.append(f"  🟡 WARNING (关注): {warning_count}")
        report.append(f"  🟢 HEALTHY (健康): {healthy_count}")
        report.append("")
        
        # 详细分析
        report.append("🔍 详细分析:")
        for result in analysis_results:
            status_emoji = {
                'CRITICAL': '🔴',
                'URGENT': '🟠',
                'WARNING': '🟡',
                'HEALTHY': '🟢'
            }.get(result['status'], '⚪')
            
            report.append(f"{status_emoji} {result['email']}:")
            report.append(f"   当前额度: {result['current_quota']:,} tokens ({result['percentage_remaining']:.1f}%)")
            report.append(f"   动态阈值: {result['dynamic_threshold']:,} tokens")
            report.append(f"   差额: {result['quota_surplus']:+,.0f} tokens")
            
            if result['suggested_execution']:
                exec_time = result['suggested_execution'].strftime('%Y-%m-%d %H:%M')
                report.append(f"   建议执行时间: {exec_time}")
            
            if result['status'] in ['CRITICAL', 'URGENT']:
                report.append(f"   ⚠️  需要提前执行续期任务")
            
            report.append("")
        
        # 系统状态
        report.append("⚙️ 系统状态:")
        report.append(f"   任务成本估算: {self.task_cost_estimate:,} tokens")
        report.append(f"   最小执行额度: {self.min_quota_for_task:,} tokens")
        report.append(f"   自适应阈值: {self.adaptive_threshold:,} tokens")
        report.append(f"   历史成功率: {self.success_rate:.1%}")
        report.append(f"   执行历史: {len(self.execution_history)} 次")
        report.append("")
        
        # 建议
        report.append("💡 建议:")
        if critical_count > 0:
            report.append("   🚨 立即执行CRITICAL状态的API Key续期")
        if urgent_count > 0:
            report.append("   ⚠️  尽快安排URGENT状态的API Key续期")
        if warning_count > 0:
            report.append("   📅 计划WARNING状态的API Key续期")
        
        report.append(f"   建议检查频率: 每{self.config['check_interval_minutes']}分钟")
        report.append("")
        
        report.append("=" * 70)
        
        return "\n".join(report)


async def main():
    """主函数"""
    print("🚀 启动智能提前执行系统")
    print("=" * 70)
    
    # 初始化系统
    system = SmartEarlyRenewalSystem()
    
    # 模拟API Key数据
    demo_api_keys = [
        {
            'api_key': 'sk-example-key',
            'email': 'critical@mails.org',
            'remaining_quota': 1500,
            'percentage_remaining': 0.15,
            'total_quota': 1000000
        },
        {
            'api_key': 'sk-example-key',
            'email': 'low@maildrop.cc',
            'remaining_quota': 8000,
            'percentage_remaining': 0.8,
            'total_quota': 1000000
        },
        {
            'api_key': 'sk-example-key',
            'email': 'normal@fakemail.net',
            'remaining_quota': 30000,
            'percentage_remaining': 3.0,
            'total_quota': 1000000
        },
        {
            'api_key': 'sk-example-key',
            'email': 'healthy@guerrilla.net',
            'remaining_quota': 500000,
            'percentage_remaining': 50.0,
            'total_quota': 1000000
        }
    ]
    
    # 分析API Key状态
    print("\n🔍 分析API Key状态...")
    analysis_results = []
    for api_key in demo_api_keys:
        result = system.analyze_api_key_status(api_key)
        analysis_results.append(result)
    
    # 生成报告
    report = system.generate_report(analysis_results)
    print(report)
    
    # 执行需要立即续期的任务
    print("\n⚡ 执行续期任务...")
    for result in analysis_results:
        if result['status'] in ['CRITICAL', 'URGENT']:
            print(f"执行提前续期: {result