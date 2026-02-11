import random
import string
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import aiosmtplib
from sqlalchemy.orm import Session
from ..models import OTP, User
from ..config import settings
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def generate_otp(length=6):
    return ''.join(random.choices(string.digits, k=length))

async def send_email(email: str, subject: str, body: str):
    if not settings.MAIL_USERNAME or not settings.MAIL_PASSWORD:
        print("Email credentials not set. Skipping email send.")
        return

    message = MIMEMultipart()
    message["From"] = settings.MAIL_FROM
    message["To"] = email
    message["Subject"] = subject
    message.attach(MIMEText(body, "html"))

    try:
        await aiosmtplib.send(
            message,
            hostname=settings.MAIL_SERVER,
            port=settings.MAIL_PORT,
            start_tls=True,
            username=settings.MAIL_USERNAME,
            password=settings.MAIL_PASSWORD,
        )
    except Exception as e:
        print(f"Failed to send email: {e}")
        # In production, you might want to raise an exception or log this more formally

def create_otp(db: Session, user: User):
    otp_code = generate_otp()
    expires_at = datetime.utcnow() + timedelta(minutes=5)

    # Invalidate old unused OTPs
    old_otps = db.query(OTP).filter(OTP.user_id == user.id, OTP.is_used == False).all()
    for otp in old_otps:
        otp.is_used = True # Mark as used/invalidated

    new_otp = OTP(user_id=user.id, otp_code=otp_code, expires_at=expires_at)
    db.add(new_otp)
    db.commit()
    db.refresh(new_otp)
    return new_otp

def verify_otp(db: Session, user: User, otp_code: str, consume: bool = True):
    # Fetch the latest active OTP for the user
    otp_record = db.query(OTP).filter(
        OTP.user_id == user.id,
        OTP.is_used == False,
        OTP.expires_at > datetime.utcnow()
    ).order_by(OTP.created_at.desc()).first()

    if not otp_record:
        return False

    if otp_record.attempts >= 3:
        return False

    if otp_record.otp_code != otp_code:
        otp_record.attempts += 1
        db.commit()
        return False

    if consume:
        otp_record.is_used = True
        db.commit()

    return True
