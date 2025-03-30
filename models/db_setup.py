from sqlalchemy import create_engine, Column, Integer, String, ForeignKey, Date, Text
from sqlalchemy.orm import relationship, declarative_base
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime 

# Define the database file
DATABASE_URL = "sqlite:///quiz_master.db"

# Create an engine and base
engine = create_engine(DATABASE_URL, echo=True)
Base = declarative_base()

# === USER MODEL ===
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    email = Column(String, unique=True, nullable=False)
    password_hash = Column(String, nullable=False)
    full_name = Column(String, nullable=False)
    qualification = Column(String)
    dob = Column(Date)
    role = Column(String, nullable=False, default="user")  # "user" or "admin"

    scores = relationship("Score", back_populates="user")  # One-to-Many with Score

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


# === SUBJECT MODEL ===
class Subject(Base):
    __tablename__ = 'subjects'
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)

    chapters = relationship('Chapter', back_populates='subject')  



# === CHAPTER MODEL ===

class Chapter(Base):
    __tablename__ = 'chapters'
    id = Column(Integer, primary_key=True)
    chapter_name = Column(String, nullable=False)
    subject_id = Column(Integer, ForeignKey('subjects.id'))
    
    subject = relationship('Subject', back_populates='chapters')   # ✅ Define relationship



# === QUIZ MODEL ===
class Quiz(Base):
    __tablename__ = 'quizzes'
    id = Column(Integer, primary_key=True)
    quiz_name = Column(String, nullable=False)
    
    # Correct relationship
    questions = relationship('Question', back_populates='quiz')    
    scores = relationship('Score', back_populates='quiz')


# === QUESTION MODEL ===
class Question(Base):
    __tablename__ = 'questions'
    id = Column(Integer, primary_key=True)
    question_text = Column(String, nullable=False)
    quiz_id = Column(Integer, ForeignKey('quizzes.id'))
    
    quiz = relationship('Quiz', back_populates='questions')  # Many-to-One with Quiz


# === SCORE MODEL ===
class Score(Base):
    __tablename__ = "scores"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    quiz_id = Column(Integer, ForeignKey("quizzes.id"))
    score_value = Column(Integer, nullable=False)


    user = relationship("User", back_populates="scores")  # Many-to-One with User
    quiz = relationship("Quiz", back_populates="scores")  # Many-to-One with Quiz


# Create tables in the database
Base.metadata.create_all(engine)
