from cx_Freeze import setup, Executable
import sys, os
import requests.certs
os.environ['REQUESTS_CA_BUNDLE'] = os.path.join(os.getcwd(), "cacert.pem")

buildOptions = dict(
	packages = ["sys","bs4","requests","selenium","os","queue",\
    "PIL","idna.idnadata","shutil","threading","xml","ssl"], 
	excludes = ["tkinter", "sqlite3"])

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