from fastapi import FastAPI, Query, HTTPException
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
    try:
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
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching info: {str(e)}")


@app.get("/download")
def download(
    url: str = Query(...),
    format_id: str = Query("bestaudio"),
    type: str = Query("mp3")
):
    try:
        uid = str(uuid.uuid4())
        output_path = os.path.join(DOWNLOAD_DIR, f"{uid}.%(ext)s")

        ydl_opts = {
            'format': format_id,
            'outtmpl': output_path,
            'quiet': True,
            'postprocessors': []
        }

        if type == "mp3":
            ydl_opts['postprocessors'].append({
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
            })
        elif type == "mp4":
            ydl_opts['postprocessors'].append({
                'key': 'FFmpegVideoConvertor',
                'preferedformat': 'mp4',
            })

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

        # Find the actual file
        for ext in ["mp3", "mp4", "m4a", "webm"]:
            full_path = os.path.join(DOWNLOAD_DIR, f"{uid}.{ext}")
            if os.path.exists(full_path):
                return FileResponse(full_path, filename=f"{uid}.{ext}")

        raise HTTPException(status_code=404, detail="Downloaded file not found.")
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Download failed: {str(e)}")
