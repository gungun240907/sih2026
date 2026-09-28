"""Extract plain text from txt/md/pdf/image uploads."""

import base64
import io

MAX_BYTES = 10 * 1024 * 1024
MAX_PDF_PAGES = 10

TEXT_EXTS = {".txt", ".md", ".markdown"}
PDF_EXTS = {".pdf"}
IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".webp"}
ALLOWED_EXTS = TEXT_EXTS | PDF_EXTS | IMAGE_EXTS


class ParseError(ValueError):
    pass


def _ext_of(filename: str) -> str:
    name = (filename or "").lower()
    dot = name.rfind(".")
    return name[dot:] if dot != -1 else ""


def extract_text(filename: str, data: bytes) -> tuple[str, str | None]:
    """Return (text, warning). Raises ParseError on invalid input."""
    if not data:
        raise ParseError("Empty file")
    if len(data) > MAX_BYTES:
        raise ParseError(f"File too large ({len(data) // 1024}KB > 10MB)")

    ext = _ext_of(filename)
    if ext not in ALLOWED_EXTS:
        raise ParseError(
            f"Unsupported file type {ext or '(none)'} — use txt, md, pdf, png, jpg, webp"
        )

    if ext in TEXT_EXTS:
        try:
            text = data.decode("utf-8")
        except UnicodeDecodeError:
            text = data.decode("utf-8", errors="replace")
        if not text.strip():
            raise ParseError("No text found in file")
        return text.strip(), None

    if ext in PDF_EXTS:
        return _extract_pdf(data)

    return _extract_image(data)


def _extract_pdf(data: bytes) -> tuple[str, str | None]:
    try:
        from pypdf import PdfReader
    except ImportError as e:
        raise ParseError(f"PDF support not installed: {e}")
    try:
        reader = PdfReader(io.BytesIO(data))
    except Exception as e:
        raise ParseError(f"Could not read PDF: {e}")
    if len(reader.pages) > MAX_PDF_PAGES:
        raise ParseError(f"PDF has {len(reader.pages)} pages (max {MAX_PDF_PAGES})")
    parts = [(p.extract_text() or "") for p in reader.pages]
    text = "\n".join(p for p in parts if p.strip()).strip()
    if len(text) < 50:
        return text, (
            "Little extractable text — this may be a scanned PDF. "
            "If the preview looks empty, upload a photo/screenshot instead."
            if text else
            "No extractable text — this looks like a scanned PDF. "
            "Upload a photo/screenshot instead."
        )
    return text, None


def _extract_image(data: bytes) -> tuple[str, str | None]:
    from app.config import GROQ_API_KEY, LLM_MODEL  # local import to avoid cycles

    if not GROQ_API_KEY:
        raise ParseError("Image OCR needs GROQ_API_KEY — upload a PDF or paste text instead")
    try:
        from openai import OpenAI
    except ImportError as e:
        raise ParseError(f"OCR support not installed: {e}")

    b64 = base64.b64encode(data).decode("ascii")
    client = OpenAI(api_key=GROQ_API_KEY, base_url="https://api.groq.com/openai/v1")
    try:
        resp = client.chat.completions.create(
            model="llama-3.2-11b-vision-preview",
            messages=[{
                "role": "user",
                "content": [
                    {"type": "text",
                     "text": "Transcribe this resume image exactly, preserving sections and line breaks. Return only the transcription."},
                    {"type": "image_url",
                     "image_url": {"url": f"data:image/png;base64,{b64}"}},
                ],
            }],
            temperature=0.0,
            max_tokens=4000,
        )
    except Exception as e:
        # fall back to text model name in config for the error message
        raise ParseError(f"Image transcription failed ({LLM_MODEL}): {e}")
    text = (resp.choices[0].message.content or "").strip()
    if len(text) < 20:
        raise ParseError("Could not read any text from this image — try a clearer photo")
    return text, None
