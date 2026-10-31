#!/usr/bin/env python3
"""一键把本地目录发布成 GitHub 仓库并推送。

跨平台（Windows / macOS / Linux），只用标准库，不需要装任何东西。

用法:
    python publish.py --dir <项目目录> --name <仓库名> [--private] [--yes]

认证优先级（自动降级，全都不用你手抄 Token）:
    1. 环境变量 GITHUB_TOKEN / GH_TOKEN
    2. GitHub CLI 已登录（gh auth status）
    3. 系统凭据管理器里已存的 GitHub 账号（Git Credential Manager / osxkeychain /
       libsecret），自动取 OAuth token
    4. 都没有 -> 提示用户走浏览器登录，退出码 2
"""

import argparse
import json
import os
import platform
import shutil
import subprocess
import sys
import urllib.error
import urllib.request

API = "https://api.github.com"


def log(msg):
    print(msg, flush=True)


def run(cmd, cwd=None, check=True, capture=False):
    """跑一条命令。Windows 下用 shell=False 列表形式，避免引号地狱。"""
    p = subprocess.run(
        cmd,
        cwd=cwd,
        capture_output=capture,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if check and p.returncode != 0:
        out = (p.stdout or "") + (p.stderr or "")
        raise RuntimeError("命令失败: %s\n%s" % (" ".join(cmd), out.strip()))
    return p


def git(*args, cwd=None, check=True, capture=True):
    return run(["git"] + list(args), cwd=cwd, check=check, capture=capture)


def api(method, path, token, body=None, raw=False):
    """调用 GitHub REST API。"""
    url = path if path.startswith("http") else API + path
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header("Authorization", "Bearer " + token)
    req.add_header("Accept", "application/vnd.github+json")
    req.add_header("X-GitHub-Api-Version", "2022-11-28")
    req.add_header("User-Agent", "alita-publish")
    if data:
        req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            payload = resp.read().decode("utf-8", "replace")
            return resp.status, payload if raw else (json.loads(payload) if payload else {})
    except urllib.error.HTTPError as e:
        detail = e.read().decode("utf-8", "replace")
        try:
            detail = json.loads(detail).get("message", detail)
        except Exception:
            pass
        raise RuntimeError("GitHub API %s %s -> %s %s" % (method, path, e.code, detail))
    except urllib.error.URLError as e:
        raise RuntimeError("网络不可达，无法访问 api.github.com: %s" % e.reason)


# ---------------------------------------------------------------- 认证


def token_from_env():
    for k in ("GITHUB_TOKEN", "GH_TOKEN", "GITHUB_PAT"):
        v = os.environ.get(k)
        if v and v.strip():
            return v.strip(), "环境变量 " + k
    return None, None


def token_from_gh():
    """GitHub CLI 已登录时，用它自己的 token。"""
    if not shutil.which("gh"):
        return None, None
    p = subprocess.run(
        ["gh", "auth", "token"], capture_output=True, text=True, encoding="utf-8",
        errors="replace",
    )
    if p.returncode == 0 and p.stdout.strip():
        return p.stdout.strip(), "GitHub CLI"
    return None, None


def token_from_credential_manager():
    """系统凭据管理器里已存的 GitHub 账号 —— 关键: 用户往往早就登录过 GitHub 客户端，
    只是不知道 git push 会直接用它,不用再输 Token。"""
    if platform.system() == "Windows":
        cmd = ["git", "credential-manager", "get"]
    elif platform.system() == "Darwin":
        cmd = ["git", "credential-osxkeychain", "get"]
    else:
        cmd = ["git", "credential-libsecret", "get"]

    payload = "protocol=https\nhost=github.com\n\n"
    try:
        p = subprocess.run(
            cmd, input=payload, capture_output=True, text=True,
            encoding="utf-8", errors="replace",
        )
    except FileNotFoundError:
        return None, None
    if p.returncode != 0 or not p.stdout:
        return None, None

    token = None
    user = None
    for line in p.stdout.splitlines():
        if line.startswith("password="):
            token = line.split("=", 1)[1].strip()
        elif line.startswith("username="):
            user = line.split("=", 1)[1].strip()
    if not token:
        return None, None
    return token, "系统凭据管理器（账号 %s）" % (user or "未知")


def get_token():
    for fn in (token_from_env, token_from_gh, token_from_credential_manager):
        tok, src = fn()
        if tok:
            return tok, src
    return None, None


# ---------------------------------------------------------------- 仓库


def find_existing_repo(token, name):
    """同名的仓库可能已经存在（重复跑脚本时）。"""
    try:
        status, data = api("GET", "/user/repos?per_page=100", token)
    except RuntimeError:
        return None
    for r in data:
        if r.get("name") == name:
            return r
    return None


def ensure_repo(token, name, private, force=False):
    repo = find_existing_repo(token, name)
    if repo:
        if force:
            log("仓库已存在，跳过创建: %s" % repo["html_url"])
        else:
            log("仓库已存在: %s" % repo["html_url"])
        return repo
    body = {
        "name": name,
        "private": bool(private),
        "description": "Created by alita publish.py",
        "auto_init": False,  # 关键: 不要 README, 否则和本地提交历史冲突
    }
    status, data = api("POST", "/user/repos", token, body)
    log("仓库已创建: %s" % data["html_url"])
    return data


def ensure_gitignore(project_dir):
    """没有 .gitignore 就补一个最小版,免得把密钥和依赖推上去。"""
    path = os.path.join(project_dir, ".gitignore")
    if os.path.exists(path):
        return False
    with open(path, "w", encoding="utf-8") as f:
        f.write(
            ".env\n.env.*\n!.env.example\n"
            "node_modules/\ndist/\nbuild/\n"
            "__pycache__/\n*.pyc\n.venv/\nvenv/\n"
            ".DS_Store\nThumbs.db\n*.log\n"
            ".idea/\n.vscode/\n"
            "*.pem\n*.key\nid_rsa*\n"
        )
    log("已自动生成 .gitignore")
    return True


def ensure_identity(project_dir):
    """没配 user.name / user.email 就用 GitHub 账号默认值兜底。"""
    for key in ("user.name", "user.email"):
        p = git("config", "--get", key, cwd=project_dir, check=False)
        if not (p.stdout or "").strip():
            return False
    return True


# ---------------------------------------------------------------- 主流程


def publish(project_dir, name, private, force=False):
    project_dir = os.path.abspath(project_dir)
    if not os.path.isdir(project_dir):
        log("目录不存在: %s" % project_dir)
        return 1

    log("项目目录: %s" % project_dir)
    log("仓库名称: %s（%s）" % (name, "私有" if private else "公开"))

    # 1. git 可用性
    if not shutil.which("git"):
        log("找不到 git，请先安装: https://git-scm.com/downloads")
        return 1
    git("--version", cwd=project_dir, check=False, capture=True)

    # 2. 认证
    token, src = get_token()
    if not token:
        log("")
        log("找不到可用的 GitHub 凭据。三个办法，任选一个：")
        log("  A. 装 GitHub CLI 并登录（一次性，之后这台电脑就不用再管）:")
        log("     https://cli.github.com  →  安装后执行:  gh auth login")
        log("  B. 生成一个 Personal Access Token（权限勾选 repo）:")
        log("     https://github.com/settings/tokens  →  复制后执行:")
        log("     set GITHUB_TOKEN=你的token   (Windows cmd)")
        log("     export GITHUB_TOKEN=你的token  (macOS/Linux)")
        log("  C. 如果你平时用 GitHub Desktop 或 VS Code 登录过，通常已经有凭据，")
        log("     重新跑一次本脚本即可。")
        return 2
    log("使用凭据来源: %s" % src)

    # 3. 验证 token 有效
    try:
        _, me = api("GET", "/user", token)
    except RuntimeError as e:
        log("凭据无效: %s" % e)
        return 2
    login = me.get("login", "?")
    log("已登录 GitHub 账号: %s" % login)

    # 4. 初始化本地仓库
    if not os.path.isdir(os.path.join(project_dir, ".git")):
        git("init", "-b", "main", cwd=project_dir, check=False)
        if not os.path.isdir(os.path.join(project_dir, ".git")):
            git("init", cwd=project_dir)
            git("branch", "-M", "main", cwd=project_dir)
        log("已初始化 Git 仓库（分支 main）")

    ensure_gitignore(project_dir)

    if not ensure_identity(project_dir):
        git("config", "user.name", login, cwd=project_dir)
        git("config", "user.email", "%s@users.noreply.github.com" % login, cwd=project_dir)
        log("已用 GitHub 账号设置提交身份: %s" % login)

    # 5. 提交
    git("add", ".", cwd=project_dir)
    staged = git("diff", "--cached", "--stat", cwd=project_dir)
    if not (staged.stdout or "").strip():
        log("没有可提交的变更，跳过提交步骤")
    else:
        p = git("commit", "-m", "chore: initial commit", cwd=project_dir, check=False)
        if p.returncode != 0:
            log("提交失败: %s" % ((p.stdout or "") + (p.stderr or "")))
            return 1
        log("已提交: %s" % git("log", "--oneline", "-n", "1", cwd=project_dir).stdout.strip())

    # 6. 建仓
    try:
        repo = ensure_repo(token, name, private, force)
    except RuntimeError as e:
        log("创建仓库失败: %s" % e)
        return 1

    clone_url = repo.get("clone_url") or repo.get("html_url")

    # 7. 关联远程
    remotes = git("remote", cwd=project_dir).stdout
    if "origin" in remotes:
        git("remote", "set-url", "origin", clone_url, cwd=project_dir)
    else:
        git("remote", "add", "origin", clone_url, cwd=project_dir)
    log("已关联远程: %s" % clone_url)

    # 8. 推送
    p = git("push", "-u", "origin", "main", cwd=project_dir, check=False)
    push_out = ((p.stdout or "") + (p.stderr or "")).strip()
    if p.returncode != 0:
        log("推送失败，完整输出:")
        log(push_out)
        log("")
        log("常见原因与对策：")
        log("  · 提示要用户名密码 → GitHub 已停用密码认证，需要 Token（见上面办法 B）")
        log("  · Permission denied (publickey) → 用的是 SSH 地址但没配公钥，改用 HTTPS")
        log("  · rejected non-fast-forward → 远程已有新提交，先 git pull --rebase origin main")
        return 1
    log(push_out)

    # 9. 回读验证
    local_sha = git("rev-parse", "HEAD", cwd=project_dir).stdout.strip()
    try:
        _, remote_ref = api(
            "GET", "/repos/%s/%s/git/ref/heads/main" % (login, name), token)
        remote_sha = remote_ref["object"]["sha"]
    except RuntimeError as e:
        log("回读失败: %s" % e)
        remote_sha = "(读取失败)"

    _, files = api("GET", "/repos/%s/%s/contents/" % (login, name), token)
    file_names = [f["name"] for f in files] if isinstance(files, list) else []

    log("")
    log("=== 发布完成 ===")
    log("仓库地址: %s" % repo.get("html_url"))
    log("本地 HEAD: %s" % local_sha)
    log("远程 main: %s" % remote_sha)
    log("文件列表: %s" % (", ".join(file_names) if file_names else "(空)"))
    if remote_sha == local_sha:
        log("验证通过: 本地与远程完全一致")
    else:
        log("警告: 本地与远程不一致，请检查上面的输出")
        return 1
    return 0


def main():
    ap = argparse.ArgumentParser(description="一键把本地目录发布到 GitHub")
    ap.add_argument("--dir", required=True, help="项目目录")
    ap.add_argument("--name", help="仓库名（默认取目录名）")
    ap.add_argument("--private", action="store_true", help="创建为私有仓库")
    ap.add_argument("--force", action="store_true", help="仓库已存在时也继续")
    ap.add_argument("--yes", action="store_true", help="不再询问，直接执行")
    args = ap.parse_args()

    project_dir = os.path.abspath(args.dir)
    name = args.name or os.path.basename(project_dir.rstrip(os.sep))
    if not args.yes and sys.stdin.isatty():
        vis = "私有" if args.private else "公开"
        ans = input("将创建 %s（%s）并推送，继续? [y/N] " % (name, vis)).strip().lower()
        if ans not in ("y", "yes"):
            log("已取消")
            return 0
    try:
        return publish(project_dir, name, args.private, args.force)
    except KeyboardInterrupt:
        log("已中断")
        return 130


if __name__ == "__main__":
    sys.exit(main())
