from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import yt_dlp


@dataclass
class MediaMetadata:
    """Representa os metadados essenciais de uma mídia suportada."""
    title: str
    source_url: str
    duration_seconds: int
    extractor_key: str
    webpage_url: str
    id: str


class DownloadError(Exception):
    """Erro genérico de download ou extração de metadados."""


class UnsupportedURLError(DownloadError):
    """Erro para URL inválida ou não suportada."""


class PrivateOrUnavailableVideoError(DownloadError):
    """Erro para vídeo privado, indisponível ou bloqueado."""


class LongDurationVideoError(DownloadError):
    """Erro para mídia com duração superior ao limite permitido."""


def is_supported_url(url: str) -> bool:
    """Verifica se a URL parece pertencer ao YouTube ou Instagram."""
    parsed = urlparse(url)
    host = parsed.netloc.lower()
    return any(domain in host for domain in ["youtube.com", "youtu.be", "instagram.com"])


def sanitize_filename(name: str) -> str:
    """Sanitiza um nome para uso em arquivos."""
    allowed = []
    for ch in name.strip():
        if ch.isalnum() or ch in ["-", "_", "."]:
            allowed.append(ch)
        elif ch.isspace():
            allowed.append("_")
    result = "".join(allowed)
    while "__" in result:
        result = result.replace("__", "_")
    return result.strip("._-") or "transcricao"


def extract_metadata(url: str) -> MediaMetadata:
    """Extrai metadados da mídia sem baixar o vídeo completo."""
    if not is_supported_url(url):
        raise UnsupportedURLError("URL inválida ou não suportada. Use YouTube ou Instagram.")

    ydl_opts = {
        "quiet": True,
        "skip_download": True,
        "noplaylist": True,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info: dict[str, Any] = ydl.extract_info(url, download=False)
    except yt_dlp.utils.ExtractorError as exc:
        message = str(exc).lower()
        if "private" in message or "unavailable" in message or "not available" in message:
            raise PrivateOrUnavailableVideoError("Vídeo privado ou indisponível.") from exc
        raise DownloadError(f"Falha ao extrair metadados: {exc}") from exc
    except Exception as exc:
        raise DownloadError(f"Falha inesperada ao extrair metadados: {exc}") from exc

    duration = int(info.get("duration") or 0)
    if duration <= 0:
        raise DownloadError("Não foi possível identificar a duração do vídeo.")
    if duration > 2 * 60 * 60:
        raise LongDurationVideoError("Vídeo com duração superior a 2 horas. Confirme antes de prosseguir.")

    title = str(info.get("title") or "transcricao")
    extractor_key = str(info.get("extractor_key") or info.get("extractor") or "")
    webpage_url = str(info.get("webpage_url") or url)
    media_id = str(info.get("id") or "unknown")

    return MediaMetadata(
        title=title,
        source_url=url,
        duration_seconds=duration,
        extractor_key=extractor_key,
        webpage_url=webpage_url,
        id=media_id,
    )


def download_audio(url: str, output_dir: Path) -> tuple[Path, MediaMetadata]:
    """Baixa apenas o áudio e retorna o caminho do arquivo gerado."""
    metadata = extract_metadata(url)
    output_dir.mkdir(parents=True, exist_ok=True)

    outtmpl = str(output_dir / "%(title)s_%(id)s.%(ext)s")
    ydl_opts = {
        "format": "bestaudio/best",
        "outtmpl": outtmpl,
        "noplaylist": True,
        "quiet": True,
        "retries": 3,
        "fragment_retries": 3,
        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192",
            }
        ],
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
    except yt_dlp.utils.DownloadError as exc:
        raise DownloadError(f"Falha ao baixar áudio: {exc}") from exc
    except Exception as exc:
        raise DownloadError(f"Falha inesperada ao baixar áudio: {exc}") from exc

    expected = output_dir / f"{sanitize_filename(metadata.title)}_{metadata.id}.mp3"
    if expected.exists():
        return expected, metadata

    candidates = sorted(output_dir.glob(f"*_{metadata.id}.mp3"))
    if candidates:
        return candidates[0], metadata

    raise DownloadError("Áudio baixado, mas o arquivo final não foi localizado.")
