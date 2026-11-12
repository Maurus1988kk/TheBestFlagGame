@echo off
rem Crea dist\FlagGame-<versione>.zip da condividere: test, eseguibile, zip con le
rem bandiere e prova dello zip estratto. Equivale a: build.bat --zip
call "%~dp0build.bat" --zip %*
