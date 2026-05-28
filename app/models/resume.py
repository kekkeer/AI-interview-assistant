from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, func
from app.database import Base


class Resume(Base):
  __tablename__ = "resumes"

  id = Column(Integer, primary_key=True, index=True)
  user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
  filename = Column(String(255), nullable=False)
  content = Column(Text, default="")
  status = Column(String(20), default="uploaded")
  created_at = Column(DateTime, server_default=func.now())
