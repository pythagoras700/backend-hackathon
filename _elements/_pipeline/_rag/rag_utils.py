import faiss
import psycopg2
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from dotenv import load_dotenv
import os
import numpy as np

load_dotenv()
embed_model = HuggingFaceEmbedding(model_name="sentence-transformers/all-MiniLM-L6-v2")


async def create_faiss_index(kb_id, documents):
    conn = psycopg2.connect(
        dbname=os.getenv("POSTGRES_DB"),
        user=os.getenv("POSTGRES_USER"),
        password=os.getenv("POSTGRES_PASSWORD"),
        host=os.getenv("POSTGRES_HOST"),
        port=os.getenv("POSTGRES_PORT"),
    )
    cur = conn.cursor()
    d = 384
    faiss_index = faiss.IndexFlatL2(d)

    embedding = embed_model.get_text_embedding(documents)
    embedding = np.array(embedding)
    faiss_index.add(embedding.reshape(1, -1))
    # Save to Postgres
    cur.execute("INSERT INTO faiss_index (embedding, text,content_id) VALUES (%s, %s,%s)",  # noqa
                (embedding.tolist(), documents, kb_id))  # type: ignore

    conn.commit()
    cur.close()
    conn.close()


async def query_postgres_faiss(query_text, kb_id, top_k=3):
    conn = psycopg2.connect(
        dbname=os.getenv("POSTGRES_DB"),
        user=os.getenv("POSTGRES_USER"),
        password=os.getenv("POSTGRES_PASSWORD"),
        host=os.getenv("POSTGRES_HOST"),
        port=os.getenv("POSTGRES_PORT"),
    )
    cur = conn.cursor()

    # Convert query to embedding
    query_embedding = embed_model.get_text_embedding(query_text)
    query_embedding = np.array(query_embedding)
    # Query PostgreSQL with pgvector's similarity search
    cur.execute(
        "SELECT text, embedding <-> %s::vector AS distance FROM faiss_index WHERE content_id = %s ORDER BY distance LIMIT %s",
        (query_embedding.tolist(), kb_id, top_k),
        )

    results = cur.fetchall()
    cur.close()
    conn.close()

    return [result[0] for result in results]