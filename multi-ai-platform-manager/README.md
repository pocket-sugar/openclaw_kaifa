# DeepSeek Auto Renew

自动注册DeepSeek API账号、获取API Key、监控额度并自动续期的系统。

## 功能特性

- ✅ 多临时邮箱服务轮换（mails.org, MailDrop, FakeMail, Guerrilla Mail）
- ✅ 浏览器自动化注册DeepSeek账号
- ✅ 自动验证码识别（OCR）
- ✅ API Key自动提取
- ✅ 额度监控和自动切换
- ✅ 5分钟重试间隔，避免频繁请求
- ✅ 完全免费，无需付费服务

## 项目结构

```
deepseek-auto-renew/
├── README.md
├── requirements.txt
├── config/
│   ├── email_services.json
│   └── settings.json
├── src/
│   ├── __init__.py
│   ├── main.py
│   ├── email_services/
│   │   ├── __init__.py
│   │   ├── base.py
│   │   ├── mails_org.py
│   │   ├── maildrop.py
│   │   ├── fakemail.py
│   │   └── guerrilla_mail.py
│   ├── browser_automation/
│   │   ├── __init__.py
│   │   ├── deepseek_registrar.py
│   │   └── captcha_solver.py
│   └── utils/
│       ├── __init__.py
│       ├── logger.py
│       └── config_loader.py
├── logs/
└── tests/
```

## 快速开始

### 1. 安装依赖
```bash
pip install -r requirements.txt
playwright install
```

### 2. 配置
编辑 `config/settings.json` 设置阈值和重试间隔。

### 3. 运行
```bash
python src/main.py
```

## 开发计划

### 第一阶段：多邮箱服务集成 ✅
- [x] 项目结构创建
- [x] 基础邮箱服务接口
- [x] 服务轮换和故障转移
- [x] Git提交

### 第二阶段：DeepSeek注册流程 ✅
- [x] 浏览器自动化框架 (Playwright)
- [x] DeepSeek注册页面分析
- [x] 验证码识别集成
- [x] 表单自动填写和提交
- [x] API Key自动提取
- [x] Git提交

### 第三阶段：完整流程
- [ ] 额度监控系统
- [ ] 自动切换逻辑
- [ ] 错误处理和重试
- [ ] 配置文件优化
- [ ] Git提交

## 配置说明

### 邮箱服务配置
系统支持多个临时邮箱服务，自动轮换使用：
- mails.org (中文界面)
- MailDrop (有API接口)
- FakeMail
- Guerrilla Mail (有JSON API)

### 监控配置
- 阈值：10% (当额度低于10%时自动注册新账号)
- 重试间隔：5分钟
- 最大重试次数：3次

## 注意事项

1. 仅用于个人技术实验和教育目的
2. 遵守各服务的使用条款
3. 避免频繁请求，设置合理间隔
4. 免费服务可能不稳定，有多服务备份

## 许可证

MIT License