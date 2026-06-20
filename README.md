# Transcritor YouTube/Instagram - Streamlit

App web para baixar apenas o áudio de vídeos do YouTube e Instagram, transcrever localmente com Whisper e gerar Markdown compatível com Obsidian.

## 1. Instalação local
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## 2. Instalar FFmpeg no sistema
Ubuntu/Debian:
```bash
sudo apt install ffmpeg
```

## 3. Rodar a app
```bash
streamlit run app.py
```

## 4. Usar
- Cole a URL do vídeo.
- Escolha o idioma e o modelo.
- Clique em **Transcrever**.
- Baixe o arquivo `.md`.

## 5. Deploy no Streamlit Community Cloud
- Envie o projeto para o GitHub.
- Garanta que `requirements.txt` e `packages.txt` estejam na raiz.
- Configure o app principal como `app.py`.
- Faça o deploy pelo Streamlit Community Cloud.