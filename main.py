import os
import mimetypes
import random
import yt_dlp
import time
import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.exceptions import HTTPException
from fastapi.responses import FileResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from yt_dlp.postprocessor import FFmpegPostProcessor


download_path = os.environ.get('DOWNLOAD_PATH') or './downloads'
port = os.environ.get('PORT') or '8000'
ffmpeg_location = os.environ.get('FFMPEG_LOCATION') or '/usr/bin/ffmpeg'

# Ensure download directory exists
os.makedirs(download_path, exist_ok=True)

# Add custom mimetypes
mimetypes.add_type('text/vtt', '.vtt')
mimetypes.add_type('text/plain', '.srt')


FFmpegPostProcessor._ffmpeg_location.set(ffmpeg_location)


class YtVideoDownloadRequestBody(BaseModel):
    url: str


def generate_random_file_name():
    timestamp_ms = int(time.time() * 1000)
    random_number = random.random()
    return f"{timestamp_ms}{random_number}"


async def cleanup_old_files():
    while True:
        try:
            now = time.time()
            cutoff = now - 3600  # 1 hour ago
            
            if os.path.exists(download_path):
                for filename in os.listdir(download_path):
                    file_path = os.path.join(download_path, filename)
                    if os.path.isfile(file_path):
                        if os.path.getmtime(file_path) < cutoff:
                            os.remove(file_path)
                            print(f"Deleted old file: {filename}")
        except Exception as e:
            print(f"Cleanup error: {e}")
        
        await asyncio.sleep(600)  # Run every 10 minutes


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Start cleanup task
    cleanup_task = asyncio.create_task(cleanup_old_files())
    yield
    # Shutdown: Cancel cleanup task
    cleanup_task.cancel()
    try:
        await cleanup_task
    except asyncio.CancelledError:
        pass


app = FastAPI(lifespan=lifespan)

app.mount("/downloads", StaticFiles(directory=download_path), name="downloads")


@app.get("/")
def health():
    return {"success": "true", "message": f'downloader service running on port {port}'}


@app.get("/api/download/{url:path}")
def download_video(url: str, request: Request):
    # Reconstruct the URL if query parameters were split
    full_url = url
    if request.query_params:
        full_url = f"{url}?{request.query_params}"
    
    file_name = f'{generate_random_file_name()}.m4a'
    urls = [full_url]
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
def get_transcripts(url: str, request: Request):
    # Reconstruct the URL if query parameters were split
    full_url = url
    if request.query_params:
        full_url = f"{url}?{request.query_params}"
    
    file_name_prefix = generate_random_file_name()
    ydl_opts = {
        'outtmpl': os.path.join(download_path, f"{file_name_prefix}"),
        'skip_download': True,
        'writesubtitles': True,
        'writeautomaticsub': True,
        'subtitleslangs': ['en'],
        'postprocessors': [{
            'key': 'FFmpegSubtitlesConvertor',
            'format': 'srt',
        }],
        'no_warnings': True,
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        error_code = ydl.download([full_url])

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
    
    if filename.endswith(".vtt"):
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
        return Response(content=content, media_type="text/plain")
    
    content_type, _ = mimetypes.guess_type(file_path)
    if not content_type:
        content_type = "application/octet-stream"
        
    return FileResponse(file_path, media_type=content_type)
