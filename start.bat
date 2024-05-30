@echo off
call "C:\ProgramData\Anaconda3\Scripts\activate.bat"
call conda activate relabel
if "%1" == "h" goto begin
mshta vbscript:createobject("wscript.shell").run("""%~0"" h",0)(window.close)&&exit
:begin
python C:\WORK\Relabel_Detection\detect\main.py