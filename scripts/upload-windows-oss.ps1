#Requires -Version 7.0
[CmdletBinding()]
param(
    [Parameter(Mandatory)]
    [string]$ArtifactsDir,
    [switch]$DryRun
)

$ErrorActionPreference = 'Stop'
$bucket = 'oss://jingshenkeji-yingji-releases'
$publicBase = 'https://yj.jingshenkeji.cn'
$receipt = Get-Content -Raw -LiteralPath (Join-Path $ArtifactsDir 'build-info.windows-x64.json') | ConvertFrom-Json
if ($receipt.platform -cne 'win32-x64' -or $receipt.validation -cne 'check:win passed' -or
    $receipt.version -cnotmatch '\A[0-9]+\.[0-9]+\.[0-9]+\z') {
    throw '需要已通过 check:win 的 Windows x64 稳定版构建收据。'
}

$exe = "Yingji-$($receipt.version)-Windows-x64.exe"
$files = @{}
foreach ($name in @($exe, "$exe.blockmap")) {
    $entry = @($receipt.files | Where-Object name -CEQ $name)
    $file = Get-Item -LiteralPath (Join-Path $ArtifactsDir $name)
    if ($entry.Count -ne 1 -or $file.PSIsContainer -or ($file.Attributes -band [IO.FileAttributes]::ReparsePoint) -or
        $file.Length -le 0 -or $file.Length -ne $entry[0].size -or
        (Get-FileHash -LiteralPath $file.FullName -Algorithm SHA256).Hash -ne $entry[0].sha256) {
        throw "本地文件与构建收据不符：$name"
    }
    $files[$name] = $entry[0]
}

foreach ($key in @($exe, "updates/windows-x64/$exe", "updates/windows-x64/$exe.blockmap")) {
    $name = ($key -split '/')[-1]
    $entry = $files[$name]
    Write-Output "$publicBase/$key  $($entry.size) bytes  SHA256 $($entry.sha256)"
    if ($DryRun) { continue }

    ossutil cp (Join-Path $ArtifactsDir $name) "$bucket/$key" --ignore-existing --region cn-shanghai
    if ($LASTEXITCODE -ne 0) { throw "OSS 上传失败：$key" }

    $tmp = [IO.Path]::GetTempFileName()
    try {
        Invoke-WebRequest -Uri "$publicBase/$key" -OutFile $tmp
        if ((Get-Item -LiteralPath $tmp).Length -ne $entry.size -or
            (Get-FileHash -LiteralPath $tmp -Algorithm SHA256).Hash -ne $entry.sha256) {
            throw "公网文件与构建收据不符，请核查同名对象：$key"
        }
    } finally {
        Remove-Item -LiteralPath $tmp
    }
}
