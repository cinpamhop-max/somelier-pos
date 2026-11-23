@echo off
cd /d "%~dp0"
echo Instalando dependencias de Sommelier POS...
py -m pip install -r requirements.txt
if errorlevel 1 (
 echo No se pudo instalar. Verifica que Python este instalado y agregado al PATH.
 pause
 exit /b 1
)
echo Iniciando Sommelier POS...
py app.py
pause
