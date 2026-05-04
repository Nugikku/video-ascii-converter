import os
import uuid
import asyncio
import pathlib
from fastapi import FastAPI, UploadFile, File, HTTPException, BackgroundTasks, Request
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from converter import convert_video_to_ascii

app = FastAPI(title="ASCII Video Converter")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR = pathlib.Path(__file__).parent.parent
FRONTEND_DIR = BASE_DIR / "frontend"

# Mount folder css dan js sesuai struktur folder kamu yang sudah ada
app.mount("/css", StaticFiles(directory=str(FRONTEND_DIR / "css")), name="css")
app.mount("/js",  StaticFiles(directory=str(FRONTEND_DIR / "js")),  name="js")

UPLOAD_DIR = "temp/uploads"
OUTPUT_DIR = "temp/outputs"
MAX_DURATION = 30
MAX_FILE_SIZE = 100 * 1024 * 1024

jobs: dict = {}

@app.get("/")
async def root():
    return FileResponse(str(FRONTEND_DIR / "index.html"))


@app.post("/api/upload")
async def upload_video(file: UploadFile = File(...)):
    allowed = ["video/mp4", "video/quicktime", "video/x-msvideo", "video/webm"]
    if file.content_type not in allowed:
        raise HTTPException(400, "Format tidak didukung. Gunakan MP4, MOV, AVI, atau WebM.")

    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(400, "Ukuran file maksimal 100MB.")

    job_id = str(uuid.uuid4())
    ext = os.path.splitext(file.filename)[1] or ".mp4"
    input_path = os.path.join(UPLOAD_DIR, f"{job_id}{ext}")

    with open(input_path, "wb") as f:
        f.write(content)

    import cv2
    cap = cv2.VideoCapture(input_path)
    fps = cap.get(cv2.CAP_PROP_FPS)
    frame_count = cap.get(cv2.CAP_PROP_FRAME_COUNT)
    cap.release()

    if fps > 0:
        duration = frame_count / fps
        if duration > MAX_DURATION:
            os.remove(input_path)
            raise HTTPException(400, f"Durasi video maksimal {MAX_DURATION} detik. Video kamu {duration:.0f} detik.")

    jobs[job_id] = {
        "status": "uploaded",
        "progress": 0,
        "input_path": input_path,
        "output_path": None,
        "error": None,
        "filename": file.filename,
    }
    return {"job_id": job_id, "message": "Upload berhasil"}


@app.post("/api/convert-settings/{job_id}")
async def start_conversion(
    job_id: str,
    background_tasks: BackgroundTasks,
    char_width: int = 100,
    colored: bool = True,
    output_fps: int = 15,
):
    if job_id not in jobs:
        raise HTTPException(404, "Job tidak ditemukan.")
    job = jobs[job_id]
    if job["status"] in ["processing", "done"]:
        raise HTTPException(400, "Job sudah diproses.")

    jobs[job_id]["status"] = "processing"
    jobs[job_id]["progress"] = 0

    output_path = os.path.join(OUTPUT_DIR, f"{job_id}_ascii.mp4")
    jobs[job_id]["output_path"] = output_path

    background_tasks.add_task(
        run_conversion,
        job_id=job_id,
        input_path=job["input_path"],
        output_path=output_path,
        char_width=char_width,
        colored=colored,
        output_fps=output_fps,
    )
    return {"job_id": job_id, "message": "Konversi dimulai"}


async def run_conversion(job_id, input_path, output_path, char_width, colored, output_fps):
    try:
        def progress_callback(pct):
            jobs[job_id]["progress"] = pct

        await asyncio.get_event_loop().run_in_executor(
            None,
            convert_video_to_ascii,
            input_path,
            output_path,
            char_width,
            colored,
            output_fps,
            progress_callback,
        )
        jobs[job_id]["status"] = "done"
        jobs[job_id]["progress"] = 100
    except Exception as e:
        jobs[job_id]["status"] = "error"
        jobs[job_id]["error"] = str(e)
        print(f"[ERROR] Job {job_id}: {e}")


@app.get("/api/status/{job_id}")
async def get_status(job_id: str):
    if job_id not in jobs:
        raise HTTPException(404, "Job tidak ditemukan.")
    job = jobs[job_id]
    return {
        "job_id": job_id,
        "status": job["status"],
        "progress": job["progress"],
        "error": job.get("error"),
    }


@app.get("/api/stream/{job_id}")
async def stream_video(job_id: str, request: Request):
    """Stream video dengan Range Request support untuk preview browser"""
    if job_id not in jobs:
        raise HTTPException(404, "Job tidak ditemukan.")
    job = jobs[job_id]
    if job["status"] != "done":
        raise HTTPException(400, "Konversi belum selesai.")
    output_path = job["output_path"]
    if not os.path.exists(output_path):
        raise HTTPException(404, "File tidak ditemukan.")

    file_size = os.path.getsize(output_path)
    range_header = request.headers.get("range")

    if range_header:
        ranges = range_header.replace("bytes=", "").split("-")
        start = int(ranges[0])
        end = int(ranges[1]) if ranges[1] else file_size - 1
        chunk_size = end - start + 1

        def iter_range():
            with open(output_path, "rb") as f:
                f.seek(start)
                remaining = chunk_size
                while remaining > 0:
                    data = f.read(min(65536, remaining))
                    if not data:
                        break
                    remaining -= len(data)
                    yield data

        return StreamingResponse(
            iter_range(),
            status_code=206,
            media_type="video/mp4",
            headers={
                "Content-Range": f"bytes {start}-{end}/{file_size}",
                "Accept-Ranges": "bytes",
                "Content-Length": str(chunk_size),
            }
        )

    def iter_full():
        with open(output_path, "rb") as f:
            while chunk := f.read(65536):
                yield chunk

    return StreamingResponse(
        iter_full(),
        media_type="video/mp4",
        headers={
            "Accept-Ranges": "bytes",
            "Content-Length": str(file_size),
        }
    )


@app.get("/api/download/{job_id}")
async def download_result(job_id: str):
    if job_id not in jobs:
        raise HTTPException(404, "Job tidak ditemukan.")
    job = jobs[job_id]
    if job["status"] != "done":
        raise HTTPException(400, "Konversi belum selesai.")
    output_path = job["output_path"]
    if not os.path.exists(output_path):
        raise HTTPException(404, "File output tidak ditemukan.")
    original_name = os.path.splitext(job["filename"])[0]
    return FileResponse(
        output_path,
        media_type="video/mp4",
        filename=f"{original_name}_ascii.mp4",
    )


@app.delete("/api/cleanup/{job_id}")
async def cleanup_job(job_id: str):
    if job_id not in jobs:
        raise HTTPException(404, "Job tidak ditemukan.")
    job = jobs[job_id]
    for path in [job.get("input_path"), job.get("output_path")]:
        if path and os.path.exists(path):
            os.remove(path)
    preview = os.path.join(OUTPUT_DIR, f"{job_id}_preview.jpg")
    if os.path.exists(preview):
        os.remove(preview)
    del jobs[job_id]
    return {"message": "Job dihapus"}
