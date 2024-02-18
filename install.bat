@echo off

REM Get the directory of this batch script
set DIR=%~dp0

REM Check if Miniconda or Anaconda is installed
set CONDA_PATH=
for /f "tokens=*" %%i in ('where conda') do set CONDA_PATH=%%i

if "%CONDA_PATH%"=="" (
    echo Miniconda or Anaconda not found on this system.
    set /p INSTALL_MINICONDA="Do you want to install Miniconda? (yes/no): "
    if /i "%INSTALL_MINICONDA%"=="yes" (
        REM Download and install Miniconda
        powershell -Command "(New-Object Net.WebClient).DownloadFile('https://repo.anaconda.com/miniconda/Miniconda3-latest-Windows-x86_64.exe', 'Miniconda3-latest-Windows-x86_64.exe')"
        start Miniconda3-latest-Windows-x86_64.exe
        echo Please follow the installation instructions to install Miniconda.
        echo Once Miniconda is installed, please run this script again.
        pause
        exit
    ) else (
        echo Exiting.
        exit
    )
) else (
    REM Create and activate a new conda environment named "env" in the current directory
    echo Miniconda or Anaconda found at %CONDA_PATH%
    echo Creating and activating conda environment...
    call "%CONDA_PATH%" create -y -p "%DIR%env" python=3.10
    call "%CONDA_PATH%" activate "%DIR%env"
)

REM Run the install.py script
echo Running installation script
python install.py
