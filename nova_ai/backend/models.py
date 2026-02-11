from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    chats = relationship("Chat", back_populates="user")
    images = relationship("Image", back_populates="user")
    video_logs = relationship("VideoLog", back_populates="user")
    otps = relationship("OTP", back_populates="user")

class OTP(Base):
    __tablename__ = "otps"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    otp_code = Column(String, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    expires_at = Column(DateTime(timezone=True))
    is_used = Column(Boolean, default=False)
    attempts = Column(Integer, default=0)

    user = relationship("User", back_populates="otps")

class Chat(Base):
    __tablename__ = "chats"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    role = Column(String)  # 'user' or 'assistant'
    content = Column(Text)
    model = Column(String, default="tinyllama")
    timestamp = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="chats")

class Image(Base):
    __tablename__ = "images"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    prompt = Column(String)
    image_path = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    parameters = Column(Text) # JSON string for params

    user = relationship("User", back_populates="images")

class VideoLog(Base):
    __tablename__ = "video_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    command = Column(String)
    input_file = Column(String)
    output_file = Column(String)
    status = Column(String) # 'processing', 'completed', 'failed'
    timestamp = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="video_logs")
