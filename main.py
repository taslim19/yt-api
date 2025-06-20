from fastapi import FastAPI, Query
from fastapi.responses import FileResponse
from pydantic import BaseModel
import yt_dlp
import os
import uuid

app = FastAPI()

DOWNLOAD_DIR = "downloads"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

class VideoInfo(BaseModel):
    title: str
    thumbnail: str
    formats: list

@app.get("/info", response_model=VideoInfo)
def get_info(url: str = Query(..., description="YouTube or YT Music URL")):
    ydl_opts = {
        'quiet': True,
        'skip_download': True,
        'format': 'bestaudio/best',
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)
        return {
            "title": info['title'],
            "thumbnail": info['thumbnail'],
            "formats": info['formats'],
        }

@app.get("/download")
def download(url: str = Query(...)):
    uid = str(uuid.uuid4())
    temp_filename = f"{uid}.%(ext)s"
    output_path = os.path.join(DOWNLOAD_DIR, temp_filename)

    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': output_path,
        'quiet': True,
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
        }]
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])

    # Find the actual file
    for file in os.listdir(DOWNLOAD_DIR):
        if file.startswith(uid):
            return FileResponse(os.path.join(DOWNLOAD_DIR, file), filename=file)

    return {"error": "Download failed"}
