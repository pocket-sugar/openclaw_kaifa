# 教OpenClaw使用GitHub技能

## 🎯 目标
教会[SERVER_IP]服务器上的OpenClaw实例使用GitHub技能，帮你自动化GitHub操作。

## 📋 当前状态检查
OpenClaw已经具备：
- ✅ Git已安装
- ✅ GitHub CLI (gh) 已安装
- ✅ Python环境就绪
- ✅ 工作目录就绪

## 🔧 需要你提供的

### 1. GitHub个人访问令牌（PAT）
**这是必须的，只有你能提供：**

1. 访问 https://github.com/settings/tokens
2. 点击 "Generate new token (classic)"
3. **必须选择的权限：**
   - `repo` (完全控制仓库)
   - `workflow` (工作流)
4. 生成令牌并**复制保存**（只显示一次）

**令牌格式：** `ghp_xxxxxxxxxxxxxxxxxxxx`

## 🚀 配置步骤（你告诉OpenClaw执行）

### 第一步：GitHub认证
**你对OpenClaw说：**
```
"OpenClaw，配置GitHub认证，这是我的令牌：ghp_你的令牌"
```

**OpenClaw会执行：**
```bash
# 使用令牌登录GitHub
echo "ghp_你的令牌" | gh auth login --with-token

# 验证登录
gh auth status
```

### 第二步：克隆你的仓库
**你对OpenClaw说：**
```
"OpenClaw，克隆我的GitHub仓库"
```

**OpenClaw会执行：**
```bash
# 克隆你的主仓库
gh repo clone pocket-sugar/projects_openclaw /root/.openclaw/workspace/projects_openclaw

# 进入仓库目录
cd /root/.openclaw/workspace/projects_openclaw
```

### 第三步：配置Git
**OpenClaw自动执行：**
```bash
# 设置Git用户信息
git config --global user.name "OpenClaw Assistant"
git config --global user.email "assistant@openclaw.ai"
git config --global init.defaultBranch main
```

## 🎮 GitHub技能使用

### 技能脚本位置
- `/root/.openclaw/workspace/github_skill.sh` - 主技能脚本
- `/root/.openclaw/workspace/configure_github.py` - 配置脚本

### 基本命令
在OpenClaw对话中，你可以说：

#### 1. 提交更改
```
"提交增强记忆系统更新"
```
→ OpenClaw执行：`./github_skill.sh commit "添加增强记忆系统：实体识别、冲突检测"`

#### 2. 推送更改
```
"推送今天的更新"
```
→ OpenClaw执行：`./github_skill.sh push`

#### 3. 创建PR
```
"创建PR：优化配置"
```
→ OpenClaw执行：`./github_skill.sh pr "优化配置" "改进了compaction配置，解决长上下文问题"`

#### 4. 同步仓库
```
"同步GitHub仓库"
```
→ OpenClaw执行：`./github_skill.sh pull`

## 🔄 实际工作流示例

### 场景：开发增强记忆系统后
```
你: "提交增强记忆系统"
OpenClaw: 
  1. 执行: ./github_skill.sh commit "部署增强记忆系统：解决长上下文和任务混淆问题"
  2. 执行: ./github_skill.sh push
  3. 执行: ./github_skill.sh pr "增强记忆系统" "添加知识图谱功能，防止任务A/B混淆"
  4. 回复: "✅ 已提交、推送并创建PR"
```

### 场景：定期备份配置
```
你: "备份OpenClaw配置"
OpenClaw:
  1. 复制: cp /root/.openclaw/openclaw.json projects_openclaw/config_backup/
  2. 执行: ./github_skill.sh commit "备份OpenClaw配置文件"
  3. 执行: ./github_skill.sh push
  4. 回复: "✅ 配置已备份到GitHub"
```

## 📁 项目结构管理

### 你的仓库规则：
- 主仓库：`pocket-sugar/projects_openclaw`
- 每个项目在独立子目录中
- 示例：`cs2026-03-19/` (今天的项目)

### OpenClaw可以帮你：
```bash
# 创建新项目目录
mkdir -p projects_openclaw/cs2026-03-19

# 初始化项目
cd projects_openclaw/cs2026-03-19
echo "# 项目 $(date)" > README.md

# 提交新项目
cd ..
./github_skill.sh commit "添加新项目：cs2026-03-19"
./github_skill.sh push
```

## 🛡️ 安全注意事项

### 1. 令牌安全
- OpenClaw不会保存你的令牌明文
- 令牌通过`gh auth login`认证后，gh CLI会安全存储
- 建议定期轮换令牌

### 2. 操作确认
重要操作前，OpenClaw可以询问确认：
```
你: "删除旧配置文件"
OpenClaw: "确认删除 config/old_config.json？[y/N]"
你: "y"
OpenClaw: 执行删除并提交
```

### 3. 备份策略
- 重要更改前自动创建备份分支
- 使用标签标记重要版本
- 定期同步到GitHub

## 🚨 故障排除

### 问题：认证失败
**解决：**
```
你: "重新认证GitHub，新令牌：ghp_新令牌"
OpenClaw: 
  gh auth logout
  echo "新令牌" | gh auth login --with-token
```

### 问题：仓库不存在
**解决：**
```
你: "初始化GitHub仓库"
OpenClaw: ./github_skill.sh init
```

### 问题：权限不足
**解决：**
- 检查令牌是否有`repo`权限
- 重新生成令牌
- 重新认证

## 📈 高级功能

### 1. 自动化Issue跟踪
```
你: "创建Issue：优化长上下文处理"
OpenClaw: 
  gh issue create --title "优化长上下文处理" --body "需要改进compaction配置"
```

### 2. 工作流触发
```
你: "运行CI测试"
OpenClaw:
  gh workflow run "CI" --ref main
```

### 3. 仓库统计
```
你: "查看仓库状态"
OpenClaw:
  gh repo view --json "name,stargazerCount,forkCount"
```

## 🎉 开始使用

### 快速启动命令：
```
你对OpenClaw说：
1. "配置GitHub技能，令牌：ghp_你的令牌"
2. "初始化仓库"
3. "提交增强记忆系统"
```

### 验证配置：
```bash
# OpenClaw可以运行验证
gh auth status
git status
gh repo view pocket-sugar/projects_openclaw
```

## 💡 使用技巧

### 1. 自然语言命令
你可以用自然语言，OpenClaw会理解：
- "把今天的更新提交到GitHub"
- "给增强记忆系统创建PR"
- "同步一下仓库"

### 2. 定期任务
设置定时任务自动同步：
```bash
# 每天凌晨3点同步
0 3 * * * cd /root/.openclaw/workspace/projects_openclaw && ./github_skill.sh pull && ./github_skill.sh push
```

### 3. 项目模板
创建标准项目结构：
```bash
# OpenClaw可以自动创建
mkdir -p {src,tests,docs,config}
touch README.md .gitignore requirements.txt
```

---

## 📞 总结

**现在OpenClaw已经准备好使用GitHub技能了！**

### 你只需要：
1. 提供GitHub PAT令牌
2. 告诉OpenClaw开始配置

### OpenClaw会：
1. 自动认证GitHub
2. 克隆你的仓库
3. 配置Git设置
4. 准备好所有技能脚本

### 然后你可以：
- ✅ 提交代码更新
- ✅ 管理PR和Issues
- ✅ 同步仓库
- ✅ 自动化GitHub工作流

**开始对OpenClaw说：**
```
"配置GitHub技能，这是我的令牌：ghp_xxxxxxxxxxxxxxxxxxxx"
```

**OpenClaw就会开始工作，帮你自动化所有GitHub操作！**