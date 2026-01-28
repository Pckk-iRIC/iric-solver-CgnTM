@echo off
setlocal

set "SELFPATH=%~dp0"
set "VENV_DIR=%SELFPATH%venv"
set "IRIC_RUNNER=%SELFPATH%run_iric_python.bat"

@REM 仮想環境が無い場合は作成（iRIC の Python を使用）
if not exist "%VENV_DIR%\Scripts\python.exe" (
  echo 仮想環境を作成します

  if not exist "%IRIC_RUNNER%" (
    echo エラー: %IRIC_RUNNER% が見つかりません。
    exit /b 1
  )

  call "%IRIC_RUNNER%" -m venv "%VENV_DIR%"
  if errorlevel 1 (
    echo エラー: 仮想環境の作成に失敗しました。
    exit /b 1
  )

  "%VENV_DIR%\Scripts\python.exe" -m pip install --upgrade pip
  "%VENV_DIR%\Scripts\python.exe" -m pip install h5py
)

if "%~1"=="" (
  echo 仮想環境の Python を起動します
  "%VENV_DIR%\Scripts\python.exe"
) else (
  "%VENV_DIR%\Scripts\python.exe" %*
)

set "EXIT_CODE=%ERRORLEVEL%"
endlocal & exit /b %EXIT_CODE%
