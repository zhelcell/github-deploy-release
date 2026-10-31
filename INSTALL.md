# 安装

## 方式一：一键装进 ALITA（推荐）

在 ALITA 里对助手说：

```
装技能 https://github.com/zhelcell/github-deploy-release
```

或用技能商城编号：

```
install_skill_from_registry
```

装完直接说"帮我把这个项目发到 GitHub"就会触发。

## 方式二：手动克隆

```bash
git clone https://github.com/zhelcell/github-deploy-release.git
cd github-deploy-release
```

## 方式三：只要那一个发布脚本

```bash
git clone --depth 1 https://github.com/zhelcell/github-deploy-release.git
python github-deploy-release/scripts/publish.py --help
```

## 前置条件

只有一个：**装了 Git**。脚本本身只用 Python 标准库，不需要 pip install 任何东西。

```bash
git --version   # 应该有版本号
python --version  # 3.8 以上
```

认证不需要手动配置——脚本会按顺序自动找：

| 优先级 | 来源 | 怎么来的 |
|---|---|---|
| 1 | `GITHUB_TOKEN` / `GH_TOKEN` 环境变量 | 你自己设的 |
| 2 | GitHub CLI 已登录 | 装过 gh 并 `gh auth login` 过 |
| 3 | 系统凭据管理器里已存的账号 | 平时用 GitHub Desktop / VS Code 登录过就有 |
| 4 | 都没有 | 脚本会告诉你怎么办 |

**第 3 条是最省事的**：很多人电脑上早就存了 GitHub 账号，只是不知道 `git push` 会直接用它。

## 首次使用

```bash
# 先看看会提交什么（不建仓、不推送）
python scripts/publish.py --dir /path/to/your/project --dry-run

# 满意了再真发
python scripts/publish.py --dir /path/to/your/project --name my-project --yes
```

## 常用参数

| 参数 | 作用 |
|---|---|
| `--dir` | 本地项目目录（必填） |
| `--name` | 远程仓库名，默认取目录名 |
| `--private` | 建私有仓库 |
| `--yes` | 不询问，直接执行（适合脚本化） |
| `--force` | 仓库已存在时继续用 |
| `--dry-run` | **只做本地预检**，不建仓不推送 |
| `--description` | 仓库描述 |
| `--topics` | 仓库标签，逗号分隔 |

## 卸载

删掉技能文件夹即可，不留下任何系统级改动。

## 常见问题

**Q：会不会把我的密钥传上去？**
A：脚本在提交前会扫一遍 `.env`、`*.pem`、`*.key`、`id_rsa`、`credentials.json` 等模式，命中就停下来并列出清单，不会推。有问题也可以自己加 `--dry-run` 先看。

**Q：仓库已经存在了怎么办？**
A：默认会复用已有仓库并推上去；想强制覆盖行为可以加 `--force`。

**Q：能推到已有仓库吗？**
A：能。脚本会覆盖 origin 的地址，`--name` 填目标仓库名，`--force` 允许复用。

**Q：能不能推到 GitLab / Gitee？**
A：目前只支持 GitHub。改起来不难——`api()` 和 clone_url 那两处换掉即可，但认证降级链是 GitHub 专用的。
