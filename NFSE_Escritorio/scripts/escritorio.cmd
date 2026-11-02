@echo off
rem Atalho Windows para scripts\escritorio.py (nao altera politica de execucao, registro ou firewall).
rem Uso: scripts\escritorio.cmd verificar ^| construir ^| iniciar --abrir ^| estado ^| parar
setlocal
set "HERE=%~dp0"
where py >nul 2>nul
if %ERRORLEVEL%==0 (
  py -3 "%HERE%escritorio.py" %*
) else (
  python "%HERE%escritorio.py" %*
)
exit /b %ERRORLEVEL%
