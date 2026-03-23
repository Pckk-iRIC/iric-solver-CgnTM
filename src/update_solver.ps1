param(
    [string]$TargetRoot = "$env:USERPROFILE\iRIC_v4\private\solvers"
)

$ErrorActionPreference = "Stop"
$solverName = "__SOLVER_NAME__"
$packageSolverDir = $PSScriptRoot
$targetDir = Join-Path $TargetRoot $solverName
$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$backupDir = Join-Path $TargetRoot ("{0}_backup_{1}" -f $solverName, $timestamp)
$hasBackup = $false

function Invoke-Robocopy {
    param(
        [string]$Source,
        [string]$Destination,
        [string[]]$Options
    )
    & robocopy $Source $Destination @Options | Out-Null
    $rc = $LASTEXITCODE
    if ($rc -ge 8) {
        throw "Robocopy failed. code=$rc"
    }
}

try {
    if (-not (Test-Path (Join-Path $packageSolverDir "definition.xml"))) {
        throw "配布物フォルダが見つかりません: $packageSolverDir"
    }
    if (-not (Test-Path $TargetRoot)) {
        throw "更新先ルートが見つかりません: $TargetRoot"
    }

    $pkgFull = [System.IO.Path]::GetFullPath($packageSolverDir).TrimEnd('\')
    $tgtFull = [System.IO.Path]::GetFullPath($targetDir).TrimEnd('\')
    if ($pkgFull -ieq $tgtFull) {
        throw "配布元フォルダと更新先フォルダが同一です。配布物を別の場所に展開してから実行してください。"
    }

    if (Test-Path $targetDir) {
        Write-Host "既存の $solverName フォルダが見つかりました。"
        $answer = Read-Host "バックアップを作成しますか？ [Y/n]"
        $doBackup = -not ($answer -match '^(?i)\s*n(o)?\s*$')
        if ($doBackup) {
            Write-Host "バックアップ作成（venv除外）: $backupDir"
            Invoke-Robocopy -Source $targetDir -Destination $backupDir -Options @(
                "/E", "/R:2", "/W:1",
                "/XD", "__pycache__", "venv",
                "/XF", "*.pyc", "update_solver.ps1"
            )
            $hasBackup = $true
        } else {
            Write-Host "バックアップを作成せずに更新します（venvは保持）。"
        }
    } else {
        New-Item -ItemType Directory -Path $targetDir -Force | Out-Null
    }

    Write-Host "新しいソルバーを配置します（venv除外）: $targetDir"
    Invoke-Robocopy -Source $packageSolverDir -Destination $targetDir -Options @(
        "/MIR", "/R:2", "/W:1",
        "/XD", "__pycache__", "venv",
        "/XF", "*.pyc", "update_solver.ps1"
    )

    Write-Host "更新が完了しました。"
    Write-Host "更新先: $targetDir"
    if ($hasBackup -and (Test-Path $backupDir)) {
        Write-Host "バックアップ: $backupDir"
    }
    $exitCode = 0
}
catch {
    Write-Host "[エラー] $($_.Exception.Message)"
    $exitCode = 1
}

Write-Host ""
Read-Host "Enterキーで終了"
exit $exitCode

