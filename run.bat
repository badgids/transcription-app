@echo off

REM Get the directory of this batch script
set DIR=%~dp0

REM Check if the conda environment is already activated
if "%CONDA_DEFAULT_ENV%"=="" (
    REM If not activated, activate the conda environment named "env" in the subdirectory
    call "%DIR%env\Scripts\activate"
)

REM Launch the Python program
python "%DIR%transcribe.py"
