@ECHO OFF
REM Set working directory to the batch file location
pushd "%~dp0"
SET "FULLPATH=%~dp0"

REM Get the first argument (dragged file)
SET "BSP_FILE=%~1"

REM Parse optional parameters using a loop for better handling
SET "OUTPUT_MOD_PATH="
SET "LUA_ONLY=0"
SET "KZ_FLAG=0"

SHIFT
:parse_args
IF "%1"=="" GOTO :end_parse
IF "%1"=="--kz" (
    SET "KZ_FLAG=1"
    SHIFT
) ELSE IF "%1"=="--output-mod" (
    SET "OUTPUT_MOD_PATH=%2"
    SHIFT
    SHIFT
) ELSE IF "%1"=="--lua-only" (
    SET "LUA_ONLY=1"
    SHIFT
) ELSE (
    ECHO Unknown parameter: %1
    PAUSE
    EXIT /B 1
)
GOTO :parse_args
:end_parse

REM Check that a file was actually provided
IF "%BSP_FILE%"=="" (
    ECHO Drag and drop a BSP file onto this script.
    PAUSE
    EXIT /B
)

ECHO Using BSP file: "%BSP_FILE%"

REM Set paths (relative to current directory after pushd)
SET "PROMPT_FOR_HL_DIR_PATH=%FULLPATH%\scripts\prompt-for-hl-dir.py"
SET "BSPGUY_PATH=%FULLPATH%\tools\bspguy\bspguy.exe"
SET "BSPGUY_INI_PATH=%FULLPATH%\tools\bspguy\bspguy.ini"
SET "BLENDER_PATH=%FULLPATH%\tools\blender-3.6.23-windows-x64\blender.exe"
SET "BLEND_EXPORT_PATH=%FULLPATH%\scripts\blender\blend-export.blend"
SET "BLEND_SKYBOX_PATH=%FULLPATH%\scripts\blender\skybox.blend"
SET "CREATE_LUA_PATH=%FULLPATH%\scripts\create-lua.py"
SET "PYTHON_PATH=%FULLPATH%\tools\blender-3.6.23-windows-x64\3.6\python\bin\python.exe"
SET "MAGICK_PATH=%FULLPATH%\tools\imagemagick\magick.exe"
REM Check that important files exist
IF NOT EXIST "%PROMPT_FOR_HL_DIR_PATH%" ECHO PROMPT_FOR_HL_DIR_PATH not found & PAUSE & EXIT /B
IF NOT EXIST "%BSPGUY_PATH%" ECHO BSPGUY not found & PAUSE & EXIT /B
IF NOT EXIST "%BSPGUY_INI_PATH%" ECHO BSPGUY_INI_PATH not found & PAUSE & EXIT /B
IF NOT EXIST "%BLENDER_PATH%" ECHO Blender not found & PAUSE & EXIT /B
IF NOT EXIST "%BLEND_EXPORT_PATH%" ECHO Blender export file not found & PAUSE & EXIT /B
IF NOT EXIST "%BLEND_SKYBOX_PATH%" ECHO Blender skybox file not found & PAUSE & EXIT /B
IF NOT EXIST "%BSP_FILE%" ECHO BSP file not found & PAUSE & EXIT /B
IF NOT EXIST "%MAGICK_PATH%" ECHO Magick not found & PAUSE & EXIT /B

REM Get base name of BSP file
FOR %%F IN ("%BSP_FILE%") DO SET "BSP_NAME=%%~nF"

REM Set scale based on kz flag
IF "%KZ_FLAG%"=="1" (
    SET SCALE=-15
) ELSE (
    SET SCALE=-25
)

REM Output directory
SET "OUT_DIR=%FULLPATH%\output\%BSP_NAME%"
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
IF EXIST "%OUT_DIR%" RMDIR /S /Q "%OUT_DIR%"
REM Recreate OUT_DIR
MD "%OUT_DIR%"

REM Run the command to convert BSP to OBJ and export the entities
"%BSPGUY_PATH%" exportobj "%BSP_FILE%" -scale "%SCALE%" -lightmap "1" -withmdl "0" -o "%OUT_DIR%"
"%BSPGUY_PATH%" exportent "%BSP_FILE%" -o "%OUT_DIR%\entities.txt"

REM Adjust gamma for atlas images
FOR %%f IN ("%OUT_DIR%\atlases\*.png") DO "%MAGICK_PATH%" "%%f" -level 0%%,100%%,1.3 -function polynomial 1.0,0.1 "%%f"

REM Create additive versions of textures
FOR %%f IN ("%OUT_DIR%\textures\*.png") DO (
    setlocal enabledelayedexpansion
    set "input=%%f"
    set "output=!input:.png=_additive.png!"
    "%MAGICK_PATH%" "!input!" -alpha set -channel A -fx "(r+g+b)/3" "!output!"
    endlocal
)

REM Convert skybox TGAs to PNGs
IF EXIST "%OUT_DIR%\skyboxes" (
    FOR %%f IN ("%OUT_DIR%\skyboxes\*.tga") DO (
        setlocal enabledelayedexpansion
        set "tga=%%f"
        set "png=!tga:.tga=.png!"
        IF NOT EXIST "!png!" "%MAGICK_PATH%" "!tga!" "!png!"
        endlocal
    )
)

REM Run blender goldsrc pipeline
"%BLENDER_PATH%" --background --python scripts/blender/goldsrc_pipeline.py -- "%OUT_DIR%" "%BSP_NAME%" "%BLEND_EXPORT_PATH%" "%BLEND_SKYBOX_PATH%" "%SCALE%"

:skip_conversion

REM Create lua files
"%PYTHON_PATH%" "%CREATE_LUA_PATH%" "%BSP_NAME%" "%OUT_DIR%/entities.txt" "%SCALE%" "%LUA_ONLY%" "%FULLPATH%override-textures"

REM If --output-mod was specified, copy the mod directory to the given path
IF DEFINED OUTPUT_MOD_PATH (
    ECHO Copying mod to "%OUTPUT_MOD_PATH%"
    XCOPY "%OUT_DIR%\mod" "%OUTPUT_MOD_PATH%" /E /I /Y /Q
)

PAUSE
