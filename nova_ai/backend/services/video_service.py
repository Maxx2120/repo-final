import subprocess
import os
import uuid
import logging
from ..models import VideoLog
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

FILTER_MAP = {
    "vintage": "curves=vintage",
    "black and white": "hue=s=0",
    "grayscale": "hue=s=0",
    "increase brightness": "eq=brightness=0.3",
    "decrease brightness": "eq=brightness=-0.3",
    "cinematic": "crop=iw:ih-140,eq=saturation=1.2:contrast=1.2", # basic cinematic look
    "slow motion": "setpts=2.0*PTS",
    "fast motion": "setpts=0.5*PTS",
    "blur": "boxblur=10:1",
    "sharpen": "unsharp=5:5:1.0:5:5:0.0",
}

def parse_prompt(prompt: str):
    filters = []
    prompt = prompt.lower()
    for key, value in FILTER_MAP.items():
        if key in prompt:
            filters.append(value)

    if not filters:
        return None
    return ",".join(filters)

def process_video(db: Session, user, input_file_path: str, prompt: str):
    # Ensure output directory exists
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    output_dir = os.path.join(base_dir, "static", "videos")
    os.makedirs(output_dir, exist_ok=True)

    output_filename = f"{uuid.uuid4()}.mp4"
    output_path = os.path.join(output_dir, output_filename)
    relative_path = f"/static/videos/{output_filename}"

    filter_chain = parse_prompt(prompt)

    cmd = ["ffmpeg", "-y", "-i", input_file_path]

    if filter_chain:
        cmd.extend(["-vf", filter_chain])

    cmd.extend(["-c:v", "libx264", "-c:a", "aac", output_path])

    try:
        logger.info(f"Running FFmpeg command: {' '.join(cmd)}")
        subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        status = "completed"
    except subprocess.CalledProcessError as e:
        logger.error(f"FFmpeg error: {e.stderr.decode()}")
        status = "failed"
    except FileNotFoundError:
        logger.error("FFmpeg not found. Please install FFmpeg.")
        status = "failed"

    # Log to DB
    log = VideoLog(
        user_id=user.id,
        command=prompt,
        input_file=input_file_path,
        output_file=relative_path if status == "completed" else None,
        status=status
    )
    db.add(log)
    db.commit()
    db.refresh(log)

    return log
