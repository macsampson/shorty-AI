import base64
import requests
import os
from config import settings


# Replace the empty string with your model id below
def generate_image_baseten(prompt: str):
    model_id = "nwx1r45q"
    baseten_api_key = settings.baseten_api_key
    BASE64_PREAMBLE = "data:image/png;base64,"

    # Call model endpoint
    res = requests.post(
        f"https://model-{model_id}.api.baseten.co/production/predict",
        headers={"Authorization": f"Api-Key {baseten_api_key}"},
        json=prompt,
    )

    # Get output image
    res = res.json()
    img_b64 = res.get("result")
    img = base64.b64decode(img_b64)

    # Save the base64 string to a PNG with incremental file names in the image folder
    with open(
        f"images/baseten/SDXL-Lightning/{len(os.listdir('images/baseten/SDXL-Lightning'))}.png",
        "wb",
    ) as f:
        f.write(img)
        f.close()


generate_image_baseten()
