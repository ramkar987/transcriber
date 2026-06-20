from __future__ import annotations

import os
from dataclasses import dataclass

from groq import Groq


class AIServiceError(Exception):
    """Erro genérico do serviço de IA."""


@dataclass
class AIResult:
    """Resultado consolidado de IA."""
    summary: str | None
    translation: str | None


def get_groq_client() -> Groq:
    """Cria o cliente Groq a partir de secrets ou variável de ambiente."""
    api_key = None
    try:
        import streamlit as st  # type: ignore
        api_key = st.secrets.get("GROQ_API_KEY")
    except Exception:
        api_key = None

    if not api_key:
        api_key = os.environ.get("GROQ_API_KEY")

    if not api_key:
        raise AIServiceError("GROQ_API_KEY não configurada.")

    return Groq(api_key=api_key)


def _chat(client: Groq, system_prompt: str, user_prompt: str, model: str) -> str:
    """Executa uma chamada de chat e retorna o texto da resposta."""
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.2,
    )
    return response.choices[0].message.content or ""


def summarize_transcript(transcript_text: str, model: str = "llama-3.3-70b-versatile") -> str:
    """Gera um resumo curto e objetivo da transcrição."""
    client = get_groq_client()
    system_prompt = "Você é um assistente que resume transcrições em português com clareza e objetividade."
    user_prompt = (
        "Resuma o conteúdo abaixo em português do Brasil, em 5 a 8 bullets curtos. "
        "Não invente fatos. Mantenha apenas os pontos principais:\n\n"
        f"{transcript_text}"
    )
    return _chat(client, system_prompt, user_prompt, model).strip()


def translate_transcript(transcript_text: str, target_language: str, model: str = "llama-3.3-70b-versatile") -> str:
    """Traduz a transcrição para o idioma de destino."""
    client = get_groq_client()
    system_prompt = "Você é um tradutor profissional que preserva sentido, tom e clareza."
    user_prompt = (
        f"Traduza o texto abaixo para {target_language}. "
        "Mantenha os timestamps e preserve a estrutura das linhas. "
        "Não adicione explicações.\n\n"
        f"{transcript_text}"
    )
    return _chat(client, system_prompt, user_prompt, model).strip()
