# OpenClaw 集成指南 - 智能提前执行系统

## 🎯 目标
将DeepSeek Auto Renew的智能提前执行系统集成到OpenClaw中，实现：
1. **自动监控API Key额度**
2. **智能预测执行时机**
3. **提前注册新API Key**
4. **自动切换配置**

## 📋 集成步骤

### 步骤1：创建OpenClaw定时任务

#### 任务配置 (`smart_early_renewal_job.json`):
```json
{
  "name": "DeepSeek智能提前续期",
  "schedule": {
    "kind": "every",
    "everyMs": 1800000  // 每30分钟执行一次
  },
  "sessionTarget": "isolated",
  "payload": {
    "kind": "agentTurn",
    "message": "执行智能提前续期检查：cd /root/.openclaw/workspace/deepseek-auto-renew && python3 smart_early_renewal.py --check-only",
    "model": "deepseek-chat",
    "timeoutSeconds": 300
  },
  "delivery": {
    "mode": "announce",
    "channel": "webchat",
    "bestEffort": true
  },
  "enabled": true
}
```

#### 紧急任务配置 (`urgent_renewal_job.json`):
```json
{
  "name": "DeepSeek紧急续期",
  "schedule": {
    "kind": "every",
    "everyMs": 300000  // 每5分钟执行一次（仅当有紧急任务时）
  },
  "sessionTarget": "isolated",
  "payload": {
    "kind": "agentTurn",
    "message": "执行紧急续期任务：cd /root/.openclaw/workspace/deepseek-auto-renew && python3 smart_early_renewal.py --execute-urgent",
    "model": "deepseek-chat",
    "timeoutSeconds": 600
  },
  "delivery": {
    "mode": "announce",
    "channel": "webchat",
    "bestEffort": true
  },
  "enabled": false  // 默认禁用，由智能系统动态启用
}
```

### 步骤2：创建智能监控脚本

#### 监控脚本 (`monitor_and_control.py`):
```python
#!/usr/bin/env python3
"""
智能监控和控制脚本
根据API Key状态动态调整OpenClaw定时任务
"""

import json
import os
import subprocess
import time
from datetime import datetime
from typing import Dict, Any

# OpenClaw配置
OPENCLAW_CONFIG = {
    'gateway_url': 'http://localhost:18789',
    'jobs_dir': '/root/.openclaw/workspace/deepseek-auto-renew/openclaw_jobs'
}

class OpenClawJobManager:
    """OpenClaw任务管理器"""
    
    def __init__(self):
        self.jobs = self.load_jobs()
    
    def load_jobs(self) -> Dict[str, Any]:
        """加载任务配置"""
        jobs = {}
        if os.path.exists(OPENCLAW_CONFIG['jobs_dir']):
            for filename in os.listdir(OPENCLAW_CONFIG['jobs_dir']):
                if filename.endswith('.json'):
                    job_id = filename.replace('.json', '')
                    with open(os.path.join(OPENCLAW_CONFIG['jobs_dir'], filename), 'r') as f:
                        jobs[job_id] = json.load(f)
        return jobs
    
    def enable_job(self, job_id: str):
        """启用任务"""
        if job_id in self.jobs:
            self.jobs[job_id]['enabled'] = True
            self.save_job(job_id)
            print(f"✅ 启用任务: {job_id}")
    
    def disable_job(self, job_id: str):
        """禁用任务"""
        if job_id in self.jobs:
            self.jobs[job_id]['enabled'] = False
            self.save_job(job_id)
            print(f"⏸️  禁用任务: {job_id}")
    
    def save_job(self, job_id: str):
        """保存任务配置"""
        os.makedirs(OPENCLAW_CONFIG['jobs_dir'], exist_ok=True)
        filename = os.path.join(OPENCLAW_CONFIG['jobs_dir'], f"{job_id}.json")
        with open(filename, 'w') as f:
            json.dump(self.jobs[job_id], f, indent=2)
    
    def update_schedule(self, job_id: str, interval_ms: int):
        """更新任务执行间隔"""
        if job_id in self.jobs:
            self.jobs[job_id]['schedule']['everyMs'] = interval_ms
            self.save_job(job_id)
            print(f"🔄 更新任务间隔: {job_id} -> {interval_ms/60000:.1f}分钟")

class SmartScheduler:
    """智能调度器"""
    
    def __init__(self):
        self.job_manager = OpenClawJobManager()
        self.last_check = None
        self.urgency_level = 'normal'  # normal, high, critical
    
    def analyze_api_status(self, api_status: Dict[str, Any]) -> str:
        """分析API状态，返回紧急级别"""
        if api_status.get('can_execute_task', True) == False:
            return 'critical'  # 无法执行任务
        
        quota_percentage = api_status.get('percentage_remaining', 100)
        
        if quota_percentage < 5:
            return 'critical'
        elif quota_percentage < 15:
            return 'high'
        elif quota_percentage < 30:
            return 'normal'
        else:
            return 'low'
    
    def adjust_scheduling(self, urgency_level: str):
        """根据紧急级别调整调度"""
        print(f"\n📊 当前紧急级别: {urgency_level}")
        
        if urgency_level == 'critical':
            # 紧急情况：启用紧急任务，高频检查
            self.job_manager.enable_job('urgent_renewal')
            self.job_manager.update_schedule('urgent_renewal', 300000)  # 5分钟
            self.job_manager.update_schedule('smart_early_renewal', 900000)  # 15分钟
            print("🚨 进入紧急模式：高频监控和立即执行")
            
        elif urgency_level == 'high':
            # 高级别：启用紧急任务，中频检查
            self.job_manager.enable_job('urgent_renewal')
            self.job_manager.update_schedule('urgent_renewal', 900000)  # 15分钟
            self.job_manager.update_schedule('smart_early_renewal', 1800000)  # 30分钟
            print("⚠️  进入高级模式：加强监控")
            
        elif urgency_level == 'normal':
            # 正常级别：禁用紧急任务，正常检查
            self.job_manager.disable_job('urgent_renewal')
            self.job_manager.update_schedule('smart_early_renewal', 3600000)  # 60分钟
            print("✅ 进入正常模式：定期监控")
            
        else:  # low
            # 低级别：低频检查
            self.job_manager.disable_job('urgent_renewal')
            self.job_manager.update_schedule('smart_early_renewal', 7200000)  # 120分钟
            print("🟢 进入低级别模式：低频监控")
    
    def run(self):
        """运行智能调度"""
        print("🤖 启动智能调度系统")
        print("=" * 50)
        
        while True:
            try:
                # 1. 检查API状态（这里应该调用实际的检查逻辑）
                api_status = self.simulate_api_check()
                
                # 2. 分析紧急级别
                urgency = self.analyze_api_status(api_status)
                
                # 3. 调整调度策略
                if urgency != self.urgency_level:
                    print(f"\n🔄 紧急级别变化: {self.urgency_level} -> {urgency}")
                    self.urgency_level = urgency
                    self.adjust_scheduling(urgency)
                
                # 4. 记录日志
                self.log_status(api_status, urgency)
                
                # 5. 等待下一次检查
                wait_time = self.get_wait_time(urgency)
                print(f"\n⏳ 下次检查: {wait_time/60:.0f}分钟后")
                time.sleep(wait_time)
                
            except KeyboardInterrupt:
                print("\n👋 手动停止智能调度系统")
                break
            except Exception as e:
                print(f"\n❌ 调度错误: {e}")
                time.sleep(300)  # 错误后等待5分钟
    
    def simulate_api_check(self) -> Dict[str, Any]:
        """模拟API检查（实际应该调用真正的检查逻辑）"""
        # 这里应该调用 smart_early_renewal.py 的检查功能
        import random
        return {
            'can_execute_task': random.random() > 0.1,  # 90%的概率可以执行任务
            'percentage_remaining': random.uniform(0, 100),
            'status': random.choice(['HEALTHY', 'WARNING', 'URGENT', 'CRITICAL'])
        }
    
    def get_wait_time(self, urgency: str) -> int:
        """根据紧急级别获取等待时间（秒）"""
        wait_times = {
            'critical': 300,   # 5分钟
            'high': 900,       # 15分钟
            'normal': 1800,    # 30分钟
            'low': 3600        # 60分钟
        }
        return wait_times.get(urgency, 1800)
    
    def log_status(self, api_status: Dict[str, Any], urgency: str):
        """记录状态"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        log_entry = {
            'timestamp': timestamp,
            'urgency': urgency,
            'api_status': api_status,
            'scheduling': {
                'smart_early_renewal': self.job_manager.jobs.get('smart_early_renewal', {}).get('schedule', {}),
                'urgent_renewal': {
                    'enabled': self.job_manager.jobs.get('urgent_renewal', {}).get('enabled', False),
                    'schedule': self.job_manager.jobs.get('urgent_renewal', {}).get('schedule', {})
                }
            }
        }
        
        # 保存日志
        log_dir = 'logs/scheduling'
        os.makedirs(log_dir, exist_ok=True)
        log_file = os.path.join(log_dir, f"scheduling_{datetime.now().strftime('%Y%m%d')}.jsonl")
        
        with open(log_file, 'a') as f:
            f.write(json.dumps(log_entry) + '\n')

if __name__ == "__main__":
    scheduler = SmartScheduler()
    scheduler.run()
```

### 步骤3：创建OpenClaw定时任务

使用OpenClaw CLI创建任务：

```bash
# 创建智能提前续期任务
openclaw cron add --file /root/.openclaw/workspace/deepseek-auto-renew/openclaw_jobs/smart_early_renewal.json

# 创建紧急续期任务（默认禁用）
openclaw cron add --file /root/.openclaw/workspace/deepseek-auto-renew/openclaw_jobs/urgent_renewal.json

# 启动智能调度系统
cd /root/.openclaw/workspace/deepseek-auto-renew
python3 monitor_and_control.py
```

### 步骤4：配置自动切换

#### OpenClaw API Key自动更新脚本 (`update_openclaw_config.py`):
```python
#!/usr/bin/env python3
"""
自动更新OpenClaw配置中的API Key
"""

import json
import os
import shutil
from datetime import datetime

# 配置文件路径
OPENCLAW_CONFIG = '/root/.openclaw/openclaw.json'
OPENCLAW_MODELS = '/root/.openclaw/agents/main/agent/models.json'
BACKUP_DIR = '/root/.openclaw/config_backups'

def backup_config():
    """备份配置文件"""
    os.makedirs(BACKUP_DIR, exist_ok=True)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    for config_file in [OPENCLAW_CONFIG, OPENCLAW_MODELS]:
        if os.path.exists(config_file):
            backup_file = os.path.join(BACKUP_DIR, f"{os.path.basename(config_file)}.{timestamp}.bak")
            shutil.copy2(config_file, backup_file)
            print(f"✅ 备份: {config_file} -> {backup_file}")

def update_deepseek_api_key(new_api_key: str):
    """更新DeepSeek API Key"""
    
    # 1. 更新models.json
    if os.path.exists(OPENCLAW_MODELS):
        with open(OPENCLAW_MODELS, 'r') as f:
            config = json.load(f)
        
        # 更新DeepSeek API Key
        if 'providers' in config and 'deepseek' in config['providers']:
            config['providers']['deepseek']['apiKey'] = new_api_key
            print(f"✅ 更新DeepSeek API Key: {new_api_key[:15]}...")
        
        with open(OPENCLAW_MODELS, 'w') as f:
            json.dump(config, f, indent=2)
    
    # 2. 更新openclaw.json（如果需要）
    if os.path.exists(OPENCLAW_CONFIG):
        with open(OPENCLAW_CONFIG, 'r') as f:
            config = json.load(f)
        
        # 这里根据实际配置结构更新
        # 可能需要更新多个位置的API Key配置
        
        with open(OPENCLAW_CONFIG, 'w') as f:
            json.dump(config, f, indent=2)
    
    print("✅ OpenClaw配置更新完成")

def restart_openclaw():
    """重启OpenClaw服务"""
    print("🔄 重启OpenClaw服务...")
    
    # 方法1: 使用systemd（如果可用）
    # subprocess.run(['systemctl', 'restart', 'openclaw'], check=False)
    
    # 方法2: 发送SIGUSR1信号
    import subprocess
    result = subprocess.run(['pkill', '-SIGUSR1', 'openclaw'], capture_output=True, text=True)
    
    if result.returncode == 0:
        print("✅ OpenClaw重启信号已发送")
    else:
        print("⚠️  重启失败，可能需要手动重启")
        print(f"错误: {result.stderr}")

def main():
    """主函数"""
    print("⚙️  OpenClaw API Key自动更新系统")
    print("=" * 50)
    
    # 从智能系统获取新的API Key
    # 这里应该从smart_early_renewal.py的结果中获取
    new_api_key = "sk-example-key
    
    print(f"新API Key: {new_api_key}")
    
    # 1. 备份当前配置
    backup_config()
    
    # 2. 更新API Key
    update_deepseek_api_key(new_api_key)
    
    # 3. 重启OpenClaw
    restart_openclaw()
    
    print("\n🎉 API Key更新完成！")
    print(f"新Key: {new_api_key[:20]}...")
    print(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    main()
```

## 🚀 完整工作流程

### 正常监控流程：
```
1. 智能调度系统每30分钟检查API Key状态
2. 如果额度充足（>30%），保持正常监控频率
3. 如果额度较低（15-30%），增加监控频率到15分钟
4. 如果额度危急（<15%），启用紧急任务，每5分钟检查
```

### 提前执行流程：
```
1. 检测到API Key额度接近任务执行阈值
2. 智能系统分析最佳执行时间
3. 提前注册新的DeepSeek账号
4. 获取新的API Key
5. 自动更新OpenClaw配置
6. 重启OpenClaw服务
7. 验证新Key工作正常
```

### 紧急处理流程：
```
1. 检测到API Key无法执行续期任务
2. 立即启用最高优先级监控
3. 使用备用API Key（如果有）
4. 立即执行紧急注册流程
5. 快速切换配置
6. 发送警报通知
```

## 📊 监控和警报

### 监控指标：
1. **API Key剩余额度百分比**
2. **任务执行成功率**
3. **注册流程平均时间**
4. **配置切换成功率**
5. **系统运行状态**

### 警报级别：
- **🟢 正常**: 额度 > 30%，无需操作
- **🟡 警告**: 额度 15-30%，需要关注
- **🟠 紧急**: 额度 5-15%，需要立即计划执行
- **🔴 危急**: 额度 < 5% 或无法执行任务，立即执行

## 🔧 故障排除

### 常见问题：
1. **API Key检查失败**: 检查网络连接和API端点
2. **注册流程失败**: 检查验证码识别和表单填写
3. **配置更新失败**: 检查文件权限和配置格式
4. **服务重启失败**: 检查OpenClaw服务状态

### 恢复策略：
1. **自动重试**: 失败任务自动重试3次
2. **备用方案**: 使用备用邮箱服务和注册策略
3. **手动干预**: 关键失败时发送通知请求手动干预
4. **回滚机制**: 配置更新失败时自动回滚到上一个版本

## 📈 优化建议

### 短期优化：
1. 实现真正的API额度检查（调用DeepSeek