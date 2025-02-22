from fastapi import APIRouter, HTTPException, Depends, UploadFile, File
from fastapi.responses import JSONResponse, StreamingResponse
from db import get_db, Session
from ._schema import GenerateVideoContent  # type: ignore
import pypdf
from fastapi import WebSocket
from ._pipeline import (
    story_content_audio,
    story_content_video,
    create_faiss_index,
    query_postgres_faiss
)
import fitz  # PyMuPDF
from io import BytesIO
import re
from .db import query_rag_db
router = APIRouter(
    prefix="/api",
    tags=["api"]
)


def remove_control_chars(text):
    return re.sub(r"[\x00-\x1F\x7F]", "", text)


@router.post("/rag/create_collection")
async def create_collection(
    title: str,
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    try:
        if file.content_type == "application/pdf":
            file_content = BytesIO(await file.read())
            pdf_reader = pypdf.PdfReader(file_content)
            file_content = ""
            for page in pdf_reader.pages:
                file_content += page.extract_text()
        else:
            file_content = await file.read()
        await create_faiss_index(title, remove_control_chars(file_content))
        return JSONResponse(content={"message": "Collection created successfully"}, status_code=200)  # noqa: E501
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/get/all_collections")
async def get_all_collections(db: Session = Depends(get_db)):
    try:
        response = await query_rag_db(db)
        return JSONResponse(content=response, status_code=200)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/generate/video/content")
async def generate_video_content(
    info: GenerateVideoContent,
    db: Session = Depends(get_db)
):
    video_content = await story_content_video(info.prompt, info.rag_id)
    print(video_content)
    return StreamingResponse(video_content, media_type="video/mp4")  # noqa


@router.websocket("/generate/audio/content/ws")
async def generate_audio_content(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_text()
            async for chunk in story_content_audio(data, "1"):
                await websocket.send_bytes(chunk)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
