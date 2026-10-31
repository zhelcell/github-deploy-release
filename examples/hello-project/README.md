# hello-project

`github-deploy-release` 技能用的最小示例项目。

## 跑起来

```bash
python hello.py
# -> hello from github-deploy-release
```

## 用这个技能发布它

```bash
python scripts/publish.py --dir examples/hello-project --name my-hello-project --yes
```

推完后去 `https://github.com/<your-user>/my-hello-project` 看结果。

## 这个示例演示了什么

- 一个干净的目录如何变成 GitHub 仓库
- `.gitignore` 排除 `__pycache__/` 等噪音
- 推送后必须回读验证（SHA 一致 + 文件能取回）
