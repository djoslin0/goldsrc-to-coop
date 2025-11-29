@ECHO OFF
REM Set working directory to the batch file location
CD /D "%~dp0"

REM Get the first argument (dragged file)
SET "BSP_FILE=%~1"

REM Parse optional parameters
SET "OUTPUT_MOD_PATH="
SET "LUA_ONLY=0"
IF "%~2"=="--output-mod" (
    SET "OUTPUT_MOD_PATH=%~3"
    IF "%~4"=="--lua-only" SET "LUA_ONLY=1"
) ELSE IF "%~2"=="--lua-only" (
    SET "LUA_ONLY=1"
    IF "%~3"=="--output-mod" SET "OUTPUT_MOD_PATH=%~4"
)

REM Check that a file was actually provided
IF "%BSP_FILE%"=="" (
    ECHO Drag and drop a BSP file onto this script.
    PAUSE
    EXIT /B
)

ECHO Using BSP file: "%BSP_FILE%"

REM Set paths
SET "PROMPT_FOR_HL_DIR_PATH=%~dp0\scripts\prompt-for-hl-dir.py"
SET "BSPGUY_PATH=%~dp0\tools\bspguy\bspguy.exe"
SET "BSPGUY_INI_PATH=%~dp0\tools\bspguy\bspguy.ini"
SET "BLENDER_PATH=%~dp0\tools\blender-3.6.23-windows-x64\blender.exe"
SET "BLEND_EXPORT_PATH=%~dp0\scripts\blender\blend-export.blend"
SET "CREATE_LUA_PATH=%~dp0\scripts\create-lua.py"
SET "PYTHON_PATH=%~dp0\tools\blender-3.6.23-windows-x64\3.6\python\bin\python.exe"
SET "MAGICK_PATH=%~dp0\tools\imagemagick\magick.exe"
SET SCALE=-25

REM Check that important files exist
IF NOT EXIST "%PROMPT_FOR_HL_DIR_PATH%" ECHO PROMPT_FOR_HL_DIR_PATH not found & PAUSE & EXIT /B
IF NOT EXIST "%BSPGUY_PATH%" ECHO BSPGUY not found & PAUSE & EXIT /B
IF NOT EXIST "%BSPGUY_INI_PATH%" ECHO BSPGUY_INI_PATH not found & PAUSE & EXIT /B
IF NOT EXIST "%BLENDER_PATH%" ECHO Blender not found & PAUSE & EXIT /B
IF NOT EXIST "%BLEND_EXPORT_PATH%" ECHO Blender export file not found & PAUSE & EXIT /B
IF NOT EXIST "%BSP_FILE%" ECHO BSP file not found & PAUSE & EXIT /B
IF NOT EXIST "%MAGICK_PATH%" ECHO Magick not found & PAUSE & EXIT /B

REM Get base name of BSP file
FOR %%F IN ("%BSP_FILE%") DO SET "BSP_NAME=%%~nF"

REM Override the scale for kz maps
IF "%BSP_NAME:~0,3%"=="kz_" (
    SET SCALE=-15
)
IF "%BSP_NAME:~0,4%"=="mls_" (
    SET SCALE=-15
)

REM Output directory
SET "OUT_DIR=%~dp0\output\%BSP_NAME%"
IF NOT EXIST "%OUT_DIR%" MD "%OUT_DIR%"

REM Get/set the half life dir
"%PYTHON_PATH%" "%PROMPT_FOR_HL_DIR_PATH%" "%BSPGUY_INI_PATH%"
IF NOT %ERRORLEVEL%==0 (
    ECHO ❌ Failed to set Half-Life directory. Exiting.
    PAUSE
    EXIT /B %ERRORLEVEL%
)

IF "%LUA_ONLY%"=="1" GOTO :skip_conversion

REM Delete OUT_DIR
IF EXIST "%OUT_DIR%" RMDIR /S /Q "%OUT_DIR%

REM Run the command to convert BSP to OBJ and export the entities
"%BSPGUY_PATH%" exportobj "%BSP_FILE%" -scale "%SCALE%" -lightmap "1" -withmdl "0" -o "%OUT_DIR%"
"%BSPGUY_PATH%" exportent "%BSP_FILE%" -o "%OUT_DIR%\entities.txt"

REM Adjust gamma for atlas images
FOR %%f IN ("%OUT_DIR%\atlases\*.png") DO "%MAGICK_PATH%" "%%f" -level 0%%,100%%,1.3 "%%f"

REM Run blender goldsrc pipeline
"%BLENDER_PATH%" --background --python scripts/blender/goldsrc_pipeline.py -- "%OUT_DIR%" "%BSP_NAME%" "%BLEND_EXPORT_PATH%" "%SCALE%"

:skip_conversion

REM Create lua files
"%PYTHON_PATH%" "%CREATE_LUA_PATH%" "%BSP_NAME%" "%OUT_DIR%/entities.txt" "%SCALE%" "%LUA_ONLY%"

REM If --output-mod was specified, copy the mod directory to the given path
IF DEFINED OUTPUT_MOD_PATH (
    ECHO Copying mod to "%OUTPUT_MOD_PATH%"
    XCOPY "%OUT_DIR%\mod" "%OUTPUT_MOD_PATH%" /E /I /Y /Q
)

PAUSE
