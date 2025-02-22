from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from dotenv import load_dotenv
import os
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, JSON, TEXT
from sqlalchemy.orm import Session
from pgvector.sqlalchemy import Vector

load_dotenv()
print(os.getenv("POSTGRES_USER"))

Base = declarative_base()
engine = create_engine(f"postgresql+psycopg2://{os.getenv('POSTGRES_USER')}:{os.getenv('POSTGRES_PASSWORD')}@{os.getenv('POSTGRES_HOST')}:{os.getenv('POSTGRES_PORT')}/{os.getenv('POSTGRES_DB')}")  # noqa: E501
session = sessionmaker(bind=engine)


class User(Base):
    __tablename__ = "user"
    id = Column(Integer, primary_key=True)
    email = Column(String)
    password = Column(String)
    created_at = Column(DateTime)
    updated_at = Column(DateTime)


class Collection(Base):
    __tablename__ = "collection"
    id = Column(Integer, primary_key=True)
    title = Column(String)
    rag_id = Column(Integer, ForeignKey("rag.id"))
    user_id = Column(Integer, ForeignKey("user.id"))
    interaction = Column(JSON)
    content_links = Column(String)
    created_at = Column(DateTime)
    updated_at = Column(DateTime)


class FaissIndex(Base):
    __tablename__ = "faiss_index"
    id = Column(Integer, primary_key=True, autoincrement=True)
    content_id = Column(String)
    embedding = Column(Vector(384))
    text = Column(TEXT)


Base.metadata.create_all(bind=engine)


async def get_db():
    db = session()
    try:
        yield db
    finally:
        db.close()
