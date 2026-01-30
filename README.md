## YouTube Downloader API using FastAPI and yt-dlp

This project provides a simple microservice using `FastAPI` and `yt-dlp` to download YouTube audio and transcripts. It includes automatic cleanup features and a simple API for file management.

### Features
- **Audio Download**: Download high-quality m4a audio from YouTube URLs.
- **Transcript Download**: Extract English transcripts (manual or auto-generated) from YouTube videos.
- **File Serving**: Direct access to downloaded files via API.
- **Auto-Cleanup**: Automatically deletes downloaded files older than 1 hour to manage storage.
- **Dockerized**: Easy deployment using Docker and `uv`.

### Prerequisites
To run this project, you need the following dependencies installed on your system:
- Python 3.13+
- FFmpeg
- UV (https://github.com/astral-sh/uv)

### Standalone Installation Guide
1. Clone the repository
   ```shell
   git clone https://github.com/rpfilomeno/yt-dl-fast-api.git
   ```
2. Create a virtual environment and install dependencies
   ```shell
   uv venv
   uv sync
   source .venv/bin/activate
   ```
3. Set Environment Variables (optional)
   ```shell
   export DOWNLOAD_PATH="./downloads"
   export PORT=8000
   export FFMPEG_LOCATION="/usr/bin/ffmpeg"
   ```
4. Start the FastAPI server:
   ```shell
   uvicorn main:app --host 0.0.0.0 --reload --port $PORT
   ```

### Docker Installation Guide
1. Build the docker image
   ```shell
   docker build -t yt-dl-fast-api-server .
   ```
2. Run the application
   ```shell
   docker run \
         --name yt-dl-fast-api-server \
         -p 8000:8000 \
         -v $(pwd)/downloads:/workspaces/downloads \
         -d yt-dl-fast-api-server
   ```
3. Check the Logs
   ```shell
   docker logs yt-dl-fast-api-server -f
   ```

### API(s)
- **Health Check**: `GET /`
- **Download Audio**: `GET /api/download/{url:path}`
  - Downloads audio as `.m4a`.
- **Download Transcript**: `GET /api/transcript/{url:path}`
  - Downloads English subtitles as `.srt` or `.vtt`.
- **List Files**: `GET /api/files`
  - Returns a list of all files in the download directory.
- **Get File**: `GET /api/files/{filename}`
  - Retrieves a specific file. `.vtt` files are returned as plain text.
- **Swagger Documentation**: `GET /docs`

### Acknowledgments
- [FastAPI](https://fastapi.tiangolo.com/)
- [yt-dlp](https://github.com/yt-dlp/yt-dlp)
