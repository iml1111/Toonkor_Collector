from cx_Freeze import setup, Executable
import sys, os
import requests.certs

includeFile = [(requests.certs.where(), "cacert.pem"),
"C:\\Users\\IML\\AppData\\Local\\Programs\\Python\\Python37-32\\DLLs\\tcl86t.dll", 
"C:\\Users\\IML\\AppData\\Local\\Programs\\Python\\Python37-32\\DLLs\\tk86t.dll"]

os.environ['REQUESTS_CA_BUNDLE'] = os.path.join(os.getcwd(), "cacert.pem")

buildOptions = dict(
	packages = ["PyQt5","sys","bs4","requests","selenium","os","queue",\
    "PIL","idna.idnadata","shutil","threading","xml","ssl"], 
	excludes = ["tkinter", "sqlite3"],
    include_files = includeFile)

base = None
if sys.platform == "win32": #windows GUI 일경우 
    base = "Win32GUI"
    #base = "Console"

exe = [Executable("main.py", base=base,  targetName="TC.exe")]

setup(
    name='Toonkor Collector',
    version = '0.2',
    author = "IML",
    description = "I'M IML!",
    options = dict(build_exe = buildOptions),
    executables = exe
)