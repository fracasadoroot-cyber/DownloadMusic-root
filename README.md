Abre Powershell para descargar Python-FFmpeg-Git Fracasadoroot-cyber
winget install Python.Python.3.12

winget install Gyan.FFmpeg

winget install Git.Git

cd $env:USERPROFILE\Desktop

git clone https://github.com/fracasadoroot-cyber/DownloadMusic-root.git

cd DownloadMusic-root
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt

Set-ExecutionPolicy -Scope CurrentUser RemoteSigned

Musica1: .\ytmusic-dl.ps1 "https://youtu.be/wUL8NklXDsw"
Mix/playlist:  .\ytmusic-dl.ps1 --mix "link"
Video:  .\ytmusic-dl.ps1 --video "link"

Al descargar se musica o video se creara una carpeta en el "DownloadMusic-root" 
