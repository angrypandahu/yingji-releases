# 官网源码

线上地址：<https://jingshenkeji.cn/>；安装包和演示图存放在阿里云 OSS：<https://yj.jingshenkeji.cn/>。

## 本地构建

```bash
python3 website/build.py --check
```

`site.json` 保存版本、下载包、演示图和校验值；`template.html` 通过 `{{version}}`、`{{download_url}}` 等占位符读取配置。

## 发版

1. 将本次平台的正式安装包上传到上海 OSS 根目录，并将同一份文件附到对应的 GitHub 稳定 Release。文件名为 `Yingji-X.Y.Z-macOS-arm64.dmg` 或 `Yingji-X.Y.Z-Windows-x64.exe`。
2. 发布 Release 会触发 `Website release`。工作流从 OSS 读取本次安装包，比对 Release 附件的字节数和 SHA-256，分别记录两个平台的版本和发行说明。单平台发版会保留另一平台已开放的版本。Windows 下载按钮只在 OSS 对象可匿名访问时显示。
3. 如发布时 Windows EXE 尚未上传到 OSS，上传完成后在 Actions 手动运行 **Website release**，选择 `main` 并输入 Windows 包所属的 Release 标签。给已公开的 Release 补传附件也需要这样重跑。随后检查 Deploy 步骤及两个官网域名的下载按钮。

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
