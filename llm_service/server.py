import logging
import os
import time
from contextlib import asynccontextmanager

import torch
from fastapi import FastAPI
from pydantic import BaseModel
from pydantic_settings import BaseSettings
from transformers import AutoModelForCausalLM, AutoTokenizer

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger("llm_service")


class LLMSettings(BaseSettings):
    MODEL_NAME: str = "Qwen/Qwen2.5-0.5B-Instruct"
    DEVICE: str = "cpu"
    TORCH_DTYPE: str = "float32"
    MAX_TOKENS: int = 512
    TEMPERATURE: float = 0.7

    class Config:
        env_file = os.path.join(os.path.dirname(__file__), "..", ".env")
        extra = "ignore"


llm_settings = LLMSettings()

DTYPE_MAP = {"float32": torch.float32, "float16": torch.float16, "bfloat16": torch.bfloat16}

tokenizer = None
model = None
model_loaded = False


def load_model():
    global tokenizer, model, model_loaded
    if tokenizer is None:
        print(f"[llm_service] Loading model {llm_settings.MODEL_NAME} on {llm_settings.DEVICE}...")
        tokenizer = AutoTokenizer.from_pretrained(
            llm_settings.MODEL_NAME, trust_remote_code=True, local_files_only=True
        )
        dtype = DTYPE_MAP.get(llm_settings.TORCH_DTYPE, torch.float32)
        model = AutoModelForCausalLM.from_pretrained(
            llm_settings.MODEL_NAME,
            dtype=dtype,
            device_map=llm_settings.DEVICE,
            trust_remote_code=True,
            local_files_only=True,
        )
        model.eval()
        model_loaded = True
        print("[llm_service] Model loaded successfully")
    return tokenizer, model


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        load_model()
    except Exception as e:
        print(f"[llm_service] Failed to load model during startup: {e}")
        import traceback
        traceback.print_exc()
    yield


app = FastAPI(title="AIMSA LLM Service", version="0.1.0")


class GenerateRequest(BaseModel):
    prompt: str
    max_tokens: int = 512
    temperature: float = 0.7


class GenerateResponse(BaseModel):
    text: str
    tokens: int
    latency: float


@app.post("/generate", response_model=GenerateResponse)
async def generate(req: GenerateRequest):
    tok, mdl = load_model()
    start = time.time()

    messages = [{"role": "user", "content": req.prompt}]
    text = tok.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
    inputs = tok(text, return_tensors="pt").to(mdl.device)

    with torch.no_grad():
        outputs = mdl.generate(
            **inputs,
            max_new_tokens=req.max_tokens,
            temperature=req.temperature,
            do_sample=req.temperature > 0,
            pad_token_id=tok.eos_token_id,
        )

    generated_ids = outputs[0][inputs["input_ids"].shape[1]:]
    response_text = tok.decode(generated_ids, skip_special_tokens=True)
    latency = time.time() - start

    return GenerateResponse(text=response_text, tokens=len(generated_ids), latency=latency)


@app.get("/health")
async def health():
    return {
        "status": "healthy" if model_loaded else "loading",
        "model": llm_settings.MODEL_NAME,
        "device": llm_settings.DEVICE,
        "model_loaded": model_loaded,
    }
