@echo off
call "C:\ProgramData\Anaconda3\Scripts\activate.bat"
call conda activate yolo
python C:\WORK\Relabel_Detection\django\manage.py makemigrations Relabel_Detection
python C:\WORK\Relabel_Detection\django\manage.py migrate
pause