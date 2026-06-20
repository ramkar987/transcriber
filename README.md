# Transcritor IA - Streamlit

App web para baixar o áudio de vídeos do YouTube e Instagram, transcrever com Whisper local e gerar resumo/tradução com Groq.

## 1. Configurar secrets
Crie `.streamlit/secrets.toml`:

```toml
GROQ_API_KEY = "sua_chave_aqui"
```

Ou defina a variável de ambiente `GROQ_API_KEY`.

## 2. Instalar
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
sudo apt install ffmpeg
```

## 3. Rodar localmente
```bash
streamlit run app.py
```

## 4. Usar
- Cole a URL do vídeo.
- Escolha idioma e modelo.
- Marque resumo e/ou tradução IA.
- Clique em Processar.
- Baixe o Markdown.

## 5. Deploy
- Suba os arquivos para o GitHub.
- Configure `GROQ_API_KEY` em Secrets no Streamlit Cloud.
- Mantenha `requirements.txt` e `packages.txt` na raiz.
- Use `app.py` como arquivo principal.
