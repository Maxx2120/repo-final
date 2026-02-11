from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import User
from ..services import otp_service
from pydantic import BaseModel
from passlib.context import CryptContext
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/otp", tags=["otp"])

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_password_hash(password):
    return pwd_context.hash(password)

class ForgotPasswordRequest(BaseModel):
    email: str

class VerifyOTPRequest(BaseModel):
    email: str
    otp: str

class ResetPasswordRequest(BaseModel):
    email: str
    otp: str
    new_password: str

@router.post("/forgot-password")
async def forgot_password(request: ForgotPasswordRequest, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == request.email).first()
    # Don't reveal user existence for security, but log it
    if not user:
        logger.info(f"Forgot password requested for non-existent email: {request.email}")
        return {"message": "If account exists, an OTP has been sent."}

    otp = otp_service.create_otp(db, user)

    # Send email in background
    background_tasks.add_task(
        otp_service.send_email,
        request.email,
        "NOVA AI - Password Reset OTP",
        f"Your OTP is: <b>{otp.otp_code}</b>. It expires in 5 minutes."
    )

    return {"message": "OTP sent to email"}

@router.post("/verify")
def verify_otp(request: VerifyOTPRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == request.email).first()
    if not user:
        raise HTTPException(status_code=400, detail="Invalid request")

    # Check if OTP is valid but do NOT consume it yet.
    is_valid = otp_service.verify_otp(db, user, request.otp, consume=False)

    if not is_valid:
        raise HTTPException(status_code=400, detail="Invalid or expired OTP")

    return {"message": "OTP verified successfully"}

@router.post("/reset-password")
def reset_password(request: ResetPasswordRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == request.email).first()
    if not user:
        raise HTTPException(status_code=400, detail="User not found")

    # Verify AND Consume OTP
    is_valid = otp_service.verify_otp(db, user, request.otp, consume=True)

    if not is_valid:
        raise HTTPException(status_code=400, detail="Invalid or expired OTP")

    # Reset password
    hashed_password = get_password_hash(request.new_password)
    user.hashed_password = hashed_password
    db.commit()

    return {"message": "Password reset successfully"}
