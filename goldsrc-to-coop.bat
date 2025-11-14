@ECHO OFF
REM Set working directory to the batch file location
CD /D "%~dp0"

REM Get the first argument (dragged file)
SET "BSP_FILE=%~1"

REM Parse optional --output-mod parameter
SET "OUTPUT_MOD_PATH="
IF "%~2"=="--output-mod" SET "OUTPUT_MOD_PATH=%~3"

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
SET "BLEND_EXPORT_PATH=%~dp0\scripts\blend-export.blend"
SET "CREATE_LUA_PATH=%~dp0\scripts\create-lua.py"
SET "PYTHON_PATH=%~dp0\tools\blender-3.6.23-windows-x64\3.6\python\bin\python.exe"
SET SCALE=-22

REM Check that important files exist
IF NOT EXIST "%PROMPT_FOR_HL_DIR_PATH%" ECHO PROMPT_FOR_HL_DIR_PATH not found & PAUSE & EXIT /B
IF NOT EXIST "%BSPGUY_PATH%" ECHO BSPGUY not found & PAUSE & EXIT /B
IF NOT EXIST "%BSPGUY_INI_PATH%" ECHO BSPGUY_INI_PATH not found & PAUSE & EXIT /B
IF NOT EXIST "%BLENDER_PATH%" ECHO Blender not found & PAUSE & EXIT /B
IF NOT EXIST "%BLEND_EXPORT_PATH%" ECHO Blender export file not found & PAUSE & EXIT /B
IF NOT EXIST "%BSP_FILE%" ECHO BSP file not found & PAUSE & EXIT /B

REM Get base name of BSP file
FOR %%F IN ("%BSP_FILE%") DO SET "BSP_NAME=%%~nF"

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

REM Run the command to convert BSP to OBJ and export the entities
"%BSPGUY_PATH%" exportobj "%BSP_FILE%" -scale "%SCALE%" -lightmap "1" -o "%OUT_DIR%"
"%BSPGUY_PATH%" exportent "%BSP_FILE%" -o "%OUT_DIR%\entities.txt"

REM Import all OBJ files into Blender
"%BLENDER_PATH%" --background --python scripts/import-all-objs.py -- "%OUT_DIR%" "%OUT_DIR%/entities.txt" "%SCALE%"

REM Combine OBJs to UV2
"%BLENDER_PATH%" --background --python scripts/combine-into-uv2.py -- "%OUT_DIR%/1-imported-objs.blend"

REM Convert materials to blender-visible lightmap
"%BLENDER_PATH%" --background --python scripts/blender-lightmap.py -- "%OUT_DIR%/2-combine-uv2.blend"

REM Convert materials to coop lightmap
"%BLENDER_PATH%" --background --python scripts/coop-lightmap.py -- "%OUT_DIR%/2-combine-uv2.blend"

REM Set fast64 stuff
"%BLENDER_PATH%" --background --python scripts/set-fast64-stuff.py -- "%OUT_DIR%/4-coop-lightmap.blend"

REM Export level
"%BLENDER_PATH%" --background --python scripts/export-level.py -- "%OUT_DIR%/5-set-fast64.blend" "%BSP_NAME%" "%BLEND_EXPORT_PATH%"

REM Create lua files
"%PYTHON_PATH%" "%CREATE_LUA_PATH%" "%BSP_NAME%" "%OUT_DIR%/entities.txt" "%SCALE%"

REM If --output-mod was specified, copy the mod directory to the given path
IF DEFINED OUTPUT_MOD_PATH (
    ECHO Copying mod to "%OUTPUT_MOD_PATH%"
    XCOPY "%OUT_DIR%\mod" "%OUTPUT_MOD_PATH%" /E /I /Y
)

PAUSE
