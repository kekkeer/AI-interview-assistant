import pdfplumber
from docx import Document


def parse_pdf(path: str) -> str:
  text = ""
  with pdfplumber.open(path) as pdf:
    for page in pdf.pages:
      t = page.extract_text()
      if t:
        text += t + "\n"
  return text.strip()


def parse_docx(path: str) -> str:
  doc = Document(path)
  return "\n".join(p.text for p in doc.paragraphs).strip()


def parse_file(path: str) -> str:
  if path.endswith(".pdf"):
    return parse_pdf(path)
  elif path.endswith(".docx"):
    return parse_docx(path)
  raise ValueError(f"不支持的文件格式: {path}")
