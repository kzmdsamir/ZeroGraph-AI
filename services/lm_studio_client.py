"""
ZeroGraph AI — LM Studio Integration Client
100% Local, Air-gapped OpenAI-compatible LLM client abstraction.
Handles health checks, URL sanitization, structured JSON response enforcement, retries, and model auto-detection.
Developer: kzsamir
"""

import json
import logging
import re
import time
import requests

from config import Config, sanitize_lm_studio_url

logger = logging.getLogger(__name__)


class LMStudioError(Exception):
    """Custom exception for LM Studio API errors."""
    pass


class LMStudioClient:
    """Client for local LM Studio inference server."""

    def __init__(self, base_url=None, model_name=None, timeout=None):
        raw_url = base_url or Config.LM_STUDIO_BASE_URL
        self.base_url = sanitize_lm_studio_url(raw_url)
        self.model_name = model_name or Config.LLM_MODEL
        self.timeout = timeout or Config.LLM_TIMEOUT
        self.chat_endpoint = f"{self.base_url}/chat/completions"
        self.models_endpoint = f"{self.base_url}/models"

    def check_health(self):
        """Check if local LM Studio instance is reachable and model is loaded."""
        try:
            resp = requests.get(self.models_endpoint, timeout=5)
            if resp.status_code == 200:
                data = resp.json()
                models = [m.get("id") for m in data.get("data", [])]
                active_model = models[0] if models else self.model_name
                return {
                    "online": True,
                    "endpoint": self.base_url,
                    "model_configured": active_model,
                    "available_models": models,
                    "status_message": "Local Core Online"
                }
            return {
                "online": False,
                "endpoint": self.base_url,
                "status_message": f"LM Studio returned status {resp.status_code}"
            }
        except Exception as e:
            return {
                "online": False,
                "endpoint": self.base_url,
                "status_message": "Local LLM unavailable. Please start LM Studio local server and load a model."
            }

    def _get_active_model(self):
        """Fetch the currently loaded model ID from LM Studio if available."""
        try:
            resp = requests.get(self.models_endpoint, timeout=3)
            if resp.status_code == 200:
                data = resp.json()
                models = [m.get("id") for m in data.get("data", []) if m.get("id")]
                if models:
                    return models[0]
        except Exception:
            pass
        return self.model_name

    def generate_json(self, system_prompt: str, user_prompt: str, temperature: float = 0.2, max_retries: int = 3):
        """
        Request strict JSON output from local LM Studio.
        Includes automatic retry and JSON repair logic.
        """
        headers = {"Content-Type": "application/json"}
        active_model = self._get_active_model()

        payload = {
            "model": active_model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "temperature": temperature,
            "stream": False,
            "response_format": {"type": "json_object"}
        }

        start_time = time.time()
        response_text = None
        last_error = None

        for attempt in range(1, max_retries + 1):
            try:
                logger.info("Calling local LM Studio (%s) at %s (attempt %d/%d)...", active_model, self.chat_endpoint, attempt, max_retries)
                resp = requests.post(self.chat_endpoint, headers=headers, json=payload, timeout=self.timeout)
                
                # Fallback if server doesn't support response_format: json_object
                if resp.status_code in (400, 422, 501) and "response_format" in payload:
                    logger.warning("LM Studio endpoint status %d; retrying without response_format.", resp.status_code)
                    payload.pop("response_format", None)
                    resp = requests.post(self.chat_endpoint, headers=headers, json=payload, timeout=self.timeout)

                resp.raise_for_status()
                data = resp.json()
                response_text = data["choices"][0]["message"]["content"]
                duration = time.time() - start_time

                # Extract and parse JSON
                parsed_json = self._extract_json(response_text)
                
                return {
                    "success": True,
                    "data": parsed_json,
                    "raw_text": response_text,
                    "duration_seconds": round(duration, 2),
                    "model_used": active_model,
                    "attempt": attempt
                }

            except requests.exceptions.RequestException as exc:
                last_error = f"HTTP error ({self.chat_endpoint}): {exc}"
                logger.warning("LM Studio request failed: %s", exc)
                time.sleep(1.5 * attempt)
            except LMStudioError as exc:
                last_error = f"JSON parsing error: {exc}"
                logger.warning("Failed to extract JSON from response: %s", exc)
                if attempt < max_retries:
                    payload["messages"].append({"role": "assistant", "content": response_text or ""})
                    payload["messages"].append({
                        "role": "user", 
                        "content": "CRITICAL REPAIR: Your previous response was invalid JSON. Return ONLY a valid JSON object matching the required schema. No Markdown code fences."
                    })
                time.sleep(1.0)

        duration = time.time() - start_time
        return {
            "success": False,
            "error": last_error or "Unknown error calling local LLM",
            "raw_text": response_text,
            "duration_seconds": round(duration, 2),
            "model_used": active_model
        }

    def _extract_json(self, text: str):
        """Clean markdown codeblocks and parse JSON object robustly."""
        if not text or not text.strip():
            raise LMStudioError("Empty text received from model")

        cleaned = re.sub(r"^```(?:json)?\s*|\s*```$", "", text.strip(), flags=re.IGNORECASE | re.MULTILINE).strip()

        # Direct JSON parse attempt
        try:
            return json.loads(cleaned)
        except json.JSONDecodeError:
            pass

        # Brace matching recovery
        start_idx = cleaned.find('{')
        end_idx = cleaned.rfind('}')
        if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
            substring = cleaned[start_idx : end_idx + 1]
            try:
                return json.loads(substring)
            except json.JSONDecodeError as exc:
                raise LMStudioError(f"Invalid JSON inside braces: {exc}")

        raise LMStudioError("No valid JSON object found in model output")
