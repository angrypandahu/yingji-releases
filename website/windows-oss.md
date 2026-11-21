# 发布 Windows 安装包到 OSS

在 Windows 构建机上打开 PowerShell 7，从本公开发行仓根目录执行。准备通过国内首装验收和 `check:win` 的同一次发行归档，其中包含 EXE、同名 `.exe.blockmap` 和 `build-info.windows-x64.json`。安装 ossutil 2.x，使用有上海桶写入权限的发布机身份。首次配置可在本机运行 `ossutil config`，区域填 `cn-shanghai`。凭据保存在发布机上。[阿里云 ossutil 配置](https://www.alibabacloud.com/help/en/oss/developer-reference/configure-ossutil)

## 上传与验证

将路径替换为实际发行归档。预演只校验本地文件，并列出三个公网地址、字节数和 SHA-256。

```powershell
$archive = Read-Host '输入 Windows 发行归档目录'
.\scripts\upload-windows-oss.ps1 -ArtifactsDir $archive -DryRun
```

核对版本和目标后，执行上传。

```powershell
.\scripts\upload-windows-oss.ps1 -ArtifactsDir $archive
```

脚本上传到上海桶 `jingshenkeji-yingji-releases`。桶根目录的 EXE 供官网下载，`updates/windows-x64/` 里的 EXE 和 blockmap 供应用内更新。脚本对每个对象做匿名完整下载，与构建收据逐项比对。同版本由一位发布人操作，中断后可用同一份归档重跑。已有同名文件会跳过上传，公网摘要冲突会报错并停止。[阿里云 cp 参数](https://www.alibabacloud.com/help/en/oss/developer-reference/cp-upload-file)

## 官网与应用内更新

- **官网**：将同一 EXE 附到对应 GitHub 稳定 Release。公开 Release 后，官网工作流会校验 OSS 文件并部署 Windows 按钮。若先公开了 Release，等 OSS 校验通过后，用该标签手动重跑 [Website release](https://github.com/angrypandahu/yingji-releases/actions/workflows/website-release.yml)。
- **应用内更新**：在持钥机使用私有源码中同版本的 `scripts/windows-release.mjs sign-feed`，从上述归档生成并验签 `update.windows-x64.json`。用公网更新目录的 EXE 测试 `Range: bytes=0-15`，应返回 HTTP 206 和 16 字节。确认当前稳定入口版本、备份已有清单，并核对即将切换的版本后，最后执行下面的命令。已有清单的覆盖提示只在确认本次正式切换时接受。

```powershell
ossutil cp (Join-Path $archive 'update.windows-x64.json') oss://jingshenkeji-yingji-releases/updates/windows-x64/update.json --cache-control no-cache --region cn-shanghai
```

切换后，从 [Windows 正式更新入口](https://yj.jingshenkeji.cn/updates/windows-x64/update.json) 匿名读回清单，与本地已验签文件核对并检查 `Cache-Control`，再在 Windows 客户端点击「检查更新」。
