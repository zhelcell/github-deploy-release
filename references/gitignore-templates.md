# .gitignore 模板

按语言选一份再删减。**不要照抄不需要的行**——多余的规则会让人以为某些文件没被跟踪。

## Python

```gitignore
__pycache__/
*.py[cod]
*$py.class
*.so
build/
dist/
*.egg-info/
.venv/
venv/
.pytest_cache/
.mypy_cache/
.ruff_cache/
.coverage
htmlcov/
```

## Node.js

```gitignore
node_modules/
npm-debug.log*
yarn-error.log*
dist/
build/
.next/
.nuxt/
.cache/
coverage/
*.tsbuildinfo
.env
.env.local
```

## 通用

```gitignore
*.log
.DS_Store
Thumbs.db
.idea/
.vscode/
*.swp
```

## Rust

```gitignore
/target/
**/*.rs.bk
```

## Go

```gitignore
*.exe
*.dll
*.so
bin/
vendor/
```

## Java / Gradle

```gitignore
*.class
*.jar
.gradle/
build/
out/
target/
```

## 密钥（任何项目都必须加）

```gitignore
.env
.env.*
!.env.example
*.pem
*.key
id_rsa
id_rsa.pub
*.p12
*.pfx
secrets.json
credentials.json
```

`!.env.example` 这行别漏——要提交模板就别提交真值。

## 验证忽略规则是否生效

```bash
git check-ignore -v <路径>      # 显示哪一行规则命中
git status --short              # 确认敏感文件没在待提交列表
git ls-files | grep -iE '\.env|\.pem|id_rsa'   # 已跟踪文件里不该有这些
```

## 补救：加错了怎么回退

已经提交过才改 `.gitignore` 不够——历史里还在，且 `git rm --cached` 只影响之后的提交：

```bash
git rm -r --cached <路径>
git commit -m "chore: stop tracking <路径>"
```

**如果这个文件是密钥，直接去 GitHub 后台吊销重置**，再谈清理历史。清理历史（`git filter-repo`）会改写所有 commit SHA，协作项目慎用。
