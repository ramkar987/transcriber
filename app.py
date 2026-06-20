from __future__ import annotations

import tempfile
from pathlib import Path

import streamlit as st

from ai import AIServiceError, summarize_transcript, translate_transcript
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

st.set_page_config(page_title="Transcritor IA", page_icon="🎙️", layout="centered")

st.title("🎙️ Transcritor YouTube / Instagram com IA")
st.write("Cole uma URL, gere a transcrição e opcionalmente crie resumo e tradução com Groq.")

with st.form("transcription_form"):
    url = st.text_input("URL do vídeo", placeholder="https://youtube.com/watch?v=XXXX")
    language = st.selectbox("Idioma da transcrição", ["auto", "pt", "en", "es"], index=0)
    model_name = st.selectbox("Modelo Whisper", ["base", "small", "medium"], index=0)
    use_summary = st.checkbox("Gerar resumo IA", value=True)
    use_translation = st.checkbox("Gerar tradução IA", value=False)
    translation_language = st.text_input("Idioma de destino da tradução", value="inglês")
    submitted = st.form_submit_button("Processar")

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

                transcript_text = "\n".join(
                    f"[{seg.start_seconds:0.0f}] {seg.text}" for seg in segments
                )
                markdown_parts = [build_markdown(metadata, segments)]

                if use_summary:
                    with st.spinner("Gerando resumo com IA..."):
                        summary = summarize_transcript(transcript_text)
                    markdown_parts.append("\n## Resumo IA\n\n" + summary)

                if use_translation:
                    with st.spinner("Gerando tradução com IA..."):
                        translation = translate_transcript(transcript_text, translation_language)
                    markdown_parts.append(f"\n## Tradução IA ({translation_language})\n\n{translation}")

        final_markdown = "\n".join(markdown_parts)

        st.success("Processamento concluído.")
        st.text_area("Prévia do Markdown", final_markdown, height=500)

        safe_name = metadata.title[:80].replace(" ", "_")
        st.download_button(
            label="Baixar Markdown",
            data=final_markdown,
            file_name=f"{safe_name}.md",
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
    except AIServiceError as exc:
        st.error(f"Falha na IA: {exc}")
    except Exception as exc:
        st.exception(exc)
