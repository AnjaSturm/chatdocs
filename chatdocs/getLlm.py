from typing import Any, Optional
from torch import cuda, bfloat16
import transformers
from langchain.llms.base import LLM


# model_id = 'meta-llama/Llama-2-13b-chat-hf'

# device = f'cuda:{cuda.current_device()}' if cuda.is_available() else 'cpu'

# # set quantization configuration to load large model with less GPU memory
# # this requires the `bitsandbytes` library
# bnb_config = transformers.BitsAndBytesConfig(
#     load_in_4bit=True,
#     bnb_4bit_quant_type='nf4',
#     bnb_4bit_use_double_quant=True,
#     bnb_4bit_compute_dtype=bfloat16
# )

# # begin initializing HF items, need auth token for these
# hf_auth = 'HF_AUTH_TOKEN'
# model_config = transformers.AutoConfig.from_pretrained(
#     model_id,
#     use_auth_token=hf_auth
# )

# model = transformers.AutoModelForCausalLM.from_pretrained(
#     model_id,
#     trust_remote_code=True,
#     config=model_config,
#     quantization_config=bnb_config,
#     device_map='auto',
#     use_auth_token=hf_auth
# )
# model.eval()
# print(f"Model loaded on {device}")
     



# tokenizer = transformers.AutoTokenizer.from_pretrained(
#     model_id,
#     use_auth_token=hf_auth
# )
     


# generate_text = transformers.pipeline(
#     model=model, tokenizer=tokenizer,
#     return_full_text=True,  # langchain expects the full text
#     task='text-generation',
#     # we pass model parameters here too
#     temperature=0.0,  # 'randomness' of outputs, 0.0 is the min and 1.0 the max
#     max_new_tokens=512,  # mex number of tokens to generate in the output
#     repetition_penalty=1.1  # without this output begins repeating
# )



# # res = generate_text("Explain to me the difference between nuclear fission and fusion.")
# # print(res[0]["generated_text"])


# return generate_text
     
     
     
# class HuggingFacePipelineAnja(LLM):
     
#     @classmethod
def from_model_id(
    # cls,
    model_id: str,
    #device: int = -1,
    model_kwargs: Optional[dict] = None,
    pipeline_kwargs: Optional[dict] = None,
    #**kwargs: Any,
) -> LLM:

   # device = f'cuda:{cuda.current_device()}' if cuda.is_available() else 'cpu'

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
    # we pass model parameters here too
    #temperature=0.0,  # 'randomness' of outputs, 0.0 is the min and 1.0 the max
    repetition_penalty=1.1,  # without this output begins repeating
    # device=device,
    model_kwargs=_model_kwargs,
    **_pipeline_kwargs,
)

        # return cls(
        #     pipeline=pipeline,
        #     model_id=model_id,
        #     model_kwargs=_model_kwargs,
        #     pipeline_kwargs=_pipeline_kwargs,
        #     **kwargs,
        # )
    return pipeline