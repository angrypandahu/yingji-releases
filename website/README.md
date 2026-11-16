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

专用账号为 `yingji-deploy`。Actions 校验 `ecs_known_hosts` 中从可信 ECS 会话取得的服务器公钥；私钥只保存在 GitHub Actions secret 与发布机受限目录。

把本目录的 `deploy-ecs.sh` 安装为 root 管理的 `/usr/local/bin/deploy-yingji-website`（0755）。为专用账号配置以下两处，公钥替换为实际部署公钥。

```text
# ~yingji-deploy/.ssh/authorized_keys
restrict,command="sudo -n /usr/local/bin/deploy-yingji-website" ssh-ed25519 <部署公钥>

# /etc/sudoers.d/yingji-website
yingji-deploy ALL=(root) NOPASSWD: /usr/local/bin/deploy-yingji-website ""
```

部署命令从标准输入读取当前页面的 SHA-256，从公开仓库 main 取回对应页面，校验后原子替换。ECS 在本机检查站点返回的完整页面摘要；失败时恢复上一份页面。最近一次部署前的页面保存在 `/var/backups/yingji-website/index.previous.html`。
