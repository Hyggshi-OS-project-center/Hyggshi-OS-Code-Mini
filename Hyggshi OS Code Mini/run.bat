@echo off
REM Download and install the necessary utilities if you don't have them already.
set LOGFILE=install_log.txt
echo ==== Check and install libraries ==== > %LOGFILE%

REM Check and install utility files (e.g. icons, modules, plugins, Resources)
call :check_folder icons
call :check_folder module
call :check_folder plugins
call :check_folder Resources

REM Function to check and install each package
call :check_install pyqt5
call :check_install pyqt5-sip
call :check_install pyinstaller
call :check_install qscintilla
call :check_install requests
call :check_install lupa
call :check_install keyring
call :check_install pillow
call :check_install markdown
call :check_install pygments

REM Run the application
python HyggshiOSCodeMini.py
pause
goto :eof

:check_install
pip show %1 >nul 2>&1
if errorlevel 1 (
    echo [%1] Not yet, installing... >> %LOGFILE%
    pip install %1 >> %LOGFILE% 2>&1
) else (
    echo [%1] Already have. >> %LOGFILE%
)
goto :eof

:check_folder
if not exist "%~1" (
    echo [folder %~1] Not available yet, please copy or create full! >> %LOGFILE%
) else (
    echo [folder %~1] Already have. >> %LOGFILE%
)
goto :eof
