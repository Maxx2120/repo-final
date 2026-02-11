from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, BackgroundTasks
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import User, VideoLog
from ..services import video_service
from .auth import get_current_user
from fastapi.concurrency import run_in_threadpool
import shutil
import os
import uuid
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/video", tags=["video"])

@router.post("/process")
async def process_video(
    prompt: str = Form(...),
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        # Save uploaded file
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        upload_dir = os.path.join(base_dir, "static", "videos", "uploads")
        os.makedirs(upload_dir, exist_ok=True)
        file_ext = os.path.splitext(file.filename)[1]
        if not file_ext:
            file_ext = ".mp4" # Default extension if missing

        filename = f"{uuid.uuid4()}{file_ext}"
        filepath = os.path.join(upload_dir, filename)

        with open(filepath, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # Process video synchronously (blocking but safe in threadpool)
        log = await run_in_threadpool(video_service.process_video, db, current_user, filepath, prompt)

        if log.status == "failed":
            raise HTTPException(status_code=500, detail="Video processing failed")

        return {"output_url": log.output_file, "status": log.status, "id": log.id}
    except Exception as e:
        logger.error(f"Video processing error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/history")
def get_history(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return db.query(VideoLog).filter(VideoLog.user_id == current_user.id).order_by(VideoLog.timestamp.desc()).all()
