# github-deploy-release

一键把本地项目发布成 GitHub 仓库并推送。跨平台（Windows / macOS / Linux），只用 Python 标准库，不需要 `pip install` 任何东西。

## 它替你做了什么

一条命令走完这一串事：

1. 初始化本地 Git 仓库（分支 `main`）
2. 自动补 `.gitignore`（拦住 `.env`、私钥、大文件）
3. **提交前预检**：扫 `.env`、`*.pem`、`*.key`、凭据文件、超大文件，有就停下不推
4. 设置提交身份（用你的 GitHub 账号，不用手填）
5. 创建仓库（公开/私有可选），同时写入仓库描述与 Topics
6. 关联远程并推送
7. 回读校验：比对本地 HEAD 与远程 `main` 的 SHA，不一致会明确报警

## 快速开始

```bash
# 先干跑一遍：只做本地检查，不建仓不推送
python scripts/publish.py --dir /path/to/your/project --dry-run

# 确认没问题再真发
python scripts/publish.py --dir /path/to/your/project --name my-project
```

`--dry-run` 不需要任何 GitHub 凭据，也不碰网络上的任何东西。

## 常用参数

| 参数 | 作用 |
|---|---|
| `--dir PATH` | 要发布的项目目录（必填） |
| `--name NAME` | 仓库名，默认取目录名 |
| `--private` | 建为私有仓库（默认公开） |
| `--description TEXT` | 仓库描述 |
| `--topics a,b,c` | 仓库 Topics，逗号分隔 |
| `--force` | 仓库已存在也继续 |
| `--yes` | 不再询问，直接执行 |
| `--dry-run` | 只做本地检查与推演，不建仓不推送 |

## 前置条件

- Python 3.8+
- Git（https://git-scm.com/downloads）
- 一种 GitHub 认证方式（脚本会自动探测，见下）

## 认证

脚本按下面顺序自动找凭据，**你不用手抄 Token**：

1. 环境变量 `GITHUB_TOKEN` / `GH_TOKEN`
2. GitHub CLI 已登录（`gh auth login`）
3. 系统凭据管理器里已存的 GitHub 账号（Git Credential Manager / osxkeychain / libsecret）——如果你平时用 GitHub Desktop 或 VS Code 登录过，通常这里就有了
4. 都没有 → 提示你走浏览器登录

第 3 条是最省事的：登录过客户端就直接能推。

## 单独拿脚本

只要 `scripts/publish.py` 一个文件也行，它不依赖本仓库其他内容：

```bash
git clone --depth 1 https://github.com/zhelcell/github-deploy-release.git
# 或直接下载 scripts/publish.py
```

## 装成 ALITA 技能

在 ALITA 里说：

```
装技能 https://github.com/zhelcell/github-deploy-release
```

详细说明见 [INSTALL.md](INSTALL.md)。

## 自检

仓库自带 GitHub Actions 工作流（`.github/workflows/self-check.yml`），每次 push 自动跑：语法检查、示例运行、dry-run、无个人痕迹扫描、`.gitignore` 覆盖检查、`skill.json` 合法性。

本地也可以自己跑：

```bash
python -m py_compile scripts/publish.py
python scripts/publish.py --dir examples/hello-project --dry-run
```

## 目录结构

```
scripts/publish.py       主脚本
skill.json               技能元数据
INSTALL.md               安装说明（ALITA / git clone / 单文件）
references/
  gitignore-templates.md 各类项目的 .gitignore 模板
  publishing-checklist.md 发布前检查清单
  troubleshooting.md      常见问题与对策
examples/hello-project/  可直接跑通的最小示例
.github/workflows/       CI 自检
```

## 许可

MIT，见 [LICENSE](LICENSE)。
