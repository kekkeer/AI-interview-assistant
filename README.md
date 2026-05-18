# AI 面试助手

基于 DeepSeek API 的智能模拟面试系统，帮助求职者通过 AI 出题 + AI 评分进行面试练习。

> 在线地址：联系作者获取

---

## 功能特性

- **AI 智能出题** — 根据职位要求自动生成 5 道面试题，贴近真实面试场景
- **逐题作答** — 每题独立作答，支持上下题切换，答案自动保存
- **AI 多维评分** — 深度 / 表达 / 逻辑 / 实用 4 维度评分 + 针对性评语
- **职位管理** — 5 个内置职位（Java后端 / 前端 / 测试 / 产品 / 算法）+ 自定义职位
- **数据看板** — 得分趋势折线图 + 各职位平均分柱状图
- **历史记录** — 分页列表 + 按职位筛选 + 查看详情
- **用户系统** — JWT 认证 + 密码加密（bcrypt）

---

## 技术栈

| 层级 | 技术 |
|------|------|------|
| 后端框架 | FastAPI (Python 3.14) |
| 数据库 | SQLAlchemy ORM + SQLite（开发）/ PostgreSQL（生产）|
| 模板引擎 | Jinja2 |
| 前端 | Bootstrap 5 + HTMX（局部刷新）|
| 图表 | Chart.js |
| AI 接口 | DeepSeek API（OpenAI 兼容）|
| 认证 | JWT (python-jose) + bcrypt |
| 部署 | Railway / Render / Zeabur |

---

## 快速开始

```bash
# 克隆仓库
git clone https://github.com/kekkeer/AI-interview-assistant.git
cd ai-interview-assistant

# 创建虚拟环境
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS / Linux
source .venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 配置环境变量
cp .env.example .env
# 编辑 .env，填入你的 DEEPSEEK_API_KEY

# 启动服务
uvicorn app.main:app --reload
```

访问 http://localhost:8001

---

## 环境变量

| 变量 | 必填 | 说明 |
|------|------|------|
| `DEEPSEEK_API_KEY` | ✅ | DeepSeek API Key |
| `SECRET_KEY` | ✅ | JWT 加密密钥（生成：`python -c "import secrets; print(secrets.token_hex(32))"`）|
| `DATABASE_URL` | ❌ | 数据库地址（默认 SQLite，生产环境用 PostgreSQL）|

---

## 项目结构

```
ai-interview/
├── app/
│   ├── main.py              # FastAPI 入口
│   ├── config.py            # 配置管理（pydantic-settings）
│   ├── database.py          # SQLAlchemy 引擎 + 会话
│   ├── render.py            # 模板渲染 + 当前用户注入
│   ├── models/              # 数据模型
│   │   ├── user.py          # User
│   │   └── interview.py     # Position / Interview / Question
│   ├── routers/             # 路由
│   │   ├── auth.py          # 注册 / 登录 / 登出 / 修改密码
│   │   ├── positions.py     # 职位列表 / 创建 / 出题
│   │   ├── interview.py     # 答题 / 评分 / 结果 / 历史
│   │   └── dashboard.py     # 数据看板
│   ├── services/            # 业务逻辑
│   │   ├── auth_service.py  # 密码哈希 / JWT
│   │   ├── ai_service.py    # DeepSeek 出题
│   │   ├── scoring_service.py # AI 评分
│   │   └── seed.py          # 种子数据
│   ├── templates/           # HTML 模板
│   └── static/              # CSS 样式
├── requirements.txt
├── Procfile                 # 部署配置
└── README.md
```

---

## 本地截图

（待补充 — 建议截 3 张：首页 / 答题页 / 数据看板）

---

## License

MIT
