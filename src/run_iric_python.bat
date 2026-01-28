@echo off
setlocal

set "SELFPATH=%~dp0"

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

set "IRIC_ENV_DIR=%MINICONDA_DIR%\envs\iric"
set "IRIC_PYTHON=%IRIC_ENV_DIR%\python.exe"

if not exist "%IRIC_PYTHON%" (
  echo エラー: iRIC の Python が見つかりません。
  echo パスを確認してください: %IRIC_PYTHON%
  exit /b 1
)

@REM iric 用 DLL を参照できるよう PATH を設定
set "PATH=%IRIC_ENV_DIR%;%IRIC_ENV_DIR%\Library\bin;%IRIC_ENV_DIR%\Scripts;%PATH%"

if "%~1"=="" (
  echo iRIC 用の Python を起動します
  "%IRIC_PYTHON%"
) else (
  "%IRIC_PYTHON%" %*
)

set "EXIT_CODE=%ERRORLEVEL%"
endlocal & exit /b %EXIT_CODE%
