"""Injection classifier (Layer 2).

Loads the RoBERTa model fine-tuned on the BIPIA dataset from HuggingFace Hub
(default: DegreeJr/singkap-ai-roberta) via a transformers pipeline. Runs on GPU
(CUDA) when available, otherwise falls back to CPU.

Binary classifier: label 0 = benign/safe, 1 = malicious/injection.
"""

from functools import lru_cache

import torch
from transformers import pipeline

from app.core.config import settings

# The model's raw label ids/strings that mean "injection".
_INJECTION_LABELS = {"1", "label_1", "malicious", "injection", "unsafe"}


def get_device() -> str:
    return "cuda" if torch.cuda.is_available() else "cpu"


@lru_cache(maxsize=1)
def _get_pipeline():
    """Load the classification pipeline once and cache it."""
    device = 0 if torch.cuda.is_available() else -1
    return pipeline(
        task="text-classification",
        model=settings.hf_model_id or "DegreeJr/singkap-ai-roberta",
        device=device,
        truncation=True,
        max_length=512,
    )


def _is_injection_label(raw_label: str) -> bool:
    return raw_label.strip().lower() in _INJECTION_LABELS


def classify(content: str) -> tuple[bool, float, str]:
    """Return (is_injection, confidence, label).

    confidence is always the model's probability for the *injection* class, so a
    benign verdict with score 0.98 reports confidence ~0.02.
    """
    clf = _get_pipeline()
    result = clf(content)[0]  # {"label": ..., "score": ...}

    raw_label = str(result["label"])
    score = float(result["score"])
    is_injection = _is_injection_label(raw_label)

    # Normalize confidence to the injection class probability.
    injection_confidence = score if is_injection else 1.0 - score
    label = "injection" if is_injection else "benign"

    return is_injection, round(injection_confidence, 4), label


def warmup() -> str:
    """Load the model and run one dummy inference. Returns the active device."""
    classify("warmup")
    return get_device()
