from typing import Any, Optional
from torch import bfloat16
import torch
import transformers
from langchain.llms.base import LLM

from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
)

from auto_gptq import AutoGPTQForCausalLM

def from_model_id(
    model_id: str,
    model_kwargs: Optional[dict] = None,
    pipeline_kwargs: Optional[dict] = None,
    **kwargs: Any,
) -> LLM:

    _model_kwargs = model_kwargs or {}
    _pipeline_kwargs = pipeline_kwargs or {}
    
    tokenizer = transformers.AutoTokenizer.from_pretrained(model_id, **_model_kwargs)

    bnb_config = transformers.BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type='nf4',
        bnb_4bit_use_double_quant=True,
        bnb_4bit_compute_dtype=bfloat16
    )
    model = transformers.AutoModelForCausalLM.from_pretrained(
        model_id,
        trust_remote_code=True,
        quantization_config=bnb_config,
        device_map='auto',
        **_model_kwargs
    )
    
    pipeline = transformers.pipeline(
    model=model, 
    tokenizer=tokenizer,
    return_full_text=True,  # langchain expects the full text
    task='text-generation',
    #temperature=0.0,  # 'randomness' of outputs, 0.0 is the min and 1.0 the max
    repetition_penalty=1.1,  # without this output begins repeating
    # device=device,
    model_kwargs=_model_kwargs,
    **_pipeline_kwargs,
)
    return pipeline


def load_quantized_model_qptq(model_id, model_basename, device_type, logging):
    """
    Load a GPTQ quantized model using AutoGPTQForCausalLM.

    This function loads a quantized model that ends with GPTQ and may have variations
    of .no-act.order or .safetensors in their HuggingFace repo.

    Notes:
    - The function checks for the ".safetensors" ending in the model_basename and removes it if present.
    """

    # The code supports all huggingface models that ends with GPTQ and have some variation
    # of .no-act.order or .safetensors in their HF repo.
    print("Using AutoGPTQForCausalLM for quantized models")

    if ".safetensors" in model_basename:
        # Remove the ".safetensors" ending if present
        model_basename = model_basename.replace(".safetensors", "")

    tokenizer = AutoTokenizer.from_pretrained(model_id, use_fast=True)
    print("Tokenizer loaded")

    model = AutoGPTQForCausalLM.from_quantized(
        model_id,
        model_basename=model_basename,
        use_safetensors=True,
        trust_remote_code=True,
        device_map="auto",
        use_triton=False,
        quantize_config=None,
    )
    return model, tokenizer


def load_full_model(model_id):

    print("Using AutoModelForCausalLM for full models")
    tokenizer = AutoTokenizer.from_pretrained(model_id, cache_dir="./models/")
    print("Tokenizer loaded")
    model = AutoModelForCausalLM.from_pretrained(
        model_id,
        device_map="auto",
        torch_dtype=torch.float16,
        low_cpu_mem_usage=True,
        cache_dir="./models",
        trust_remote_code=True, # set these if you are using NVIDIA GPU
        load_in_4bit=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_compute_dtype=torch.float16,
        # max_memory={0: "15GB"} # Uncomment this line with you encounter CUDA out of memory errors
    )
    model.tie_weights()
    return model, tokenizer