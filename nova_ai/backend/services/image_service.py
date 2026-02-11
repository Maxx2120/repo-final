import os
import uuid
import json
import logging
from ..models import Image as DBImage
from ..config import settings
from PIL import Image as PILImage, ImageDraw

logger = logging.getLogger(__name__)

SD_PIPELINE = None
SD_AVAILABLE = False
SD_LIBRARY_PRESENT = False

try:
    import torch
    from diffusers import StableDiffusionPipeline
    SD_LIBRARY_PRESENT = True
except ImportError:
    pass

def load_model():
    global SD_PIPELINE, SD_AVAILABLE
    if SD_AVAILABLE and SD_PIPELINE:
        return

    if not SD_LIBRARY_PRESENT:
        SD_AVAILABLE = False
        return

    try:
        logger.info("Loading Stable Diffusion model...")
        model_id = settings.DIFFUSION_MODEL_ID

        # Optimize for CPU
        device = "cpu"
        if torch.cuda.is_available():
            device = "cuda"

        pipe = StableDiffusionPipeline.from_pretrained(model_id, torch_dtype=torch.float32)
        pipe = pipe.to(device)
        pipe.enable_attention_slicing()

        SD_PIPELINE = pipe
        SD_AVAILABLE = True
        logger.info("Stable Diffusion model loaded successfully.")
    except Exception as e:
        logger.error(f"Failed to load Stable Diffusion model: {e}")
        SD_AVAILABLE = False

def create_mock_image(prompt, filepath):
    img = PILImage.new('RGB', (512, 512), color = (73, 109, 137))
    d = ImageDraw.Draw(img)
    d.text((10,10), "Mock Image\n" + prompt[:50], fill=(255,255,0))
    img.save(filepath)

def generate_image(db, user, prompt: str):
    global SD_PIPELINE, SD_AVAILABLE

    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    static_dir = os.path.join(base_dir, "static")
    generated_dir = os.path.join(static_dir, "generated")

    filename = f"{uuid.uuid4()}.png"
    # Ensure directory exists
    os.makedirs(generated_dir, exist_ok=True)
    filepath = os.path.join(generated_dir, filename)
    relative_path = f"/static/generated/{filename}"

    generation_successful = False

    if SD_LIBRARY_PRESENT:
        if SD_PIPELINE is None:
            load_model()

        if SD_AVAILABLE:
            try:
                # Use fewer steps for CPU optimization
                image = SD_PIPELINE(prompt, num_inference_steps=20).images[0]
                image.save(filepath)
                generation_successful = True
            except Exception as e:
                logger.error(f"Error generating image with model: {e}")
                generation_successful = False

    if not generation_successful:
        create_mock_image(prompt, filepath)

    # Save to DB
    new_image = DBImage(
        user_id=user.id,
        prompt=prompt,
        image_path=relative_path,
        parameters=json.dumps({"model": "stable-diffusion-v1-5" if generation_successful else "mock"})
    )
    db.add(new_image)
    db.commit()
    db.refresh(new_image)

    return new_image
