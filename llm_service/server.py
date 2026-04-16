import time
from contextlib import asynccontextmanager

import torch
from fastapi import FastAPI
from pydantic import BaseModel
from transformers import AutoModelForCausalLM, AutoTokenizer

MODEL_NAME = "Qwen/Qwen2.5-0.5B-Instruct"

tokenizer = None
model = None


def load_model():
    global tokenizer, model
    if tokenizer is None:
        tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME, trust_remote_code=True)
        model = AutoModelForCausalLM.from_pretrained(
            MODEL_NAME,
            torch_dtype=torch.float32,
            device_map="cpu",
            trust_remote_code=True,
        )
        model.eval()
    return tokenizer, model


@asynccontextmanager
async def lifespan(app: FastAPI):
    load_model()
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
    return {"status": "healthy", "model": MODEL_NAME, "device": "cpu"}
