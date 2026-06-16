"""
llm_providers.py — Abstraksi multi-provider LLM.

Menyediakan SATU antarmuka seragam (`LLMProvider.chat_json`) di atas
beberapa penyedia LLM, sehingga sistem bisa berganti penyedia hanya
dengan mengubah variabel lingkungan `LLM_PROVIDER` di file .env — tanpa
menyentuh logika rule engine maupun frontend.

Penyedia yang didukung (pilih lewat LLM_PROVIDER):
  groq      → Groq            (llama-3.3-70b-versatile)  env: GROQ_API_KEY
  openai    → OpenAI/ChatGPT  (gpt-4o-mini)              env: OPENAI_API_KEY
  gemini    → Google Gemini   (gemini-2.0-flash)         env: GEMINI_API_KEY
  claude    → Anthropic Claude(claude-3-5-haiku-latest)  env: ANTHROPIC_API_KEY
  deepseek  → DeepSeek        (deepseek-chat)            env: DEEPSEEK_API_KEY

Model default tiap penyedia bisa ditimpa lewat LLM_MODEL.

Semua SDK diimpor secara lazy (di dalam method), sehingga aplikasi tetap
jalan walau hanya sebagian SDK yang terpasang. SDK yang belum terpasang
baru memunculkan error (dengan petunjuk `pip install`) ketika penyedia
itu benar-benar dipilih.

Author : Kelompok AI Code Review Tutor
Course : Kecerdasan Buatan, Semester Genap 2025/2026
Penanggung jawab modul ini: Habel Mangopo
"""

import os
from abc import ABC, abstractmethod
from typing import Optional

from dotenv import load_dotenv

# Muat .env saat modul diimpor agar resolve_provider() bisa dipanggil
# mandiri (mis. dari endpoint /api/llm) tanpa bergantung urutan import.
load_dotenv()


# ============================================================
# Exception ternormalisasi
# ------------------------------------------------------------
# Tiap penyedia punya tipe error sendiri-sendiri. Provider di bawah
# menerjemahkannya ke salah satu exception berikut agar pemanggil
# (llm_explainer) cukup menangani satu set exception yang sama.
# ============================================================

class ProviderError(Exception):
    """Error umum/tak terduga dari penyedia LLM."""


class ProviderRateLimit(ProviderError):
    """Kuota/rate limit penyedia habis (mis. HTTP 429)."""


class ProviderAuthError(ProviderError):
    """API key salah / tidak punya akses (HTTP 401/403)."""


class ProviderConnectionError(ProviderError):
    """Gagal menghubungi server penyedia (jaringan)."""


class ProviderNotInstalled(ProviderError):
    """SDK penyedia belum terpasang (perlu `pip install`)."""


# ============================================================
# Base class
# ============================================================

class LLMProvider(ABC):
    """Antarmuka seragam untuk satu penyedia LLM."""

    name: str = ""            # kunci internal (mis. "groq")
    label: str = ""           # nama tampilan (mis. "Groq")
    env_key: str = ""         # nama env var untuk API key
    default_model: str = ""   # model default bila LLM_MODEL kosong

    def __init__(self, api_key: str, model: Optional[str] = None):
        self.api_key = api_key
        self.model = (model or "").strip() or self.default_model

    @abstractmethod
    def chat_json(self, system_prompt: str, user_prompt: str) -> str:
        """Kirim prompt, kembalikan teks respons mentah (diharapkan JSON).

        Raises:
            ProviderRateLimit / ProviderAuthError / ProviderConnectionError /
            ProviderNotInstalled / ProviderError — sudah ternormalisasi.
        """
        raise NotImplementedError


# ============================================================
# Provider berbasis SDK kompatibel-OpenAI (OpenAI & DeepSeek)
# ------------------------------------------------------------
# OpenAI dan DeepSeek sama-sama memakai paket `openai` dan endpoint
# chat.completions yang identik; DeepSeek hanya beda base_url.
# ============================================================

class _OpenAICompatProvider(LLMProvider):
    base_url: Optional[str] = None   # None → endpoint default OpenAI

    def chat_json(self, system_prompt: str, user_prompt: str) -> str:
        try:
            import openai
            from openai import OpenAI
        except ImportError as e:
            raise ProviderNotInstalled(
                f"Paket 'openai' belum terpasang untuk penyedia '{self.name}'. "
                "Jalankan: pip install openai"
            ) from e

        # max_retries=0 → fail-fast, tidak menggantung 30-60 detik saat rate limit
        client = OpenAI(api_key=self.api_key, base_url=self.base_url, max_retries=0)
        try:
            resp = client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                response_format={"type": "json_object"},
                temperature=0.4,
            )
            return resp.choices[0].message.content or ""
        except openai.RateLimitError as e:
            raise ProviderRateLimit(str(e)) from e
        except openai.AuthenticationError as e:
            raise ProviderAuthError(str(e)) from e
        except openai.APIConnectionError as e:
            raise ProviderConnectionError(str(e)) from e
        except Exception as e:
            raise ProviderError(str(e)) from e


class OpenAIProvider(_OpenAICompatProvider):
    name = "openai"
    label = "OpenAI (ChatGPT)"
    env_key = "OPENAI_API_KEY"
    default_model = "gpt-4o-mini"
    base_url = None


class DeepSeekProvider(_OpenAICompatProvider):
    name = "deepseek"
    label = "DeepSeek"
    env_key = "DEEPSEEK_API_KEY"
    default_model = "deepseek-chat"
    base_url = "https://api.deepseek.com"


# ============================================================
# Groq (SDK `groq`, juga kompatibel-OpenAI tapi paket sendiri)
# ============================================================

class GroqProvider(LLMProvider):
    name = "groq"
    label = "Groq"
    env_key = "GROQ_API_KEY"
    default_model = "llama-3.3-70b-versatile"

    def chat_json(self, system_prompt: str, user_prompt: str) -> str:
        try:
            import groq
            from groq import Groq
        except ImportError as e:
            raise ProviderNotInstalled(
                "Paket 'groq' belum terpasang. Jalankan: pip install groq"
            ) from e

        client = Groq(api_key=self.api_key, max_retries=0)
        try:
            resp = client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                response_format={"type": "json_object"},
                temperature=0.4,
            )
            return resp.choices[0].message.content or ""
        except groq.RateLimitError as e:
            raise ProviderRateLimit(str(e)) from e
        except groq.AuthenticationError as e:
            raise ProviderAuthError(str(e)) from e
        except groq.APIConnectionError as e:
            raise ProviderConnectionError(str(e)) from e
        except Exception as e:
            raise ProviderError(str(e)) from e


# ============================================================
# Google Gemini (SDK baru `google-genai`)
# ============================================================

class GeminiProvider(LLMProvider):
    name = "gemini"
    label = "Google Gemini"
    env_key = "GEMINI_API_KEY"
    default_model = "gemini-2.0-flash"

    def chat_json(self, system_prompt: str, user_prompt: str) -> str:
        try:
            from google import genai
            from google.genai import types
            from google.genai import errors as genai_errors
        except ImportError as e:
            raise ProviderNotInstalled(
                "Paket 'google-genai' belum terpasang untuk penyedia 'gemini'. "
                "Jalankan: pip install google-genai"
            ) from e

        client = genai.Client(api_key=self.api_key)
        try:
            resp = client.models.generate_content(
                model=self.model,
                contents=user_prompt,
                config=types.GenerateContentConfig(
                    system_instruction=system_prompt,
                    response_mime_type="application/json",
                    temperature=0.4,
                ),
            )
            return resp.text or ""
        except genai_errors.APIError as e:
            code = getattr(e, "code", None)
            if code == 429:
                raise ProviderRateLimit(str(e)) from e
            if code in (401, 403):
                raise ProviderAuthError(str(e)) from e
            raise ProviderError(str(e)) from e
        except Exception as e:
            raise ProviderError(str(e)) from e


# ============================================================
# Anthropic Claude (SDK `anthropic`)
# ------------------------------------------------------------
# Anthropic tidak punya mode "json_object", jadi kepatuhan format JSON
# dijamin lewat instruksi pada system prompt + parser longgar di pemanggil.
# ============================================================

class AnthropicProvider(LLMProvider):
    name = "claude"
    label = "Anthropic (Claude)"
    env_key = "ANTHROPIC_API_KEY"
    default_model = "claude-3-5-haiku-latest"

    def chat_json(self, system_prompt: str, user_prompt: str) -> str:
        try:
            import anthropic
        except ImportError as e:
            raise ProviderNotInstalled(
                "Paket 'anthropic' belum terpasang untuk penyedia 'claude'. "
                "Jalankan: pip install anthropic"
            ) from e

        client = anthropic.Anthropic(api_key=self.api_key, max_retries=0)
        system = (
            system_prompt
            + "\n\nPENTING: keluarkan HANYA JSON valid sesuai instruksi, "
            "tanpa teks pembuka/penutup, tanpa pembungkus markdown."
        )
        try:
            resp = client.messages.create(
                model=self.model,
                max_tokens=4096,
                temperature=0.4,
                system=system,
                messages=[{"role": "user", "content": user_prompt}],
            )
            return "".join(
                block.text for block in resp.content
                if getattr(block, "type", None) == "text"
            )
        except anthropic.RateLimitError as e:
            raise ProviderRateLimit(str(e)) from e
        except anthropic.AuthenticationError as e:
            raise ProviderAuthError(str(e)) from e
        except anthropic.APIConnectionError as e:
            raise ProviderConnectionError(str(e)) from e
        except Exception as e:
            raise ProviderError(str(e)) from e


# ============================================================
# Registry & factory
# ============================================================

# Kunci utama + alias yang umum diketik pengguna.
_PROVIDERS = {
    "groq":      GroqProvider,
    "openai":    OpenAIProvider,
    "chatgpt":   OpenAIProvider,    # alias
    "gpt":       OpenAIProvider,    # alias
    "gemini":    GeminiProvider,
    "google":    GeminiProvider,    # alias
    "claude":    AnthropicProvider,
    "anthropic": AnthropicProvider,  # alias
    "deepseek":  DeepSeekProvider,
}

# Provider default bila LLM_PROVIDER tidak diisi.
DEFAULT_PROVIDER = "groq"


def available_providers() -> list:
    """Daftar nama penyedia utama (tanpa alias), untuk dokumentasi/diagnostik."""
    seen = []
    for cls in (GroqProvider, OpenAIProvider, GeminiProvider,
                AnthropicProvider, DeepSeekProvider):
        if cls.name not in seen:
            seen.append(cls.name)
    return seen


def resolve_provider():
    """Tentukan penyedia aktif berdasarkan environment.

    Membaca:
      LLM_PROVIDER — nama penyedia (default 'groq')
      <ENV_KEY>    — API key sesuai penyedia (mis. GROQ_API_KEY)
      LLM_MODEL    — opsional, menimpa model default penyedia

    Returns:
        Tuple (provider, status, label):
          provider — instance LLMProvider, atau None bila tidak bisa dipakai
          status   — "ok" | "no_key" | "unknown_provider"
          label    — nama tampilan penyedia (untuk pesan ke pengguna)
    """
    raw = (os.environ.get("LLM_PROVIDER", "") or "").strip().lower()
    name = raw or DEFAULT_PROVIDER

    cls = _PROVIDERS.get(name)
    if cls is None:
        return None, "unknown_provider", raw

    api_key = (os.environ.get(cls.env_key, "") or "").strip()
    if not api_key:
        return None, "no_key", cls.label

    model = (os.environ.get("LLM_MODEL", "") or "").strip() or None
    return cls(api_key, model=model), "ok", cls.label
