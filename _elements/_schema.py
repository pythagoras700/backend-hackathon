from pydantic import BaseModel, Field
from typing import List, Optional
from fastapi import UploadFile
from pydantic import model_validator

STORY_CONTENT = ""


class VoiceConfig(BaseModel):
    voice_id: str = Field(
        description="The id of the voice",
        default="bot"
    )
    language: str = Field(default="en-US")
    speed: float = Field(
        description="The speed of the voice",
        default=1.0
    )


class ListnerMetadata(BaseModel):
    name: str
    age: int
    gender: str
    location: str
    interests: List[str]


class ListenerInformation(BaseModel):
    listener_metadata: ListnerMetadata
    overall_prompt: str
    kb_id: Optional[str] = None


class ToolResponse(BaseModel):
    content: dict
    tool_name: str
    break_chat_loop: bool = False


class CreateCollection(BaseModel):
    title: str


class GenerateVideoContent(BaseModel):
    rag_id: str = Field(
        description="The id of the RAG collection",
        default=STORY_CONTENT
    )
    prompt: str = Field(
        description="The prompt to generate the video content",
        )

    @model_validator(mode="after")
    def validate_prompt(self):
        if self.prompt == "":
            raise ValueError("Prompt cannot be empty")
        return self
