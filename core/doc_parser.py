"""
Advanced Document Parser & Persian OCR/NLP Engine for Career Co-Pilot Enterprise.
Built with skills: persian-ocr + persian-nlp + document-parsing-resume
Features:
- Two-column PDF layout-aware extraction (preserves column reading order)
- Persian OCR integration (Tesseract fas/eng + PyMuPDF pixmap rasterizer)
- Persian NLP text normalization (Yeh/Kaf, Arabic digits, half-space/ZWNJ, tatweel)
- Structured resume segmentation (Experience, Skills, Education, Projects)
"""

import io
import re
from pathlib import Path
from typing import Dict, Any, List, Optional
from PIL import Image

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

try:
    import pytesseract
    HAS_TESSERACT = True
except ImportError:
    HAS_TESSERACT = False

class PersianNLPOptimizer:
    """Normalizes Persian and Arabic text variants, digits, and half-spaces."""

    # Arabic to Persian character mapping
    CHAR_MAP = {
        'ي': 'ی',
        'ى': 'ی',
        'ك': 'ک',
        'ة': 'ه',
        'ؤ': 'و',
        'إ': 'ا',
        'أ': 'ا',
        'ء': '',
        'ئ': 'ی',
        'ـ': '', # Tatweel/Kashida removal
    }

    # Arabic digits to Persian
    DIGIT_MAP = {
        '٠': '۰', '١': '۱', '٢': '۲', '٣': '۳', '٤': '۴',
        '٥': '۵', '٦': '۶', '٧': '۷', '٨': '۸', '٩': '۹'
    }

    @classmethod
    def normalize(cls, text: str) -> str:
        if not text:
            return ""

        # 1. Normalize Arabic characters
        for ar, fa in cls.CHAR_MAP.items():
            text = text.replace(ar, fa)

        # 2. Normalize Arabic digits to Persian
        for ar_d, fa_d in cls.DIGIT_MAP.items():
            text = text.replace(ar_d, fa_d)

        # 3. Normalize ZWNJ (half-space)
        # Standardize multiple spaces and weird newlines
        text = re.sub(r'[\u200c\s]+', lambda m: '\u200c' if '\u200c' in m.group(0) and ' ' not in m.group(0) else ' ', text)
        
        # 4. Common Persian affixes normalization with ZWNJ (e.g. "می شود" -> "می‌شود")
        text = re.sub(r'\b(می|نمی)\s+', lambda m: m.group(1) + '\u200c', text)
        text = re.sub(r'\s+(ها|های|هایی|هایم|هایت|هایمان|هایتان|هایشان)\b', lambda m: '\u200c' + m.group(1), text)

        # 5. Remove excessive linebreaks and whitespace
        text = re.sub(r'[ \t]+', ' ', text)
        text = re.sub(r'\n{3,}', '\n\n', text)
        return text.strip()


class DocumentParser:
    """
    Enterprise-grade parser for Resumes (.pdf, .docx, .png, .jpg, .txt).
    Supports layout-aware extraction and OCR.
    """

    @classmethod
    def parse_bytes(cls, content: bytes, filename: str) -> str:
        suffix = Path(filename).suffix.lower()

        if suffix == ".pdf":
            raw = cls.extract_from_pdf(content)
        elif suffix in [".docx", ".doc"]:
            raw = cls.extract_from_docx(content)
        elif suffix in [".png", ".jpg", ".jpeg", ".tiff", ".bmp"]:
            raw = cls.extract_from_image(content)
        elif suffix in [".txt", ".md"]:
            raw = cls.extract_from_text(content)
        else:
            try:
                raw = content.decode("utf-8")
            except Exception:
                raw = cls.extract_from_pdf(content)

        return PersianNLPOptimizer.normalize(raw)

    @classmethod
    def extract_from_pdf(cls, content: bytes) -> str:
        """Extracts text from PDF, handling two-column layouts and falling back to OCR if scanned."""
        text_parts = []
        
        if HAS_FITZ:
            try:
                doc = fitz.open(stream=content, filetype="pdf")
                total_text_len = 0
                
                for page in doc:
                    # Layout-aware block extraction: detects columns
                    blocks = page.get_text("blocks")
                    # blocks: (x0, y0, x1, y1, "text", block_no, block_type)
                    page_width = page.rect.width
                    mid_x = page_width / 2.0

                    # Check if page looks like two-column (content distributed across both halves)
                    left_blocks = []
                    right_blocks = []
                    full_blocks = []

                    for b in blocks:
                        if b[6] != 0: # not text block
                            continue
                        text = b[4].strip()
                        if not text:
                            continue
                        x0, y0, x1, y1 = b[:4]
                        
                        if x1 <= mid_x + 20:
                            left_blocks.append((y0, text))
                        elif x0 >= mid_x - 20:
                            right_blocks.append((y0, text))
                        else:
                            full_blocks.append((y0, text))

                    # If clear 2-column layout exists, sort columns sequentially
                    if len(left_blocks) >= 2 and len(right_blocks) >= 2:
                        # Order: left column then right column (or RTL depending on font)
                        left_blocks.sort(key=lambda x: x[0])
                        right_blocks.sort(key=lambda x: x[0])
                        sorted_text = [t for _, t in left_blocks] + [t for _, t in right_blocks]
                        page_text = "\n".join(sorted_text)
                    else:
                        # Default natural reading order
                        blocks.sort(key=lambda b: (b[1], b[0]))
                        page_text = "\n".join(b[4].strip() for b in blocks if b[4].strip())

                    total_text_len += len(page_text.strip())
                    text_parts.append(page_text)

                # Scanned PDF detection: if very little text was found across pages, trigger OCR rasterization
                if total_text_len < 100 and HAS_TESSERACT:
                    ocr_parts = []
                    for page_idx in range(min(len(doc), 3)): # OCR up to 3 pages
                        page = doc[page_idx]
                        pix = page.get_pixmap(dpi=150)
                        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                        try:
                            ocr_text = pytesseract.image_to_string(img, lang="fas+eng")
                            if ocr_text.strip():
                                ocr_parts.append(ocr_text.strip())
                        except Exception:
                            # Tesseract binary might not be in PATH
                            pass
                    if ocr_parts:
                        doc.close()
                        return "\n\n".join(ocr_parts)

                doc.close()
                if text_parts:
                    return "\n\n".join(text_parts)
            except Exception:
                pass

        # Fallback to pypdf
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
    def extract_from_image(cls, content: bytes) -> str:
        """Performs OCR on resume image files."""
        if not HAS_TESSERACT:
            return "OCR_ENGINE_NOT_AVAILABLE: Tesseract is not installed or configured."
        try:
            img = Image.open(io.BytesIO(content))
            text = pytesseract.image_to_string(img, lang="fas+eng")
            return text.strip()
        except Exception as e:
            return f"OCR_ERROR: {str(e)}"

    @classmethod
    def extract_from_docx(cls, content: bytes) -> str:
        if not HAS_DOCX:
            return ""
        try:
            doc = docx.Document(io.BytesIO(content))
            full_text = []
            for para in doc.paragraphs:
                if para.text.strip():
                    full_text.append(para.text.strip())
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

    @classmethod
    def extract_sections(cls, text: str) -> Dict[str, str]:
        """
        Segments resume text into logical sections:
        - experience: سوابق کاری / سوابق شغلی / Work Experience
        - skills: مهارت‌ها / توانمندی‌ها / Skills
        - education: تحصیلات / مدارک تحصیلی / Education
        - projects: پروژه‌ها / دستاوردها / Projects
        """
        sections = {
            "summary": "",
            "experience": "",
            "skills": "",
            "education": "",
            "projects": ""
        }

        headings = {
            "experience": r"(?:سوابق\s+شغلی|سوابق\s+کاری|تجربیات\s+کاری|work\s+experience|experience)",
            "skills": r"(?:مهارت\s*ها|مهارت‌های\s+فنی|توانمندی\s*ها|skills|technical\s+skills)",
            "education": r"(?:تحصیلات|سوابق\s+تحصیلی|آموزش|education|academic)",
            "projects": r"(?:پروژه\s*ها|دستاوردها|پروژه‌های\s+برجسته|projects|achievements)"
        }

        combined = "|".join(f"(?P<{k}>{v})" for k, v in headings.items())
        pattern = re.compile(rf"(?:\n|\A)\s*(?:{combined})\s*[:\-\n]", re.IGNORECASE)
        matches = list(pattern.finditer(text))

        if not matches:
            sections["summary"] = text.strip()
            return sections

        # Content before first heading is summary
        sections["summary"] = text[:matches[0].start()].strip()

        for i, m in enumerate(matches):
            start = m.end()
            end = matches[i+1].start() if i+1 < len(matches) else len(text)
            matched_keys = [k for k, v in m.groupdict().items() if v]
            if matched_keys:
                sec_key = matched_keys[0]
                sections[sec_key] = text[start:end].strip()

        return sections

doc_parser = DocumentParser()
