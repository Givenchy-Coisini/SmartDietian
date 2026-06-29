# scripts/git-commit-push.ps1
# 一键 commit + push 脚本，沉淀了 SmartDietian 项目里踩过的所有坑：
#   1. 中文 commit message 用 UTF-8 无 BOM 临时文件 + git commit -F，避免 PowerShell GBK 控制台导致仓库存的字节错位。
#   2. push 默认重试 3 次（GitHub 国内访问偶发连接被重置 / 端口 443 超时）。
#   3. git 写到 stderr 的进度信息在 PowerShell 里会被当作 NativeCommandError，本脚本用 $LASTEXITCODE 真实判断成败。
#   4. 默认 git add -A，可通过 -Path 精确指定要 add 的文件 / 目录。
#
# 用法：
#   .\scripts\git-commit-push.ps1 "提交信息"
#   .\scripts\git-commit-push.ps1 "提交信息" -Path "app","frontend/src/utils"
#   .\scripts\git-commit-push.ps1 "提交信息" -NoPush                       # 只 commit 不 push
#   .\scripts\git-commit-push.ps1 "提交信息" -Branch dev                   # 推到指定分支
#   .\scripts\git-commit-push.ps1 "提交信息" -Remote origin -Retries 5 -RetryDelaySec 3
#   .\scripts\git-commit-push.ps1 -h                                       # 查看帮助
[CmdletBinding()]
param(
    [Parameter(Position = 0)]
    [string] $Message,

    [string[]] $Path = @(),

    [string] $Remote = 'origin',

    [string] $Branch = '',

    [int] $Retries = 3,

    [int] $RetryDelaySec = 5,

    [switch] $NoPush,

    [switch] $AllowEmpty,

    [Alias('h')]
    [switch] $Help
)

$ErrorActionPreference = 'Stop'

# 关键：PowerShell 5 默认控制台/外部命令解码用 OEM 代码页（中文系统下是 GBK），
# 而 git 输出的是 UTF-8 字节。如果不强制把编码切到 UTF-8，
# 像 `git rev-parse --show-toplevel` 返回的中文路径就会被解码成乱码，
# 后续 Set-Location 找不到路径而崩。下面三行解决这个问题，仅作用于本脚本进程。
try {
    [Console]::OutputEncoding = [System.Text.Encoding]::UTF8
    [Console]::InputEncoding = [System.Text.Encoding]::UTF8
    $OutputEncoding = [System.Text.Encoding]::UTF8
} catch { }

function Show-Help {
    Get-Content $PSCommandPath | Select-Object -First 22 | ForEach-Object { Write-Host $_ }
}

if ($Help -or [string]::IsNullOrWhiteSpace($Message)) {
    Show-Help
    if ([string]::IsNullOrWhiteSpace($Message) -and -not $Help) {
        Write-Host ''
        Write-Host '[ERROR] 必须提供 commit message。示例：.\scripts\git-commit-push.ps1 "提交信息"' -ForegroundColor Red
        exit 1
    }
    exit 0
}

# ─── 第 1 步：确认当前目录是一个 git 仓库 ───
try {
    $repoRoot = (git rev-parse --show-toplevel 2>$null) | Out-String
    $repoRoot = $repoRoot.Trim()
    if ($LASTEXITCODE -ne 0 -or [string]::IsNullOrWhiteSpace($repoRoot)) {
        throw 'not a git repo'
    }
} catch {
    Write-Host '[ERROR] 当前目录不是一个 git 仓库。' -ForegroundColor Red
    exit 1
}
Set-Location $repoRoot
Write-Host "[INFO] 仓库根目录: $repoRoot" -ForegroundColor Cyan

# ─── 第 2 步：确定目标分支 ───
if ([string]::IsNullOrWhiteSpace($Branch)) {
    $Branch = (git rev-parse --abbrev-ref HEAD 2>$null).Trim()
    if ($LASTEXITCODE -ne 0 -or [string]::IsNullOrWhiteSpace($Branch) -or $Branch -eq 'HEAD') {
        Write-Host '[ERROR] 无法确定当前分支（detached HEAD？）。请用 -Branch 显式指定。' -ForegroundColor Red
        exit 1
    }
}
Write-Host "[INFO] 目标分支: $Branch    远端: $Remote" -ForegroundColor Cyan

# ─── 第 3 步：git add ───
if ($Path.Count -gt 0) {
    Write-Host "[INFO] git add 指定路径: $($Path -join ', ')" -ForegroundColor Cyan
    git add -- @Path
} else {
    Write-Host '[INFO] git add -A（全部变更）' -ForegroundColor Cyan
    git add -A
}
if ($LASTEXITCODE -ne 0) {
    Write-Host '[ERROR] git add 失败。' -ForegroundColor Red
    exit 1
}

# ─── 第 4 步：检查暂存区是否有改动 ───
git diff --cached --quiet
$hasStagedChanges = ($LASTEXITCODE -ne 0)
if (-not $hasStagedChanges -and -not $AllowEmpty) {
    Write-Host '[WARN] 暂存区没有任何改动，跳过 commit。' -ForegroundColor Yellow
    Write-Host '       如果你想创建空 commit，加 -AllowEmpty 参数。' -ForegroundColor Yellow
    if (-not $NoPush) {
        Write-Host '[INFO] 仍尝试 push（同步现有 commit）...' -ForegroundColor Cyan
    } else {
        exit 0
    }
} else {
    # ─── 第 5 步：写 UTF-8 无 BOM 的 commit message 临时文件 ───
    $tmpFile = Join-Path $repoRoot ('COMMIT_MSG_TMP_' + [guid]::NewGuid().ToString('N').Substring(0, 8) + '.txt')
    try {
        [System.IO.File]::WriteAllText($tmpFile, $Message, (New-Object System.Text.UTF8Encoding $false))
        # 验证字节序列（仅在 verbose 下输出）
        if ($VerbosePreference -eq 'Continue') {
            $bytes = [System.IO.File]::ReadAllBytes($tmpFile)
            $hex = ($bytes | ForEach-Object { $_.ToString('x2') }) -join ' '
            Write-Verbose "commit message bytes: $hex"
        }

        # ─── 第 6 步：commit ───
        $commitArgs = @('commit', '-F', $tmpFile)
        if ($AllowEmpty) { $commitArgs += '--allow-empty' }
        git @commitArgs
        if ($LASTEXITCODE -ne 0) {
            Write-Host '[ERROR] git commit 失败。' -ForegroundColor Red
            exit 1
        }
        $commitHash = (git rev-parse --short HEAD).Trim()
        Write-Host "[OK]   commit $commitHash 已生成。" -ForegroundColor Green
    } finally {
        if (Test-Path $tmpFile) { Remove-Item $tmpFile -Force -ErrorAction SilentlyContinue }
    }
}

# ─── 第 7 步：push（带重试） ───
if ($NoPush) {
    Write-Host '[INFO] -NoPush 指定，跳过推送。' -ForegroundColor Cyan
    exit 0
}

$attempt = 0
$pushed = $false
# 在推送循环里临时把 ErrorActionPreference 改为 Continue，
# 否则 git 输出 stderr 内容（如 "fatal: unable to access..."）会被 PowerShell 5 当作
# terminating error 直接抛出 NativeCommandError，导致重试循环被强行中断。
$savedEAP = $ErrorActionPreference
$ErrorActionPreference = 'Continue'
try {
    while ($attempt -lt $Retries -and -not $pushed) {
        $attempt++
        Write-Host "[INFO] git push $Remote $Branch  (第 $attempt/$Retries 次尝试)" -ForegroundColor Cyan
        # 把 stderr 合并到 stdout
        $pushOutput = & git push $Remote $Branch 2>&1
        $pushExit = $LASTEXITCODE
        foreach ($line in $pushOutput) { Write-Host $line }
        if ($pushExit -eq 0) {
            $pushed = $true
            Write-Host "[OK]   push 成功 -> $Remote/$Branch" -ForegroundColor Green
            break
        }
        Write-Host "[WARN] 第 $attempt 次推送失败（exit=$pushExit）" -ForegroundColor Yellow
        if ($attempt -lt $Retries) {
            Write-Host "       $RetryDelaySec 秒后重试..." -ForegroundColor Yellow
            Start-Sleep -Seconds $RetryDelaySec
        }
    }
} finally {
    $ErrorActionPreference = $savedEAP
}

if (-not $pushed) {
    Write-Host "[ERROR] $Retries 次推送都失败了。你可以手动重试：git push $Remote $Branch" -ForegroundColor Red
    exit 1
}

exit 0
