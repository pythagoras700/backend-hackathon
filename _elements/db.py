from sqlalchemy.orm import Session
from  sqlalchemy import select
from db import FaissIndex
from ._schema import CreateCollection


async def query_rag_db(db: Session):
    """
    Query the database to get all the collections
    """
    try:
        content = select(FaissIndex.content_id)
        content = db.execute(content).scalars().all()
        print(content)
        return content
    except Exception as e:
        raise e


async def insert_db(db: Session, query: CreateCollection):
    """
    Insert a new collection into the database
    """
    try:
        db.add(query)
        db.commit()
        return query
    except Exception as e:
        raise e
