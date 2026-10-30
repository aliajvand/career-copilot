import io
from pathlib import Path
from typing import Union

try:
    import fitz  # PyMuPDF
    HAS_FITZ = True
except ImportError:
    HAS_FITZ = False

try:
    import pypdf
    HAS_PYPDF = True
except ImportError:
    HAS_PYPDF = False

try:
    import docx
    HAS_DOCX = True
except ImportError:
    HAS_DOCX = False

class DocumentParser:
    """
    Production-grade document parser for Resume files (.pdf, .docx, .txt).
    Extracts text cleanly while preserving structure, bullet points, and sections.
    """

    @classmethod
    def parse_bytes(cls, content: bytes, filename: str) -> str:
        suffix = Path(filename).suffix.lower()

        if suffix == ".pdf":
            return cls.extract_from_pdf(content)
        elif suffix in [".docx", ".doc"]:
            return cls.extract_from_docx(content)
        elif suffix in [".txt", ".md"]:
            return cls.extract_from_text(content)
        else:
            # Fallback attempt
            try:
                return content.decode("utf-8")
            except Exception:
                return cls.extract_from_pdf(content)

    @classmethod
    def extract_from_pdf(cls, content: bytes) -> str:
        text_parts = []
        
        # 1. Try PyMuPDF (fitz) first - fastest and highest fidelity
        if HAS_FITZ:
            try:
                doc = fitz.open(stream=content, filetype="pdf")
                for page in doc:
                    text = page.get_text()
                    if text:
                        text_parts.append(text.strip())
                doc.close()
                if text_parts:
                    return "\n\n".join(text_parts)
            except Exception:
                pass

        # 2. Try pypdf fallback
        if HAS_PYPDF:
            try:
                reader = pypdf.PdfReader(io.BytesIO(content))
                for page in reader.pages:
                    text = page.extract_text()
                    if text:
                        text_parts.append(text.strip())
                if text_parts:
                    return "\n\n".join(text_parts)
            except Exception:
                pass

        return ""

    @classmethod
    def extract_from_docx(cls, content: bytes) -> str:
        if not HAS_DOCX:
            return ""

        try:
            doc = docx.Document(io.BytesIO(content))
            full_text = []

            # Extract from paragraphs
            for para in doc.paragraphs:
                if para.text.strip():
                    full_text.append(para.text.strip())

            # Also extract from tables (many resumes format skills or experience in tables)
            for table in doc.tables:
                for row in table.rows:
                    row_text = [cell.text.strip() for cell in row.cells if cell.text.strip()]
                    if row_text:
                        full_text.append(" | ".join(row_text))

            return "\n\n".join(full_text)
        except Exception:
            return ""

    @classmethod
    def extract_from_text(cls, content: bytes) -> str:
        for enc in ["utf-8", "utf-16", "cp1256", "latin1"]:
            try:
                return content.decode(enc)
            except UnicodeDecodeError:
                continue
        return content.decode("utf-8", errors="ignore")

doc_parser = DocumentParser()
