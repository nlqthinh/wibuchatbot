import time
import torch
from diffusers import DiffusionPipeline, EulerDiscreteScheduler

# Setup pipeline
scheduler = EulerDiscreteScheduler.from_pretrained("John6666/baxl-v3-sdxl", subfolder="scheduler")
pipeline = DiffusionPipeline.from_pretrained(
    "John6666/baxl-v3-sdxl",
    scheduler=scheduler,
    use_safetensors=True
)

device = "cuda" if torch.cuda.is_available() else "cpu"
pipeline.to(device)

def generate_image(prompt: str) -> str:
    """
    Creates an image based on the specified prompt using DiffusionPipeline.
    :param prompt: The prompt used to generate the image (must be in English).
    :return: Path to the generated image file.
    """
    image = pipeline(
        prompt=prompt,
        negative_prompt="ugly, deformed, disfigured, poor details, bad anatomy, low quality, worst quality",
        num_inference_steps=30
    ).images[0]

    # Save image file
    file_name = f"image_{int(time.time())}.png"
    image.save(file_name)
    return file_name