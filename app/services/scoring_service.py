import json
import re

from openai import OpenAI

from app.config import settings

client = OpenAI(
  api_key=settings.deepseek_api_key,
  base_url=settings.deepseek_base_url,
)

SYSTEM_PROMPT = "你是一名资深面试官，请从深度、表达、逻辑、实用四个维度对面试者的答案进行评分。"


def score_interview(title: str, questions: list[dict]) -> dict:
  questions_text = "\n".join(
    f"第{q['order']}题：{q['content']}\n面试者回答：{q['answer'] or '（未作答）'}\n"
    for q in questions
  )

  prompt = f"""职位名称：{title}

以下是一次模拟面试的全部题目和面试者回答，请逐题评分：

{questions_text}

评分标准（每题4个维度，每项1-5分）：
- 深度：是否理解问题本质
- 表达：回答是否清晰有条理  
- 逻辑：论证是否严谨
- 实用：解决方案是否可行

每题得分 = (depth + expression + logic + practical) / 4 * 20（百分制）

必须按以下 JSON 格式返回（不要markdown代码块，只返回纯JSON）：
{{
  "scores": [
    {{"order": 1, "score": 0, "comment": "评分理由"}},
    {{"order": 2, "score": 0, "comment": "评分理由"}}
  ],
  "summary": "对面试者整体表现的评价和建议"
}}
"""

  try:
    resp = client.chat.completions.create(
      model="deepseek-chat",
      messages=[
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": prompt},
      ],
      temperature=0.3,
    )
    raw = resp.choices[0].message.content or ""
    return _parse_scores(raw)
  except Exception as e:
    raise RuntimeError(f"AI 评分调用失败: {e}")


def _parse_scores(raw: str) -> dict:
  json_str = raw.strip()

  match = re.search(r"```(?:json)?\s*([\s\S]*?)```", json_str)
  if match:
    json_str = match.group(1).strip()

  try:
    data = json.loads(json_str)
  except json.JSONDecodeError:
    raise RuntimeError("AI 评分返回格式无法解析")

  scores = data.get("scores", [])
  if not scores:
    raise RuntimeError("AI 评分结果为空")

  return data
