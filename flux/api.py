import torch
from diffusers import FluxPipeline, FluxTransformer2DModel
import datetime
import fastapi
from io import BytesIO
import base64

from schemas.generate_image_request import GenerateImageRequest

app = fastapi.FastAPI()





# get the current date and time 
current_time = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

# initialize the FluxPipeline at the start of the app
# pipe = FluxPipeline.from_pretrained("black-forest-labs/FLUX.1-schnell", torch_dtype=torch.bfloat16)
class FLUXloader:
    _pipe = None

    @classmethod
    def get_pipe(cls):
        if cls._pipe is None:
            cls._pipe = cls._load_model()
        return cls._pipe

    @classmethod
    def _load_model(cls):

        pipe  = FluxPipeline.from_pretrained("black-forest-labs/FLUX.1-schnell", torch_dtype=torch.bfloat16, cache_dir="/app/models")

        # pipe = FluxPipeline.from_pretrained("argmaxinc/mlx-FLUX.1-schnell-4bit-quantized", torch_dtype=torch.bfloat16, cache_dir="/app/models")

        return pipe


@app.post("/generate_image")
async def generate_image(request: GenerateImageRequest):
    print("Generating FLUX image with prompt: ", request.prompt)

    # Check if CUDA is available
    # device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

    pipe = FLUXloader.get_pipe()
    # pipe.enable_model_cpu_offload()
    pipe.enable_sequential_cpu_offload() #save some VRAM if you are using a GPU

    image = pipe(
        request.prompt,
        guidance_scale=request.guidance_scale,
        output_type="pil",
        num_inference_steps=request.num_inference_steps, #use a larger number if you are using [dev]
        max_sequence_length=request.max_sequence_length,
        # generator=torch.Generator("cuda")
    ).images[0]

    with BytesIO() as buffered:
        image.save(buffered, format="PNG")
        img_str = base64.b64encode(buffered.getvalue()).decode("utf-8")

    # save the image with the current date and time in the filename
    # image.save(f"flux-schnell_{current_time}.png")

    return {"image": img_str} 


@app.post("/unload_model")
async def unload_model():
    FLUXloader._pipe = None
    torch.cuda.empty_cache()
    print("Flux model unloaded")
    return {"message": "Model unloaded"}        