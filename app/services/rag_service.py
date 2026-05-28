import json
import re
import os

import numpy as np
import faiss
from sentence_transformers import SentenceTransformer

from openai import OpenAI
from app.config import settings

client = OpenAI(
  api_key=settings.deepseek_api_key,
  base_url=settings.deepseek_base_url,
)

_model = None


def _get_model():
  global _model
  if _model is None:
    _model = SentenceTransformer("all-MiniLM-L6-v2")
  return _model


def chunk_text(text: str, size: int = 300) -> list[str]:
  words = text.replace("\n", " ")
  return [words[i:i + size] for i in range(0, len(words), size)]


def build_index(chunks: list[str]):
  model = _get_model()
  vecs = model.encode(chunks, convert_numpy=True, show_progress_bar=False)
  dim = vecs.shape[1]
  index = faiss.IndexFlatL2(dim)
  index.add(vecs)
  return index, vecs


def retrieve(index: faiss.IndexFlatL2, chunks: list[str], query: str, k: int = 3) -> list[str]:
  model = _get_model()
  qv = model.encode([query], convert_numpy=True, show_progress_bar=False)
  _, ids = index.search(qv, k)
  return [chunks[i] for i in ids[0] if i < len(chunks)]


SYSTEM_PROMPT = (
  "你是一名资深技术面试官。请根据用户的简历内容，生成针对性的面试题。"
)

USER_PROMPT_TEMPLATE = """以下是候选人的简历片段：

{context}

请根据上述简历内容，生成 5 道面试题，考察候选人的技术深度和项目经验。

必须按以下 JSON 格式返回（不要markdown代码块，只返回纯JSON）：
{{
  "questions": [
    {{"content": "题目内容", "order": 1}},
    {{"content": "题目内容", "order": 2}}
  ]
}}
"""


def generate_from_resume(chunks: list[str], index: faiss.IndexFlatL2, query: str) -> list[dict]:
  top_chunks = retrieve(index, chunks, query)
  context = "\n---\n".join(top_chunks)

  try:
    resp = client.chat.completions.create(
      model="deepseek-chat",
      messages=[
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": USER_PROMPT_TEMPLATE.format(context=context)},
      ],
      temperature=1.0,
    )
    raw = resp.choices[0].message.content or ""
    return _parse(raw)
  except Exception as e:
    raise RuntimeError(f"AI 出题失败: {e}")


def _parse(raw: str) -> list[dict]:
  json_str = raw.strip()
  match = re.search(r"```(?:json)?\s*([\s\S]*?)```", json_str)
  if match:
    json_str = match.group(1).strip()
  data = json.loads(json_str)
  questions = data.get("questions", [])
  for q in questions:
    q.setdefault("content", "")
    q.setdefault("order", 0)
  return questions[:5]
