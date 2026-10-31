# 排查手册

## push 报 could not read Username / Authentication failed

按顺序排查凭据来源：

1. `echo %GITHUB_TOKEN%`（PowerShell 用 `$env:GITHUB_TOKEN`）——有值且有效就先用它
2. `gh auth status` —— 登录了就能取 token
3. 系统凭据管理器：
   - Windows: `git credential-manager github list`
   - macOS: `security find-internet-password -s github.com`
   - Linux: `secret-tool lookup service git`

**最容易被忽略的是第 3 条。** 装了 Git for Windows 或 GitHub Desktop 的机器上通常已经存了 GitHub 账号，压根不用重新登录。

`scripts/publish.py` 的认证降级链就是按这个顺序实现的，可直接跑它看它走到哪一级。

## 仓库是空的

```bash
git ls-files                          # 看实际跟踪了几个文件（空 = 全被忽略了）
git check-ignore -v <文件>            # 看是哪条规则排掉它
git status --short                    # 未跟踪的文件用 git add 补上
```

## 推到了错的分支

```bash
git branch -vv                       # 看本地分支的 upstream
git push -u origin main              # 明确推 main 并设上游
```

## 远程有提交，本地推不上去

```bash
git fetch origin
git log --oneline --graph --all -10
git rebase origin/main               # 或 git pull --rebase
```

## 大文件被拒

```bash
git ls-tree -r -l HEAD | sort -k4 -n -r | head -20   # 找最大的几个
```

超过 100MB 必须用 LFS：

```bash
git lfs install
git lfs track "*.psd"
git add .gitattributes
git commit -m "chore: track large files with LFS"
```

## 换了账号推不上去

```bash
git remote -v                                              # 确认 remote 地址
git remote set-url origin https://github.com/<新账号>/<仓库>.git
git credential-manager github list                        # 看存了哪些账号
git credential-manager github logout <旧账号>
```

## 确认远程真的更新了

```bash
git ls-remote origin refs/heads/main                     # SHA 要和 git rev-parse HEAD 一致
curl -s -o /dev/null -w "%{http_code}" https://raw.githubusercontent.com/<user>/<repo>/main/README.md
```

## 建仓接口报 422

多半是仓库名已存在，或名字里有非法字符：

- 只能含字母、数字、连字符、下划线、点
- 不能以连字符开头结尾，不能有连续连字符
- 名字必须和 `owner/name` 里的 name 部分一致

## 私有仓库 curl 取回 404

私有仓库的 raw 地址需要认证，404 是正常的——改用带 token 的 API：

```bash
curl -s -H "Authorization: token $GITHUB_TOKEN" \
  https://api.github.com/repos/<owner>/<repo>/contents/README.md
```

## 推送成功但仓库页看不到文件

检查是不是推到了非默认分支：

```bash
git branch -vv
git remote show origin | grep "HEAD branch"
```

把内容挪到默认分支：`git push origin HEAD:<默认分支>`。
