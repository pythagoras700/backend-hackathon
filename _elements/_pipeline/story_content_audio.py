from mistralai import Mistral
from .story_content import story_content, embed_story_content


MISTRAL_API_KEY = "K9tWkq0rrqrR1Ib2asiTpRZyMiwiFMgx"
MISTRAL_MODEL = "mistral-tiny"


async def story_content_audio(user_prompt: str, kb_id: str):
    client = Mistral(api_key=MISTRAL_API_KEY)
    collection = await story_content(user_prompt, kb_id=kb_id, client=client)
    audio_content = embed_story_content(collection["story_content"],
                                        client,
                                        enable_video=False)
    async for chunk in audio_content:
        yield chunk
