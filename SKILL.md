---
name: github-deploy-release
author: 李东泽
description: 把本地项目一键发布到 GitHub 的完整流程助手——自动初始化 git 仓库、生成 .gitignore、提交前扫描敏感文件（.env/私钥/大文件）、创建远程仓库、推送分支，并在推送后回读校验本地与远端 SHA 是否一致。认证四级自动降级（环境变量 → GitHub CLI → 系统凭据管理器 → 浏览器登录），用户无需手动抄写 Token。怎么用：把项目目录交给本技能，或直接运行 python scripts/publish.py --dir <项目目录> --name <仓库名>，先加 --dry-run 只做本地预检不外发，确认无误后去掉即可真正建仓推送。当用户说“发到 GitHub”“把这个项目开源”“上传到仓库”“发布到 GitHub”“建个仓库”“把代码传上去”“帮我推送代码”时触发。
---

# GitHub 部署发布

一步步把一个本地目录变成 GitHub 上一个可访问的远程仓库，并且**验证真的推上去了**。

## 什么时候用

- "帮我把这个项目发到 GitHub"
- "开个仓库，把代码传上去"
- "这个脚本怎么开源给别人用"
- 已有本地 git 仓库，只想推上去
- "把这个目录做成公开仓库"

## 安装（给第一次用的人）

前置只要两个：**装了 Git** 和 **Python 3.8+**。脚本只用标准库，不需要 pip install。

```bash
git --version
python --version
```

装进 ALITA（推荐，在对话里对助手说）：

```
装技能 https://github.com/zhelcell/github-deploy-release
```

手动克隆：

```bash
git clone https://github.com/zhelcell/github-deploy-release.git
```

只想拿走那个发布脚本：

```bash
git clone --depth 1 https://github.com/zhelcell/github-deploy-release.git
python github-deploy-release/scripts/publish.py --help
```

完整说明见 `INSTALL.md`。**认证不需要手动配置**——脚本会依次尝试环境变量 → GitHub CLI → 系统凭据管理器；多数人电脑上早就存了 GitHub 账号，直接就能用。

## 铁律

1. **先看目录，再动手。** 推之前必须确认：哪些文件要传、哪些要排除。密钥、`.env`、`node_modules`、构建产物绝不进仓库。
2. **推完必须回读验证。** 不能只看 `git push` 返回 0 就宣布成功。要比对本地 HEAD 与远程 SHA、确认远程文件列表、抽一个文件走 API 取回。
3. **认证不让用户抄 Token。** 按顺序自动降级，全失败才让用户登录。
4. **不外发未经确认的内容。** 仓库设为 public 前问一句；删除远程仓库、force push 这类不可逆动作必须先确认。

## 流程

### 第 0 步：看目录

```bash
ls -la <项目目录>
```

判断三件事：

- 有没有 `.git`（已初始化就跳到第 3 步）
- 有没有敏感文件（`.env`、密钥、`credentials`）
- 有没有大文件（>50MB 会被 GitHub 拒绝）

### 第 1 步：初始化

```bash
git init
git branch -M main
```

### 第 2 步：配置 .gitignore

最容易漏、也最容易出事的一步。先扫敏感文件：

```bash
find <项目目录> -name ".env*" -o -name "id_rsa*"
```

模板见 `references/gitignore-templates.md`。

### 第 3 步：首次提交

```bash
git add .
git status                 # 确认暂存区里没有 .env / 密钥 / node_modules
git commit -m "chore: initial commit"
```

提交前一定要 `git status` 看一眼——暂存区里的每个文件都会变成公开资产。

### 第 4 步：认证（自动降级）

1. 环境变量 `GITHUB_TOKEN` / `GH_TOKEN`
2. GitHub CLI 已登录 → `gh auth status`
3. 系统凭据管理器里已存的账号 → Git Credential Manager(Windows) / osxkeychain(mac) / libsecret(Linux)
4. 全没有 → 引导用户走浏览器设备码登录

`scripts/publish.py` 已经把这四级全实现好，**优先直接调它**。

### 第 5 步：建仓 + 推送 + 验证

```bash
python scripts/publish.py --dir <项目目录> --name <仓库名> [--private] [--yes]
```

参数：

| 参数 | 含义 |
|---|---|
| `--dir` | 本地项目目录（必填） |
| `--name` | 远程仓库名（必填） |
| `--private` | 建私有仓库；不加则公开 |
| `--yes` | 跳过交互确认（用于无人值守场景） |
| `--force` | 仓库已存在时继续用，不报错退出 |

### 第 6 步：回读验证（不可省）

```bash
git rev-parse HEAD
git ls-remote origin refs/heads/main    # 两行 SHA 必须一致
curl -s -o /dev/null -w "%{http_code}" https://raw.githubusercontent.com/<user>/<repo>/main/README.md
```

三个都过，才算发布成功。`publish.py` 已内置这三项校验。

## 常见坑

| 现象 | 原因 | 解法 |
|---|---|---|
| push 提示 could not read Username | 没有可用凭据 | 走第 4 步降级链，别让用户手抄 Token |
| push 成功但仓库里没文件 | 推的是别的分支 | `git branch -vv` 确认上游对应关系 |
| 提示建 PR 但仓库空 | 空提交或 .gitignore 排除了全部文件 | `git ls-files` 看实际跟踪数 |
| HTTP 413 / file too large | 文件超 100MB | Git LFS 或排除该文件 |
| 仓库泄露了密钥 | .gitignore 加晚了 | 密钥必须重置，改 .gitignore 不够 |
| 推了但本地没记上游 | 没用 `-u` | `git push -u origin main` |

密钥泄漏是唯一"必须重置"级别的错误，其他都能补救。

## 想给别人用时

仓库里不能有发布者自己的信息：

- `skill.json` 不带人名
- `SKILL.md` 不写死绝对路径
- 示例用 `<your-repo>` 占位
- 脚本里不留任何个人 Token
- 不在文档里出现本机用户名（如 `C:\Users\<你的名字>\...`）

## 参考资料

- `references/gitignore-templates.md` — 各语言 .gitignore 模板 + 验证方法
- `references/troubleshooting.md` — 认证、仓库空、分支错、大文件等排查手册
- `references/publishing-checklist.md` — 发布前自检清单
- `examples/hello-project/` — 最小可跑示例
