# 官网源码

线上地址：<https://jingshenkeji.cn/>；安装包和演示图存放在阿里云 OSS：<https://yj.jingshenkeji.cn/>。

## 本地构建

```bash
python3 website/build.py --check
```

`site.json` 保存版本、下载包、演示图和校验值；`template.html` 通过 `{{version}}`、`{{download_url}}` 等占位符读取配置。

## 发版

1. 发布 GitHub Release，并上传 Mac DMG。
2. 把同名 DMG 和需要更新的演示图上传到 OSS 根目录。
3. 在 Actions 里确认 `Website release`：它会校验 OSS 文件、更新 `site.json` / `index.html`、提交到 `main`，并部署到 ECS。

## 一次性准备

在 GitHub 仓库 Settings → Secrets and variables → Actions 配置：

- `YINGJI_ECS_HOST`
- `YINGJI_ECS_USER`
- `YINGJI_ECS_SSH_KEY`
- `YINGJI_ECS_PORT`

ECS 准备：

```sh
useradd --create-home --shell /bin/sh yingji-deploy
install --directory --owner yingji-deploy /opt/yingji-releases
runuser -u yingji-deploy -- git clone https://github.com/angrypandahu/yingji-releases.git /opt/yingji-releases
```

部署脚本内容：

```sh
#!/bin/sh
set -eu
cd /opt/yingji-releases
git fetch origin main
git reset --hard origin/main
install -m 0644 website/index.html /clouddream/yingji-website/index.html
curl --fail --silent --show-error --max-time 30 http://127.0.0.1:18090/ >/dev/null
```

`sudo` 配置：

```text
yingji-deploy ALL=(root) NOPASSWD: /usr/local/bin/deploy-yingji-website
```
