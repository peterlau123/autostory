from huggingface_hub import InferenceClient
from PIL import Image

client = InferenceClient(
    provider="hf-inference",
    api_key="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",
)

# output is a PIL.Image object
print("🚀 Start image generation ...")
image = client.text_to_image(
    "Astronaut riding a horse",
    model="stabilityai/stable-diffusion-3.5-large-turbo",
)
print("✅ End image generation ...")

image.save("test.jpg")
