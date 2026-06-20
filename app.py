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

# ─── Configuração da página ───────────────────────────────────────────────────
st.set_page_config(
    page_title="Transcritor IA",
    page_icon="🎙️",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ─── CSS customizado ──────────────────────────────────────────────────────────
st.markdown("""
<style>
/* Remove padding padrão do topo */
.block-container {
    padding-top: 1.8rem;
    padding-bottom: 2rem;
    max-width: 1200px;
}

/* Cabeçalho principal */
.app-header {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    margin-bottom: 0.25rem;
}
.app-title {
    font-size: 2rem;
    font-weight: 800;
    background: linear-gradient(90deg, #7C3AED, #A78BFA);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    margin: 0;
}
.app-subtitle {
    color: #9CA3AF;
    font-size: 0.95rem;
    margin-bottom: 1.5rem;
}

/* Cards */
.card {
    background: rgba(255,255,255,0.04);
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 16px;
    padding: 1.4rem 1.5rem;
    margin-bottom: 1rem;
}
.card-title {
    font-size: 1rem;
    font-weight: 700;
    color: #A78BFA;
    margin-bottom: 1rem;
    text-transform: uppercase;
    letter-spacing: 0.06em;
}

/* Badge de status */
.badge-ok {
    display: inline-block;
    background: #065F46;
    color: #6EE7B7;
    padding: 0.2rem 0.75rem;
    border-radius: 999px;
    font-size: 0.8rem;
    font-weight: 600;
}
.badge-error {
    display: inline-block;
    background: #7F1D1D;
    color: #FCA5A5;
    padding: 0.2rem 0.75rem;
    border-radius: 999px;
    font-size: 0.8rem;
    font-weight: 600;
}

/* Divider */
.divider {
    border: none;
    border-top: 1px solid rgba(255,255,255,0.07);
    margin: 1rem 0;
}

/* Botão de download customizado */
div[data-testid="stDownloadButton"] button {
    width: 100%;
    background: linear-gradient(90deg, #7C3AED, #5B21B6);
    color: white;
    border: none;
    border-radius: 10px;
    padding: 0.55rem 1rem;
    font-weight: 600;
    font-size: 0.95rem;
    transition: opacity 0.2s;
}
div[data-testid="stDownloadButton"] button:hover {
    opacity: 0.88;
}

/* Textarea */
textarea {
    font-family: 'Courier New', monospace !important;
    font-size: 0.82rem !important;
}

/* Métricas */
.metric-row {
    display: flex;
    gap: 1rem;
    flex-wrap: wrap;
    margin-bottom: 1rem;
}
.metric-box {
    background: rgba(124,58,237,0.12);
    border: 1px solid rgba(124,58,237,0.25);
    border-radius: 12px;
    padding: 0.6rem 1rem;
    flex: 1;
    min-width: 120px;
}
.metric-label {
    font-size: 0.72rem;
    color: #9CA3AF;
    text-transform: uppercase;
    letter-spacing: 0.05em;
}
.metric-value {
    font-size: 1.05rem;
    font-weight: 700;
    color: #E5E7EB;
}
</style>
""", unsafe_allow_html=True)

# ─── Cabeçalho ────────────────────────────────────────────────────────────────
st.markdown("""
<div class="app-header">
    <span style="font-size:2rem;">🎙️</span>
    <p class="app-title">Transcritor IA</p>
</div>
<p class="app-subtitle">
    Baixe áudio, transcreva com Whisper, gere resumo e traduza com IA — tudo em um clique.
</p>
""", unsafe_allow_html=True)

# ─── Layout de duas colunas ───────────────────────────────────────────────────
col_input, col_output = st.columns([1, 1.3], gap="large")

# ─── Coluna esquerda: configurações ──────────────────────────────────────────
with col_input:

    st.markdown('<div class="card"><div class="card-title">🔗 Vídeo</div>', unsafe_allow_html=True)
    url = st.text_input(
        "URL do vídeo",
        placeholder="https://youtube.com/watch?v=XXXX",
        label_visibility="collapsed",
    )
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="card"><div class="card-title">⚙️ Transcrição</div>', unsafe_allow_html=True)
    whisper_model = st.selectbox(
        "Modelo Whisper",
        options=["base", "small", "medium"],
        index=0,
        help="Modelos maiores são mais precisos, mas mais lentos.",
    )
    language = st.selectbox(
        "Idioma do áudio",
        options=["auto", "pt", "en", "es", "fr", "de", "it"],
        index=0,
        help="'auto' detecta automaticamente.",
    )
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="card"><div class="card-title">🤖 Inteligência Artificial</div>', unsafe_allow_html=True)
    use_summary = st.checkbox("Gerar resumo com IA", value=True)
    use_translation = st.checkbox("Gerar tradução com IA", value=False)
    translation_language = st.text_input(
        "Idioma de destino",
        value="inglês",
        disabled=not use_translation,
    )
    groq_model = st.selectbox(
        "Modelo Groq",
        options=[
            "llama-3.3-70b-versatile",
            "llama-3.1-8b-instant",
            "gemma2-9b-it",
            "mixtral-8x7b-32768",
        ],
        index=0,
        help="Modelos maiores geram resultados mais precisos.",
    )
    st.markdown('</div>', unsafe_allow_html=True)

    process_btn = st.button("▶ Processar Vídeo", use_container_width=True, type="primary")

# ─── Coluna direita: resultado ────────────────────────────────────────────────
with col_output:

    st.markdown('<div class="card"><div class="card-title">📄 Resultado</div>', unsafe_allow_html=True)

    result_placeholder = st.empty()
    download_placeholder = st.empty()

    if not process_btn:
        result_placeholder.markdown("""
<div style="text-align:center; padding: 3rem 1rem; color: #6B7280;">
    <span style="font-size:2.5rem;">📂</span><br><br>
    <span>Preencha os campos ao lado e clique em <strong>Processar Vídeo</strong>.</span>
</div>
""", unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)

# ─── Processamento ────────────────────────────────────────────────────────────
if process_btn:
    if not url.strip():
        with col_output:
            st.error("Informe uma URL válida.")
        st.stop()

    final_markdown = None
    metadata = None

    try:
        with col_output:
            with st.status("Processando...", expanded=True) as status:

                st.write("🔍 Validando URL e coletando metadados...")
                metadata = extract_metadata(url.strip())

                if metadata.duration_seconds > 2 * 60 * 60:
                    st.warning("Vídeo com mais de 2 horas. O processamento pode ser demorado.")

                duration_fmt = f"{metadata.duration_seconds // 3600:02d}:{(metadata.duration_seconds % 3600) // 60:02d}:{metadata.duration_seconds % 60:02d}"

                st.write("⬇️ Baixando áudio...")
                with tempfile.TemporaryDirectory() as tmpdir:
                    audio_dir = Path(tmpdir) / "audio"
                    audio_path, metadata = download_audio(url.strip(), audio_dir)

                    st.write("🎙️ Transcrevendo com Whisper...")
                    segments = transcribe_audio(
                        audio_path=audio_path,
                        model_name=whisper_model,
                        language=None if language == "auto" else language,
                    )

                    transcript_text = "\n".join(
                        f"[{seg.start_seconds:0.0f}] {seg.text}" for seg in segments
                    )
                    markdown_parts = [build_markdown(metadata, segments)]

                    if use_summary:
                        st.write("📝 Gerando resumo com IA...")
                        summary = summarize_transcript(transcript_text, model=groq_model)
                        markdown_parts.append("\n## Resumo IA\n\n" + summary)

                    if use_translation:
                        st.write(f"🌐 Traduzindo para {translation_language}...")
                        translation = translate_transcript(transcript_text, translation_language, model=groq_model)
                        markdown_parts.append(f"\n## Tradução IA ({translation_language})\n\n{translation}")

                final_markdown = "\n".join(markdown_parts)
                status.update(label="✅ Concluído!", state="complete", expanded=False)

        # Métricas
        with col_output:
            words = len(transcript_text.split()) if "transcript_text" in dir() else 0
            st.markdown(f"""
<div class="metric-row">
    <div class="metric-box">
        <div class="metric-label">Duração</div>
        <div class="metric-value">{duration_fmt}</div>
    </div>
    <div class="metric-box">
        <div class="metric-label">Segmentos</div>
        <div class="metric-value">{len(segments)}</div>
    </div>
    <div class="metric-box">
        <div class="metric-label">Palavras</div>
        <div class="metric-value">{words:,}</div>
    </div>
    <div class="metric-box">
        <div class="metric-label">Modelo</div>
        <div class="metric-value">{whisper_model}</div>
    </div>
</div>
""", unsafe_allow_html=True)

            tabs = st.tabs(["📄 Transcrição", "📝 Resumo IA", "🌐 Tradução"])

            with tabs[0]:
                st.text_area(
                    "Transcrição completa",
                    value=markdown_parts[0],
                    height=400,
                    label_visibility="collapsed",
                )

            with tabs[1]:
                if use_summary:
                    st.markdown(summary)
                else:
                    st.info("Resumo IA não foi solicitado.")

            with tabs[2]:
                if use_translation:
                    st.markdown(translation)
                else:
                    st.info("Tradução IA não foi solicitada.")

            st.markdown("<hr class='divider'>", unsafe_allow_html=True)
            safe_name = metadata.title[:80].replace(" ", "_")
            st.download_button(
                label="⬇️ Baixar Markdown completo",
                data=final_markdown,
                file_name=f"{safe_name}.md",
                mime="text/markdown",
                use_container_width=True,
            )

    except UnsupportedURLError as exc:
        with col_output:
            st.error(f"🚫 URL inválida ou não suportada: {exc}")
    except PrivateOrUnavailableVideoError as exc:
        with col_output:
            st.error(f"🔒 Vídeo privado ou indisponível: {exc}")
    except LongDurationVideoError as exc:
        with col_output:
            st.warning(f"⏱️ Duração acima do limite: {exc}")
    except DownloadError as exc:
        with col_output:
            st.error(f"⬇️ Falha no download: {exc}")
    except TranscriptionError as exc:
        with col_output:
            st.error(f"🎙️ Falha na transcrição: {exc}")
    except AIServiceError as exc:
        with col_output:
            st.error(f"🤖 Falha na IA: {exc}")
    except Exception as exc:
        with col_output:
            st.exception(exc)
