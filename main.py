import os
import random
import yt_dlp
import time
from fastapi import FastAPI
from fastapi.exceptions import HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from yt_dlp.postprocessor import FFmpegPostProcessor


download_path = os.environ.get('DOWNLOAD_PATH') or './downloads'
port = os.environ.get('PORT') or '80'
ffmpeg_location = os.environ.get('FFMPEG_LOCATION') or '/usr/bin/ffmpeg'

# Ensure download directory exists
os.makedirs(download_path, exist_ok=True)


FFmpegPostProcessor._ffmpeg_location.set(ffmpeg_location)


class YtVideoDownloadRequestBody(BaseModel):
    url: str


def generate_random_file_name():
    timestamp_ms = int(time.time() * 1000)
    random_number = random.random()
    return f"{timestamp_ms}{random_number}"


app = FastAPI()

app.mount("/downloads", StaticFiles(directory=download_path), name="downloads")


@app.get("/")
def health():
    return {"success": "true", "message": f'downloader service running on port {port}'}


@app.get("/api/download/{url:path}")
def download_video(url: str):
    file_name = f'{generate_random_file_name()}.m4a'
    urls = [url]
    ydl_opts = {
        'outtmpl': {
            'default': "/".join([download_path, file_name]),
        },
        'format': 'm4a/bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'm4a',
        }]
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        error_code = ydl.download(urls)

    if error_code == 0:
        return {"status": "success", "file_name": file_name}
    else:
        raise HTTPException(506, detail="download failed for internal server error")

@app.get("/api/transcript/{url:path}")
def get_transcripts(url: str):
    file_name_prefix = generate_random_file_name()
    ydl_opts = {
        'outtmpl': os.path.join(download_path, f"{file_name_prefix}"),
        'skip_download': True,
        'writesubtitles': True,
        'writeautomaticsub': True,
        'subtitleslangs': ['en.*'],
        'postprocessors': [{
            'key': 'FFmpegSubtitlesConvertor',
            'format': 'srt',
        }],
        'quiet': True,
        'no_warnings': True,
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        error_code = ydl.download([url])

    if error_code == 0:
        # Check for files starting with file_name_prefix
        files = os.listdir(download_path)
        for f in files:
            if f.startswith(file_name_prefix) and f.endswith(('.srt', '.vtt')):
                return {"status": "success", "file_name": f}
        
        raise HTTPException(404, detail="English transcript not found for this video")
    else:
        raise HTTPException(506, detail="download failed for internal server error")

@app.get("/api/files")
def list_files():
    files = os.listdir(download_path)
    return {"files": files}

@app.get("/api/files/{filename}")
def download_file(filename: str):
    file_path = os.path.join(download_path, filename)
    if not os.path.exists(file_path):
        raise HTTPException(404, detail="File not found")
    return FileResponse(file_path, media_type="audio/m4a")
