@echo off
REM Download and install the necessary utilities if you don't have them already.
set LOGFILE=install_log.txt
echo ==== Check and install libraries ==== > %LOGFILE%

REM Check and install utility folders (e.g. icons, modules, plugins, Resources)
call :check_folder icons
call :check_folder module
call :check_folder plugins
call :check_folder Resources

REM Check and install utility executables/tools (example: git, python, 7z)
call :check_utility git
call :check_utility python
REM Thêm các tiện ích khác nếu cần, ví dụ:
REM call :check_utility 7z

REM Function to check and install each package
call :check_install pyqt5
call :check_install pyqt5-sip
call :check_install qscintilla
call :check_install requests
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

:check_utility
where %1 >nul 2>&1
if errorlevel 1 (
    echo [utility %1] Not found, please install! >> %LOGFILE%
    REM Tùy tiện ích, có thể tự động cài đặt ở đây nếu muốn
) else (
    echo [utility %1] Already have. >> %LOGFILE%
)
goto :eof
