#Requires -Version 7.0
$ErrorActionPreference = 'Stop'
$upload = Join-Path $PSScriptRoot '../upload-windows-oss.ps1'
$dir = (New-Item -ItemType Directory -Path (Join-Path ([IO.Path]::GetTempPath()) ([guid]::NewGuid()))).FullName
$remote = @{}
$bucket = 'oss://jingshenkeji-yingji-releases/'
$base = 'https://yj.jingshenkeji.cn/'
function ossutil($command, $source, $destination) {
    if ($command -ne 'cp' -or $args -notcontains '--ignore-existing' -or !$destination.StartsWith($bucket)) {
        throw 'unexpected upload'
    }
    $key = $destination.Substring($bucket.Length)
    if (!$remote.ContainsKey($key)) { $remote[$key] = [IO.File]::ReadAllBytes($source) }
    $global:LASTEXITCODE = 0
}
function Invoke-WebRequest($Uri, $OutFile) {
    if (!$Uri.StartsWith($base)) { throw 'unexpected public URL' }
    [IO.File]::WriteAllBytes($OutFile, $remote[$Uri.Substring($base.Length)])
}
function Assert-Fails($expected) {
    try { & $upload -ArtifactsDir $dir | Out-Null } catch {
        if ($_.Exception.Message -like "*$expected*") { return }
        throw
    }
    throw "expected failure: $expected"
}

try {
    $exe = 'Yingji-1.2.3-Windows-x64.exe'
    $files = foreach ($name in @($exe, "$exe.blockmap")) {
        $path = Join-Path $dir $name
        [IO.File]::WriteAllText($path, $name)
        @{ name = $name; size = (Get-Item $path).Length; sha256 = (Get-FileHash $path).Hash.ToLowerInvariant() }
    }
    @{version='1.2.3'; platform='win32-x64'; validation='check:win passed'; files=$files} |
        ConvertTo-Json | Set-Content (Join-Path $dir 'build-info.windows-x64.json')
    & $upload -ArtifactsDir $dir -DryRun | Out-Null
    if ($remote.Count) { throw 'dry run uploaded an object' }
    & $upload -ArtifactsDir $dir | Out-Null
    & $upload -ArtifactsDir $dir | Out-Null
    foreach ($key in @($exe, "updates/windows-x64/$exe", "updates/windows-x64/$exe.blockmap")) {
        if (!$remote.ContainsKey($key)) { throw "missing upload: $key" }
    }
    $remote[$exe] = [byte[]]::new($remote[$exe].Length)
    Assert-Fails '公网文件与构建收据不符'
    $remote.Clear()
    Add-Content (Join-Path $dir "$exe.blockmap") 'changed'
    Assert-Fails '本地文件与构建收据不符'
    if ($remote.Count) { throw 'uploaded before validating all inputs' }
    Write-Output 'Windows OSS upload regression passed.'
} finally {
    Remove-Item -LiteralPath $dir -Recurse -Force
}
