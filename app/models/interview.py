from sqlalchemy import Column, Integer, String, Text, Float, Boolean, DateTime, ForeignKey, func
from sqlalchemy.orm import relationship

from app.database import Base


class Position(Base):
  __tablename__ = "positions"

  id = Column(Integer, primary_key=True, index=True)
  title = Column(String(100), nullable=False)
  description = Column(Text, default="")
  is_builtin = Column(Boolean, default=False)
  created_at = Column(DateTime, server_default=func.now())

  interviews = relationship("Interview", back_populates="position")

  def __repr__(self):
    return f"<Position(id={self.id}, title={self.title})>"


class Interview(Base):
  __tablename__ = "interviews"

  id = Column(Integer, primary_key=True, index=True)
  user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
  position_id = Column(Integer, ForeignKey("positions.id"), nullable=False)
  status = Column(String(20), default="in_progress")
  total_score = Column(Float, nullable=True)
  created_at = Column(DateTime, server_default=func.now())
  completed_at = Column(DateTime, nullable=True)

  user = relationship("User", backref="interviews")
  position = relationship("Position", back_populates="interviews")
  questions = relationship("Question", back_populates="interview", order_by="Question.order")

  def __repr__(self):
    return f"<Interview(id={self.id}, user_id={self.user_id}, status={self.status})>"


class Question(Base):
  __tablename__ = "questions"

  id = Column(Integer, primary_key=True, index=True)
  interview_id = Column(Integer, ForeignKey("interviews.id"), nullable=False)
  content = Column(Text, nullable=False)
  answer = Column(Text, default="")
  score = Column(Float, nullable=True)
  comment = Column(Text, default="")
  order = Column(Integer, nullable=False)

  interview = relationship("Interview", back_populates="questions")

  def __repr__(self):
    return f"<Question(id={self.id}, order={self.order})>"
