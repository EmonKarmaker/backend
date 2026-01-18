import subprocess

FFMPEG = r"C:\ffmpeg\bin\ffmpeg.exe"

subprocess.run([FFMPEG, "-version"], check=True)
