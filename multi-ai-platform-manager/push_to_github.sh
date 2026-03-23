#!/bin/bash

echo "🚀 GitHub代码推送脚本"
echo "========================"

if [ $# -eq 0 ]; then
    echo "使用方法: $0 <GitHub_PAT_Token>"
    echo ""
    echo "示例:"
    echo "  $0 ghp_xxxxxxxxxxxxxxxxxxxx"
    echo ""
    echo "如何获取GitHub PAT令牌:"
    echo "1. 访问 https://github.com/settings/tokens"
    echo "2. 点击 'Generate new token (classic)'"
    echo "3. 选择权限: repo (完全控制仓库)"
    echo "4. 生成并复制令牌"
    exit 1
fi

GITHUB_TOKEN="$1"
REPO_OWNER="pocket-sugar"
REPO_NAME="projects_openclaw"
PROJECT_NAME="multi-ai-platform-manager"

echo "1. 配置GitHub认证..."
echo "$GITHUB_TOKEN" | gh auth login --with-token

if [ $? -ne 0 ]; then
    echo "❌ GitHub认证失败"
    exit 1
fi

echo "✅ GitHub认证成功"

echo "2. 克隆GitHub仓库..."
cd /root/.openclaw/workspace

if [ -d "$REPO_NAME" ]; then
    echo "⚠️  仓库已存在，更新..."
    cd "$REPO_NAME"
    git pull origin main
else
    echo "正在克隆仓库..."
    git clone "https://${GITHUB_TOKEN}@github.com/${REPO_OWNER}/${REPO_NAME}.git"
    cd "$REPO_NAME"
fi

echo "✅ 仓库准备就绪: $(pwd)"

echo "3. 创建项目目录..."
PROJECT_DIR="$PROJECT_NAME"

if [ -d "$PROJECT_DIR" ]; then
    echo "⚠️  项目目录已存在，备份..."
    BACKUP_DIR="${PROJECT_DIR}_backup_$(date +%Y%m%d_%H%M%S)"
    mv "$PROJECT_DIR" "$BACKUP_DIR"
    echo "✅ 备份完成: $BACKUP_DIR"
fi

mkdir -p "$PROJECT_DIR"

echo "4. 复制代码文件..."
SOURCE_DIR="/root/.openclaw/workspace/code_backup"

# 复制所有文件（除了.git目录）
find "$SOURCE_DIR" -type f -not -path "*/.git/*" | while read -r file; do
    rel_path="${file#$SOURCE_DIR/}"
    target_path="$PROJECT_DIR/$rel_path"
    mkdir -p "$(dirname "$target_path")"
    cp "$file" "$target_path"
    echo "   📄 $rel_path"
done

echo "✅ 代码文件复制完成"

echo "5. 创建项目README..."
cat > "$PROJECT_DIR/README.md" << 'EOF'
# 🚀 Multi-AI Platform Manager

## 📋 项目概述
多AI平台自动管理系统，支持智谱AI等平台的自动化注册、额度监控和API Key自动切换。

## 🎯 核心功能
1. **智谱AI自动化注册** - 支持邮箱注册，自动获取API Key
2. **多平台管理** - 插件式架构，易于扩展
3. **智能额度监控** - 提前预测和续期
4. **无缝API切换** - 自动更新OpenClaw配置

## 📁 项目结构
```
multi-ai-platform-manager/
├── platforms/           # 平台插件
│   └── zhipu/          # 智谱AI平台
│       ├── __init__.py
│       ├── registrar.py    # 注册器
│       └── quota_monitor.py # 额度监控
├── src/                # 核心代码
├── config/             # 配置文件
├── logs/               # 日志文件
└── tests/              # 测试文件
```

## 🚀 快速开始
```bash
# 安装依赖
pip install -r requirements.txt

# 测试智谱AI注册
python3 test_simple.py
```

## 🔧 配置
编辑 `config/settings.json`:
```json
{
  "threshold_percent": 10,
  "check_interval_minutes": 5,
  "headless": true
}
```

## 📈 开发进展
- ✅ 智谱AI注册器核心功能完成
- 🔄 额度监控模块开发中
- 🔄 多平台管理器开发中
- 🔄 OpenClaw集成开发中

## 🤝 贡献
欢迎提交Issue和Pull Request！

## 📄 许可证
MIT License

## 🔗 相关链接
- OpenClaw集成文档: [openclaw_integration.md](./openclaw_integration.md)
- 项目战略调整: [PROJECT_REDIRECT.md](./PROJECT_REDIRECT.md)
- 智能提前执行: [smart_early_renewal.py](./smart_early_renewal.py)
EOF

echo "✅ README创建完成"

echo "6. 提交到GitHub..."
git add "$PROJECT_DIR"

# 配置Git用户
git config user.name "OpenClaw Assistant"
git config user.email "assistant@openclaw.ai"

# 提交
COMMIT_MESSAGE="feat: 添加Multi-AI Platform Manager项目

- 智谱AI自动化注册器
- 多平台插件架构
- 智能额度监控系统
- 项目文档和配置
- OpenClaw集成方案"

git commit -m "$COMMIT_MESSAGE"

echo "7. 推送到GitHub..."
git push origin main

if [ $? -eq 0 ]; then
    echo ""
    echo "🎉 代码推送成功！"
    echo "========================================"
    echo "项目已推送到GitHub:"
    echo "https://github.com/${REPO_OWNER}/${REPO_NAME}/tree/main/${PROJECT_NAME}"
    echo ""
    echo "📁 项目包含:"
    echo "  • 智谱AI注册器 (platforms/zhipu/registrar.py)"
    echo "  • 多平台插件架构"
    echo "  • 智能额度监控系统"
    echo "  • OpenClaw集成方案"
    echo "  • 完整项目文档"
    echo ""
    echo "🚀 下一步:"
    echo "  1. 测试智谱AI注册流程"
    echo "  2. 完善额度监控模块"
    echo "  3. 集成到OpenClaw定时任务"
else
    echo "❌ 推送失败，请检查网络和权限"
    exit 1
fi