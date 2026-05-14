import json
import re

from openai import OpenAI, APIConnectionError, AuthenticationError, APITimeoutError

from app.config import settings

client = OpenAI(
  api_key=settings.deepseek_api_key,
  base_url=settings.deepseek_base_url,
)

SYSTEM_PROMPT = (
  "你是一名资深技术面试官。请根据你了解的职位要求，生成面试题。"
  "要求题目贴近真实面试场景，难度适中，覆盖基础到进阶。"
)

USER_PROMPT_TEMPLATE = """职位名称：{title}
职位描述：{description}

请针对上述职位，生成 {count} 道面试题。
{avoid_text}

必须按以下 JSON 格式返回（不要markdown代码块，只返回纯JSON）：
{{
  "questions": [
    {{"content": "题目内容", "order": 1}},
    {{"content": "题目内容", "order": 2}}
  ]
}}
"""


def generate_questions(title: str, description: str, count: int = 5, avoid: list[str] | None = None) -> list[dict]:
  avoid_text = ""
  if avoid:
    avoid_text = "以下题目已经出过，请避免重复：\n" + "\n".join(f"- {q}" for q in avoid)

  try:
    resp = client.chat.completions.create(
      model="deepseek-chat",
      messages=[
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": USER_PROMPT_TEMPLATE.format(title=title, description=description, count=count, avoid_text=avoid_text)},
      ],
      temperature=1.0,
    )
    raw = resp.choices[0].message.content or ""
    return _parse_questions(raw, count)
  except AuthenticationError:
    raise RuntimeError("API Key 无效，请在 .env 中设置正确的 DEEPSEEK_API_KEY")
  except (APIConnectionError, APITimeoutError):
    raise RuntimeError("网络连接失败，请检查网络后重试")
  except Exception as e:
    raise RuntimeError(f"AI 出题失败: {e}")


def _parse_questions(raw: str, expected: int) -> list[dict]:
  json_str = raw.strip()

  match = re.search(r"```(?:json)?\s*([\s\S]*?)```", json_str)
  if match:
    json_str = match.group(1).strip()

  try:
    data = json.loads(json_str)
  except json.JSONDecodeError:
    raise RuntimeError("AI 返回的格式无法解析，请重试")

  questions = data.get("questions", [])
  if not questions:
    raise RuntimeError("AI 返回的题目为空")

  for q in questions:
    q.setdefault("content", "")
    q.setdefault("order", 0)

  return questions[:expected]
