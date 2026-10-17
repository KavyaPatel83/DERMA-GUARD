"""
src/llm/client.py — Ollama LLM client (DERMA-GUARD v4.0)

Model: qwen2.5:7b (NOT llama3 from legacy system)
Constraints (CRITICAL):
  - 30-second timeout
  - 2 retries on failure
  - Conservative fallback prompt on Stage 2 verification failure
  - temperature=0.0 for all clinical decisions
"""
from __future__ import annotations

import json
import time
import warnings
from typing import Any, Dict, Optional

import requests


class OllamaClient:
    """Ollama LLM client with mandatory timeout/retry/fallback.

    CRITICAL constraints per DERMA-GUARD spec:
    - 30-second timeout on every call
    - 2 retries with exponential backoff
    - Conservative fallback if retries exhausted
    - temperature=0.0 for all clinical decisions
    """

    DEFAULT_MODEL = "qwen2.5:7b"
    DEFAULT_TIMEOUT = 30  # seconds
    DEFAULT_MAX_RETRIES = 2
    CONSERVATIVE_SYSTEM_PROMPT = (
        "State only what is directly supported by the evidence below. "
        "Do not infer, speculate, or extrapolate. "
        "If uncertain, state that explicitly."
    )

    def __init__(
        self,
        base_url: str = "http://localhost:11434",
        model: str = DEFAULT_MODEL,
        timeout: int = DEFAULT_TIMEOUT,
        max_retries: int = DEFAULT_MAX_RETRIES,
        temperature: float = 0.0,
        max_tokens: int = 512,
    ):
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout = timeout
        self.max_retries = max_retries
        self.default_temperature = temperature
        self.default_max_tokens = max_tokens

    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        conservative: bool = False,
    ) -> str:
        """Generate a response from the LLM.

        Args:
            prompt:       user prompt
            system_prompt: optional system context
            temperature:  override default (default = 0.0 for clinical safety)
            max_tokens:   override default
            conservative: if True, uses CONSERVATIVE_SYSTEM_PROMPT as system

        Returns:
            Generated text string

        Raises:
            RuntimeError: if all retries fail (after logging)
        """
        if conservative:
            system_prompt = self.CONSERVATIVE_SYSTEM_PROMPT

        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": temperature if temperature is not None else self.default_temperature,
                "num_predict": max_tokens if max_tokens is not None else self.default_max_tokens,
            },
        }
        if system_prompt:
            payload["system"] = system_prompt

        last_error: Optional[Exception] = None
        for attempt in range(self.max_retries + 1):
            try:
                response = requests.post(
                    f"{self.base_url}/api/generate",
                    json=payload,
                    timeout=self.timeout,
                )
                response.raise_for_status()
                data = response.json()
                return str(data.get("response", ""))
            except requests.exceptions.Timeout:
                last_error = TimeoutError(
                    f"Ollama request timed out after {self.timeout}s (attempt {attempt+1})"
                )
            except requests.exceptions.ConnectionError:
                last_error = ConnectionError(
                    f"Cannot connect to Ollama at {self.base_url}. Is Ollama running?"
                )
            except Exception as e:
                last_error = e

            if attempt < self.max_retries:
                wait = 2 ** attempt  # exponential backoff: 1s, 2s
                time.sleep(wait)

        warnings.warn(f"[OllamaClient] All {self.max_retries+1} attempts failed: {last_error}")
        raise RuntimeError(f"LLM call failed after {self.max_retries+1} attempts: {last_error}")

    def generate_json(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.0,
    ) -> Dict[str, Any]:
        """Generate and parse a JSON response.

        Returns empty dict on parse failure rather than raising.
        """
        raw = self.generate(
            prompt,
            system_prompt=system_prompt,
            temperature=temperature,
        )
        # Try to extract JSON from response
        import re
        match = re.search(r'\{.*?\}', raw, re.DOTALL)
        if match:
            try:
                return json.loads(match.group())
            except json.JSONDecodeError:
                pass
        return {}

    def is_available(self) -> bool:
        """Quick health check — returns True if Ollama is reachable."""
        try:
            r = requests.get(f"{self.base_url}/api/tags", timeout=5)
            return r.status_code == 200
        except Exception:
            return False

    def ensure_model_available(self) -> bool:
        """Check if the configured model is pulled and available."""
        try:
            r = requests.get(f"{self.base_url}/api/tags", timeout=5)
            if r.status_code == 200:
                models = [m["name"] for m in r.json().get("models", [])]
                return any(self.model in m for m in models)
        except Exception:
            pass
        return False
