@echo off
rem ==========================================================================
rem  The Best Flag Game - crea l'eseguibile Windows
rem
rem    build.bat               venv + dipendenze + test + eseguibile
rem    build.bat --senza-test  salta i test (piu' veloce)
rem
rem  L'ambiente virtuale e i file temporanei di PyInstaller vanno in
rem  %LOCALAPPDATA%\FlagGame-build (fuori da OneDrive: sono centinaia di MB).
rem  Per cambiarla: set FLAGGAME_BUILD=C:\altra\cartella  prima di lanciare.
rem  Risultato: dist\FlagGame\FlagGame.exe
rem ==========================================================================
setlocal EnableExtensions
cd /d "%~dp0"
title The Best Flag Game - build

if "%FLAGGAME_BUILD%"=="" set "FLAGGAME_BUILD=%LOCALAPPDATA%\FlagGame-build"
set "VENV=%FLAGGAME_BUILD%\venv"
set "VPY=%VENV%\Scripts\python.exe"

rem --- 1. Python 3.10 o successivo --------------------------------------------
set "PYTHON="
for %%V in (3.12 3.11 3.13 3.10) do (
    if not defined PYTHON (
        py -%%V -c "import sys" >nul 2>&1 && set "PYTHON=py -%%V"
    )
)
if not defined PYTHON (
    python -c "import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)" >nul 2>&1 && set "PYTHON=python"
)
if not defined PYTHON (
    echo [ERRORE] Python 3.10 o successivo non trovato.
    echo          Installalo da https://www.python.org/downloads/ e riprova.
    goto :errore
)
echo [1/5] Python trovato: %PYTHON%

rem --- 2. Ambiente virtuale ---------------------------------------------------
if not exist "%VPY%" (
    echo [2/5] Creo l'ambiente virtuale in "%VENV%" ...
    %PYTHON% -m venv "%VENV%" || goto :errore
) else (
    echo [2/5] Ambiente virtuale gia' presente: "%VENV%"
)

rem --- 3. Dipendenze ----------------------------------------------------------
echo [3/5] Installo le dipendenze ...
"%VPY%" -m pip install --disable-pip-version-check -q --upgrade pip || goto :errore
"%VPY%" -m pip install --disable-pip-version-check -q -r requirements-dev.txt || goto :errore

rem --- 4. Test ----------------------------------------------------------------
if /i "%~1"=="--senza-test" (
    echo [4/5] Test saltati.
) else (
    echo [4/5] Eseguo i test, circa un minuto ...
    "%VPY%" -m pytest -q -p no:cacheprovider || goto :errore
)

rem --- 5. Eseguibile ----------------------------------------------------------
echo [5/5] Creo l'eseguibile con PyInstaller ...
if not exist "assets\icona.ico" "%VPY%" tools\genera_icona.py
"%VPY%" -m PyInstaller --noconfirm --clean --log-level WARN ^
    --windowed --onedir --name FlagGame ^
    --icon "%~dp0assets\icona.ico" ^
    --add-data "%~dp0dati;dati" ^
    --add-data "%~dp0assets;assets" ^
    --exclude-module tkinter --exclude-module pytest --exclude-module PIL ^
    --distpath "%~dp0dist" --workpath "%FLAGGAME_BUILD%\work" --specpath "%FLAGGAME_BUILD%" ^
    "%~dp0main.py" || goto :errore

rem OpenGL software (20 MB): non serve, l'interfaccia usa solo il disegno raster.
del /q "%~dp0dist\FlagGame\_internal\PySide6\opengl32sw.dll" >nul 2>&1

rem Copia modificabile dei dati (nomi, continenti, livelli) accanto all'eseguibile.
xcopy /e /i /y /q "%~dp0dati" "%~dp0dist\FlagGame\dati" >nul

rem Verifica: l'eseguibile si avvia, trova le bandiere e apre le schermate.
start "" /wait "%~dp0dist\FlagGame\FlagGame.exe" --verifica
if errorlevel 1 (
    echo [ERRORE] L'eseguibile e' stato creato ma la verifica di avvio non e' riuscita.
    goto :errore
)

echo.
echo ==========================================================================
echo  Fatto! Eseguibile: "%~dp0dist\FlagGame\FlagGame.exe"
echo  Le bandiere NON sono incluse: il gioco usa la cartella "flags" del progetto.
echo  Se sposti la cartella dist\FlagGame altrove, metti "flags" accanto a
echo  FlagGame.exe oppure scegli la cartella al primo avvio.
echo ==========================================================================
if /i not "%~2"=="--senza-pausa" if /i not "%~1"=="--senza-pausa" pause
exit /b 0

:errore
echo.
echo Build non riuscita: controlla i messaggi qui sopra.
if /i not "%~2"=="--senza-pausa" if /i not "%~1"=="--senza-pausa" pause
exit /b 1
