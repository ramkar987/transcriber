from __future__ import annotations

import tempfile
from pathlib import Path

import streamlit as st

from downloader import (
    DownloadError,
    LongDurationVideoError,
    PrivateOrUnavailableVideoError,
    UnsupportedURLError,
    download_audio,
    extract_metadata,
)
from formatter import build_markdown
from transcriber import TranscriptionError, transcribe_audio

st.set_page_config(page_title="Transcritor YouTube/Instagram", page_icon="🎙️", layout="centered")

st.title("🎙️ Transcritor YouTube / Instagram")
st.write("Cole uma URL do YouTube ou Instagram, gere a transcrição com timestamps e baixe o Markdown pronto para Obsidian.")

with st.form("transcription_form"):
    url = st.text_input("URL do vídeo", placeholder="https://youtube.com/watch?v=XXXX")
    language = st.selectbox("Idioma da transcrição", ["auto", "pt", "en", "es"], index=0)
    model_name = st.selectbox("Modelo Whisper", ["base", "small", "medium"], index=0)
    submitted = st.form_submit_button("Transcrever")

if submitted:
    if not url.strip():
        st.error("Informe uma URL válida.")
        st.stop()

    try:
        with st.spinner("Validando URL e coletando metadados..."):
            metadata = extract_metadata(url.strip())

        if metadata.duration_seconds > 2 * 60 * 60:
            st.warning("Vídeo com mais de 2 horas. O processamento pode ser demorado.")

        with st.spinner("Baixando apenas o áudio..."):
            with tempfile.TemporaryDirectory() as tmpdir:
                audio_dir = Path(tmpdir) / "audio"
                audio_path, metadata = download_audio(url.strip(), audio_dir)

                with st.spinner("Transcrevendo com Whisper local..."):
                    segments = transcribe_audio(
                        audio_path=audio_path,
                        model_name=model_name,
                        language=None if language == "auto" else language,
                    )

                markdown = build_markdown(metadata, segments)

        st.success("Transcrição concluída.")
        st.text_area("Prévia do Markdown", markdown, height=400)

        st.download_button(
            label="Baixar Markdown",
            data=markdown,
            file_name=f"{metadata.title[:80].replace(' ', '_')}.md",
            mime="text/markdown",
        )

    except UnsupportedURLError as exc:
        st.error(f"URL inválida ou não suportada: {exc}")
    except PrivateOrUnavailableVideoError as exc:
        st.error(f"Vídeo privado ou indisponível: {exc}")
    except LongDurationVideoError as exc:
        st.error(f"Duração acima do limite: {exc}")
    except DownloadError as exc:
        st.error(f"Falha no download: {exc}")
    except TranscriptionError as exc:
        st.error(f"Falha na transcrição: {exc}")
    except Exception as exc:
        st.exception(exc)