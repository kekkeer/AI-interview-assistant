from app.database import SessionLocal
from app.models import Position

BUILTIN_POSITIONS = [
  {"title": "Java后端开发", "description": "Java基础、Spring框架、微服务架构、数据库设计、分布式系统"},
  {"title": "前端开发", "description": "HTML/CSS、JavaScript/TypeScript、React/Vue、性能优化、工程化"},
  {"title": "软件测试", "description": "测试理论、自动化测试、性能测试、CI/CD、缺陷管理"},
  {"title": "产品经理", "description": "需求分析、产品设计、数据分析、项目管理、用户研究"},
  {"title": "算法工程师", "description": "数据结构、机器学习、深度学习、模型优化、论文阅读"},
]


def seed_positions():
  db = SessionLocal()
  try:
    existing = db.query(Position).count()
    if existing > 0:
      return
    for data in BUILTIN_POSITIONS:
      db.add(Position(title=data["title"], description=data["description"], is_builtin=True))
    db.commit()
    print(f"种子数据：已添加 {len(BUILTIN_POSITIONS)} 个内置职位")
  finally:
    db.close()
