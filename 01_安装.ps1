param([switch]$ModelsOnly)
$ErrorActionPreference = 'Stop'
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$root = $PSScriptRoot
if (-not $root) { throw '无法定位程序目录。' }
if ([System.IO.Path]::GetPathRoot($root) -match '^C:\\$') {
    throw '为避免占用 C 盘，请先把本文件夹解压到 D: 或 E: 等非系统盘，再运行安装。'
}
$downloads = Join-Path $root 'downloads'
$portableRoot = Join-Path $root 'runtime'
$portable = Join-Path $portableRoot 'ComfyUI_windows_portable'
$checkpoints = Join-Path $portable 'ComfyUI\models\checkpoints'
foreach ($folder in @($downloads,$portableRoot,(Join-Path $root 'cache'),(Join-Path $root 'temp'),(Join-Path $root 'input'),(Join-Path $root 'output'))) {
    New-Item -ItemType Directory -Force -Path $folder | Out-Null
}

function Download-Resume([string]$Url, [string]$Destination) {
    $curl = (Get-Command 'curl.exe' -ErrorAction SilentlyContinue)
    if (-not $curl) { throw '找不到 Windows 内置 curl.exe。请更新 Windows 或手动下载官方文件。' }
    Write-Host "下载：$Url" -ForegroundColor Cyan
    & curl.exe --fail --location --retry 4 --retry-delay 3 --connect-timeout 30 --continue-at - --output $Destination $Url
    if ($LASTEXITCODE -ne 0) { throw "下载失败。请检查网络，重新运行会尝试续传：$Destination" }
}

function Find-Extractor {
    foreach ($candidate in @('C:\Program Files\7-Zip\7z.exe','C:\Program Files (x86)\7-Zip\7z.exe')) {
        if (Test-Path $candidate) { return $candidate }
    }
    $c = (Get-Command 7z.exe -ErrorAction SilentlyContinue)
    if ($c) { return $c.Source }
    $mini = Join-Path $downloads '7zr.exe'
    if (-not (Test-Path $mini)) {
        Download-Resume 'https://www.7-zip.org/a/7zr.exe' $mini
    }
    return $mini
}

function Ensure-Portable {
    if (Test-Path (Join-Path $portable 'python_embeded\python.exe')) {
        Write-Host '检测到已有 ComfyUI 便携版，跳过运行环境下载。' -ForegroundColor Green
        return
    }
    $archive = Join-Path $downloads 'ComfyUI_windows_portable_nvidia.7z'
    Write-Host '准备下载 ComfyUI Windows NVIDIA 便携版。下载较大，请保留足够硬盘空间。' -ForegroundColor Yellow
    Download-Resume 'https://github.com/comfyanonymous/ComfyUI/releases/latest/download/ComfyUI_windows_portable_nvidia.7z' $archive
    $extractor = Find-Extractor
    Write-Host '解压运行环境中…' -ForegroundColor Cyan
    & $extractor x -y $archive "-o$portableRoot"
    if ($LASTEXITCODE -ne 0 -or -not (Test-Path (Join-Path $portable 'python_embeded\python.exe'))) {
        throw '解压失败，或便携版目录结构与预期不同。请检查 runtime 文件夹与下载的归档。'
    }
    Write-Host 'ComfyUI 解压完成。' -ForegroundColor Green
    $answer = Read-Host '是否删除便携版的安装压缩包以节省磁盘？(Y/n；默认 Y)'
    if ($answer -notmatch '^(n|N)$') { Remove-Item $archive -Force }
}

function Ensure-Checkpoint([string]$Name,[string]$Url,[string]$Hash) {
    New-Item -ItemType Directory -Force -Path $checkpoints | Out-Null
    $target = Join-Path $checkpoints $Name
    if (Test-Path $target) {
        Write-Host "模型已存在：$Name，检查 SHA256…" -ForegroundColor Gray
        $current = (Get-FileHash $target -Algorithm SHA256).Hash.ToLowerInvariant()
        if ($current -eq $Hash) {
            Write-Host '校验通过，跳过下载。' -ForegroundColor Green
            return
        }
        Write-Host '已有模型的 SHA256 不匹配，先移走，不会覆盖它。' -ForegroundColor Yellow
        Rename-Item $target ($Name + '.invalid-' + (Get-Date -Format 'yyyyMMdd-HHmmss'))
    }
    Download-Resume $Url $target
    Write-Host "正在检查 $Name 的 SHA256…"
    $actual = (Get-FileHash $target -Algorithm SHA256).Hash.ToLowerInvariant()
    if ($actual -ne $Hash) {
        throw "模型校验失败：$Name。文件保留在 checkpoints，建议删除后重新运行下载。"
    }
    Write-Host "模型安装完成：$Name" -ForegroundColor Green
}

try {
    if (-not $ModelsOnly) { Ensure-Portable }
    if (-not (Test-Path (Join-Path $portable 'python_embeded\python.exe'))) {
        throw '缺少 ComfyUI 运行环境，请先运行 01_安装.cmd。'
    }
    Write-Host ''
    Write-Host '模型安装选项：' -ForegroundColor Cyan
    Write-Host ' [1] 动漫（Animagine XL 4.0，约 7 GB）'
    Write-Host ' [2] 动漫 + 真人（两模型合计约 14 GB）'
    Write-Host ' [3] 只装真人（RealVisXL V5，约 7 GB）'
    Write-Host ' [0] 稍后手动安装模型'
    $choice = Read-Host '请选择 0/1/2/3（默认 2）'
    if (-not $choice) { $choice = '2' }
    if ($choice -notin @('0','1','2','3')) { throw '选择无效。' }
    if ($choice -in @('1','2')) {
        Ensure-Checkpoint 'animagine-xl-4.0-opt.safetensors' `
            'https://huggingface.co/cagliostrolab/animagine-xl-4.0/resolve/main/animagine-xl-4.0-opt.safetensors' `
            '6327eca98bfb6538dd7a4edce22484a1bbc57a8cff6b11d075d40da1afb847ac'
    }
    if ($choice -in @('2','3')) {
        Ensure-Checkpoint 'RealVisXL_V5.0_fp16.safetensors' `
            'https://huggingface.co/SG161222/RealVisXL_V5.0/resolve/main/RealVisXL_V5.0_fp16.safetensors' `
            '6a35a7855770ae9820a3c931d4964c3817b6d9e3c6f9c4dabb5b3a94e5643b80'
    }
    Write-Host ''
    Write-Host '准备就绪！双击 02_启动.cmd 即可打开中文画室。' -ForegroundColor Green
    Write-Host ('模型目录：' + $checkpoints)
    Write-Host ('图片目录：' + (Join-Path $root 'output'))
    exit 0
} catch {
    Write-Host ('安装出错：' + $_.Exception.Message) -ForegroundColor Red
    exit 1
}
