rem 
rem changeMonitor.cmd
rem

set PYTHONIOENCODING=UTF-8

if "%change_monitor_home%" == "" goto do_init

goto skip_init

:do_init
set change_monitor_home=CONFIGURE HERE 
set PYTHONPATH=%change_monitor_home%;%change_monitor_home%\src
set PYTHON_HOME=%change_monitor_home%
set PATH=%PYTHON_HOME%\Scripts\;%PATH%
set PYTHON_EXE=%PYTHON_HOME%\Scripts\python.exe

:skip_init

"%PYTHON_EXE%" -u %change_monitor_home%\main.py ^
--config="config.json" ^
--logging="logging.json" ^
%1 %2 %3 %4 %5



