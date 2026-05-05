from sqlalchemy import Column, Integer, String, ForeignKey
from app.core.database import Base

class Chunk(Base):
    __tablename__ = "chunks"

    chunk_id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id"))
    chunk_content = Column(String)