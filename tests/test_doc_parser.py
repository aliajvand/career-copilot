import unittest
from pathlib import Path
from core.doc_parser import doc_parser, PersianNLPOptimizer

class TestDocumentParser(unittest.TestCase):

    def test_persian_normalization(self):
        dirty_text = "شركت داده پردازي علي رجوند ١٢٣٤٥ مي شود"
        clean = PersianNLPOptimizer.normalize(dirty_text)
        self.assertIn("شرکت", clean)
        self.assertIn("پردازی", clean)
        self.assertIn("علی", clean)
        self.assertIn("۱۲۳۴۵", clean)
        self.assertIn("می‌شود", clean)

    def test_real_resume_parsing(self):
        pdf_path = Path("D:/startup/Ali_Ajvand_Resume (12) (1).pdf")
        if pdf_path.exists():
            content = pdf_path.read_bytes()
            parsed = doc_parser.parse_bytes(content, pdf_path.name)
            self.assertGreater(len(parsed), 500)
            self.assertIn("Ali Ajvand", parsed)

    def test_section_segmentation(self):
        sample_resume = """
        علی رجوند - متخصص هوش مصنوعی
        
        سوابق کاری:
        - توسعه‌دهنده هوش تجاری در JTI به مدت ۲ سال
        - سرپرست تحلیل داده
        
        مهارت‌های فنی:
        Python, Power BI, SQL, Machine Learning
        
        تحصیلات:
        کارشناسی مهندسی کامپیوتر
        """
        sections = doc_parser.extract_sections(sample_resume)
        self.assertIn("JTI", sections["experience"])
        self.assertIn("Python", sections["skills"])
        self.assertIn("مهندسی کامپیوتر", sections["education"])

if __name__ == "__main__":
    unittest.main()
