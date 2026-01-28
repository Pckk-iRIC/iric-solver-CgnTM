@echo off
setlocal

set "SELFPATH=%~dp0"
set "ROOT_DIR=%SELFPATH%.."

@REM iRIC の Miniconda3 パスを探索
set "MINICONDA_DIR="
set "CANDIDATE1=%SELFPATH%..\..\..\Miniconda3"
set "CANDIDATE2=%SELFPATH%..\..\..\..\iRIC_v4\Miniconda3"

if exist "%CANDIDATE1%\Scripts\activate.bat" set "MINICONDA_DIR=%CANDIDATE1%"
if "%MINICONDA_DIR%"=="" if exist "%CANDIDATE2%\Scripts\activate.bat" set "MINICONDA_DIR=%CANDIDATE2%"

if "%MINICONDA_DIR%"=="" (
  echo エラー: iRIC の Miniconda3 が見つかりません。
  echo 確認パス: %CANDIDATE1%
  echo 確認パス: %CANDIDATE2%
  exit /b 1
)

@REM iRIC の conda 環境を有効化
call "%MINICONDA_DIR%\Scripts\activate.bat" base
call "%MINICONDA_DIR%\Scripts\activate.bat" iric

echo CGNS 統合処理を開始します
python "%SELFPATH%main.py" %*

endlocal
