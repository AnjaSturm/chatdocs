from typing import Any, Callable, Dict, Optional

from langchain.llms import HuggingFacePipeline
from langchain.llms.base import LLM

from .getLlm import from_model_id, load_quantized_model_qptq

def get_llm(
    config: Dict[str, Any],
    *,
    callback: Optional[Callable[[str], None]] = None,
) -> LLM:
    config["model_id"] = config["model"]
    # pipeline = load_quantized_model_qptq(**config)
    pipeline = from_model_id(**config)
    llm = HuggingFacePipeline(pipeline=pipeline)
    return llm


