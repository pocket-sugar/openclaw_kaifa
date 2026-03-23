#!/bin/bash

echo "🚀 GitHub代码提交脚本"
echo "========================"

# 等待GitHub仓库克隆完成
echo "1. 检查GitHub仓库状态..."
if [ ! -d "/root/.openclaw/workspace/projects_openclaw" ]; then
    echo "❌ GitHub仓库尚未克隆完成"
    echo "   请先运行: git clone https://github.com/pocket-sugar/projects_openclaw.git"
    exit 1
fi

cd /root/.openclaw/workspace/projects_openclaw

echo "✅ GitHub仓库已就绪: $(pwd)"

# 2. 创建项目目录
echo "2. 创建项目目录..."
PROJECT_NAME="multi-ai-platform-manager"
PROJECT_DIR="$PROJECT_NAME"

if [ -d "$PROJECT_DIR" ]; then
    echo "⚠️  项目目录已存在: $PROJECT_DIR"
    echo "   备份旧版本..."
    BACKUP_DIR="${PROJECT_DIR}_backup_$(date +%Y%m%d_%H%M%S)"
    mv "$PROJECT_DIR" "$BACKUP_DIR"
    echo "   ✅ 备份完成: $BACKUP_DIR"
fi

mkdir -p "$PROJECT_DIR"
echo "✅ 创建项目目录: $PROJECT_DIR"

# 3. 复制代码文件
echo "3. 复制代码文件..."
SOURCE_DIR="/root/.openclaw/workspace/deepseek-auto-renew"

# 复制Python文件
find "$SOURCE_DIR" -name "*.py" -type f | while read -r file; do
    rel_path="${file#$SOURCE_DIR/}"
    target_path="$PROJECT_DIR/$rel_path"
    mkdir -p "$(dirname "$target_path")"
    cp "$file" "$target_path"
    echo "   📄 $rel_path"
done

# 复制文档文件
find "$SOURCE_DIR" -name "*.md" -type f | while read -r file; do
    rel_path="${file#$SOURCE_DIR/}"
    target_path="$PROJECT_DIR/$rel_path"
    mkdir -p "$(dirname "$target_path")"
    cp "$file" "$target_path"
    echo "   📄 $rel_path"
done

# 复制配置文件
find "$SOURCE_DIR" -name "*.json" -type f | while read -r file; do
    rel_path="${file#$SOURCE_DIR/}"
    target_path="$PROJECT_DIR/$rel_path"
    mkdir -p "$(dirname "$target_path")"
    cp "$file" "$target_path"
    echo "   📄 $rel_path"
done

echo "✅ 代码文件复制完成"

# 4. 创建README
echo "4. 创建项目README..."
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
EOF

echo "✅ README创建完成"

# 5. 创建requirements.txt
echo "5. 创建依赖文件..."
cat > "$PROJECT_DIR/requirements.txt" << 'EOF'
playwright>=1.40.0
aiohttp>=3.9.0
beautifulsoup4>=4.12.0
requests>=2.31.0
pytesseract>=0.3.10
pillow>=10.0.0
python-dotenv>=1.0.0
EOF

echo "✅ 依赖文件创建完成"

# 6. Git操作
echo "6. 提交到GitHub..."
cd /root/.openclaw/workspace/projects_openclaw

# 配置Git用户
git config user.name "OpenClaw Assistant"
git config user.email "assistant@openclaw.ai"

# 添加文件
git add "$PROJECT_DIR"

# 检查状态
echo "Git状态:"
git status --short

# 提交
COMMIT_MESSAGE="feat: 添加Multi-AI Platform Manager项目

- 智谱AI自动化注册器
- 多平台插件架构
- 智能额度监控系统
- 项目文档和配置"

git commit -m "$COMMIT_MESSAGE"

# 推送到GitHub
echo "推送到GitHub..."
git push origin main

echo "🎉 代码提交完成！"
echo "项目已推送到: https://github.com/pocket-sugar/projects_openclaw/tree/main/$PROJECT_NAME"
EOF

chmod +x /root/.openclaw/workspace/commit_to_github.sh
echo "✅ 提交脚本创建完成: /root/.openclaw/workspace/commit_to_github.sh"