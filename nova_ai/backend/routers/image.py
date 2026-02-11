from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import User, Image
from ..services import image_service
from .auth import get_current_user
from pydantic import BaseModel
from fastapi.concurrency import run_in_threadpool
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/image", tags=["image"])

class ImageRequest(BaseModel):
    prompt: str

@router.post("/generate")
async def generate_image(request: ImageRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    try:
        # Run blocking image generation in threadpool
        image = await run_in_threadpool(image_service.generate_image, db, current_user, request.prompt)
        return {"image_url": image.image_path, "prompt": image.prompt, "id": image.id}
    except Exception as e:
        logger.error(f"Image generation failed: {e}")
        raise HTTPException(status_code=500, detail="Image generation failed")

@router.get("/history")
def get_history(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return db.query(Image).filter(Image.user_id == current_user.id).order_by(Image.created_at.desc()).all()
