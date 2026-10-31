# 发布前自检清单

## 内容

- [ ] README.md 存在，说清楚这个项目是干什么的、怎么跑起来
- [ ] LICENSE 文件在（MIT / Apache-2.0 / GPL-3.0）
- [ ] `.gitignore` 已提交，敏感文件确实没被跟踪
- [ ] 没有自己的真实信息：绝对路径、用户名目录、公司名、内网地址
- [ ] 示例里的仓库名用 `<your-repo>` 占位，不是真仓库名
- [ ] 脚本和代码里没有个人 Token、API Key、账号名

## 安全

```bash
# 扫当前跟踪的文件
git ls-files | grep -iE '\.env|\.pem|\.key|secret|credential|token'

# 扫历史（不止当前 HEAD）
git log --all --full-history --name-only | grep -iE '\.env$|\.pem$|id_rsa'

# 看最大的几个文件
git ls-tree -r -l HEAD | sort -k4 -n -r | head -5
```

- [ ] 上面三条都没命中
- [ ] 大文件没混进来（>50MB 会被 GitHub 拒绝，>100MB 必拒）

## 远程

- [ ] 仓库可见性是预期的（public 还是 private）
- [ ] 推送成功且已回读验证（SHA 一致 + 抽一个文件能取回）
- [ ] 仓库描述、Topics 填了，别人能搜到

## 给别人用的时候额外查

- [ ] `skill.json` 里没有写死绝对路径
- [ ] SKILL.md 的描述里没有本机路径
- [ ] 脚本不写死用户目录，路径都用参数传入
- [ ] 文档里没有出现本机用户名
- [ ] 在一台干净的机器上（或新用户环境）跑一遍 `scripts/publish.py` 能通
- [ ] 脚本只依赖 Python 标准库（不需要 pip install 任何东西）

## 验证命令清单（复制即用）

```bash
# 1. 语法与帮助可用
python scripts/publish.py --help

# 2. 认证链路能走通（不实际建仓）
python scripts/publish.py --dir examples/hello-project --name your-repo --dry-run

# 3. 无个人痕迹
grep -rniE "zhelcell|C:\\\\Users|Administrator" . --include="*.md" --include="*.json" --include="*.py"
```
