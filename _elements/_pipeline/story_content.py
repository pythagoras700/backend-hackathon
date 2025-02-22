from ._rag import query_postgres_faiss
import json
from elevenlabs.client import ElevenLabs
from mistralai import Mistral
from cachetools import cached  # type: ignore
import random
import base64
import fal_client
import os
from moviepy import *  # type: ignore
from .fuzzy import cache  # type: ignore
import openai


MISTRAL_MODEL = "mistral-tiny"
ELEVENLABS_API_KEY = "sk_6a3784fb87c1f208276c54b59fed6753e182e41c7b2da0d0"
FAL_API_KEY = "f12f373e-0e23-4415-9c4a-28025c8ff687:3c0f38824a435f9222fda4a28fd23813"  # noqa
MISTRAL_API_KEY = "K9tWkq0rrqrR1Ib2asiTpRZyMiwiFMgx"

voices = [
    "9BWtsMINqrJLrRacOk9x",
    "CwhRBWXzGAHq8TQ4Fs17",
    "EXAVITQu4vr4xnSDxMaL",
    "FGY2WhTYpPnrIDTdsKH5",
    "IKne3meq5aSn9XLyUdCD",
    "JBFqnCBsd6RMkjVDRZzb",
    "N2lVS1w4EtoT3dr4eOWO",
    "SAz9YHcvj6GT2YYXdXww",
    "TX3LPaxmHKxFdv7VOQHJ",
]


async def img_to_video(prompt: str):
    if cache.get(prompt):
        return cache.get(prompt)
    stream = fal_client.stream_async(
        "workflows/vrs-darkness/test",
        arguments={
            "prompt": prompt,
            "prompt_enhancement": True,
            "seed": 0
        },
    )

    buffer = b""
    async for event in stream:
        buffer += event['video']
    cache.add(prompt, buffer)
    return buffer


@cached
def get_random_voice(narrator_voice: str):
    if narrator_voice == "narrator":
        return "JBFqnCBsd6RMkjVDRZzb"
    else:
        return random.choice(voices)


async def story_content(user_prompt: str, kb_id: str, client: Mistral):
    collection_best_sellers = await query_postgres_faiss(user_prompt, "bestseller")  # noqa
    collection_kb = await query_postgres_faiss(user_prompt, kb_id)  # noqa

    system_prompt = f""" You are an expert storyteller.
    Here are how closely related best sellers books abstract and the flow will look like:
    {collection_best_sellers}

    Here are how closely related creative ideas u can take as example:
    {collection_kb}

    Now, user will give a short descirption of the storyand you need to generate a story content for the user prompt. # noqa
    Please generate a story content for the user prompt.
    Make sure the story content is closely related to the user prompt & let it be creative. Make sure you also generate a short summary of the story content that will reflect the environment
    in which the story takes place.
    please follow json format for the response.
    {{
        "story_content": "story_content",
        "summary": "summary"
    }}
    """  # noqa
    client = openai.OpenAI(api_key=MISTRAL_API_KEY, base_url="https://api.mistral.ai/v1")
    content = client.chat.completions.create(
        model=MISTRAL_MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],  # type: ignore
        stream=False    
    )
    buffer = content.choices[0].message.content
    try:
        content = json.loads(buffer)
        return content
    except Exception as e:
        print(e)
        try:
            buffer = buffer.replace("'", '"')
            print(buffer)
            content = json.loads(buffer)
            return content
        except Exception as e:
            print(e)
            print(buffer)


async def embed_story_content(
    story_content: str,
    client: Mistral,
    enable_video: bool = False,
):
    if enable_video:
        system_prompt = """You are a helpful assistant that can answer questions and help with tasks. You will be given a story and must generate a scene prompt and transcript for narration. 
        Ensure that whenever the cartoon speaks, the video generation prompt is appropriate. Keep the video prompt within 15 words. In The Trancript add periods and spaces and make words in capital letters. all those have emotion. also add exlamatory marks in case of excitement.
        Add "..." in case of pause. In case of success make it in capital letters etc.. generate has many scenes.
        Follow this JSON format:
        [{"video_prompt": "prompt", "transcript": "transcript", "speaker": "narrator/cartoon"}....]"""  # noqa
    else:
        system_prompt = """You are a helpful assistant that can answer questions and help with tasks. You will be given a story you mush generate a transcript for narration. Ensure that whenever the cartoon speaks, the video generation prompt is appropriate. Keep the video prompt within 15 words. In The Trancript add periods and spaces and make words in capital letters. all those have emotion. also add exlamatory marks in case of excitement.
        Add "..." in case of pause. In case of success make it in capital letters etc.. generate has many scenes.
        Follow this JSON format:
        [{"transcript": "transcript", "speaker": "narrator/cartoon"}....]"""  # noqa
    openai_client = openai.OpenAI(api_key=MISTRAL_API_KEY, base_url="https://api.mistral.ai/v1")
    response = openai_client.chat.completions.create(
        model=MISTRAL_MODEL,
        messages=[
            {
                "role": "system",
                "content": system_prompt
            },
            {
                "role": "user",
                "content": """{story_content}""",  # noqa
            },
        ],  # type: ignore
        stream=True
    )
    buffer = ""
    for chunk in response:
        if chunk.choices[0].delta.content is not None:
            buffer += chunk.choices[0].delta.content
            # Try parsing as a JSON array
            try:
                partial_json = json.loads(buffer)
                if not enable_video:
                    audio_bytes = process_audio_data(partial_json, partial_json["speaker"], False)  # noqa
                    print(partial_json)
                    yield {"audio": audio_bytes, "speaker": partial_json["speaker"]}  # noqa
                else:
                    print(partial_json)
                    audio_bytes = process_audio_data(partial_json, partial_json["speaker"], True)  # noqa
                    video_bytes = process_video_data(partial_json, partial_json["speaker"], audio_bytes)  # noqa
                    yield {"video": video_bytes}

                buffer = ""  # Clear buffer after successful processing
            except json.JSONDecodeError:
                pass  # Incomplete JSON, wait for more data


async def process_audio_data(scene: dict, speaker: str, enable_video: bool):
    client = ElevenLabs(api_key=ELEVENLABS_API_KEY)
    VOICE_ID = get_random_voice(speaker)
    audio_bytes_iterator = client.text_to_speech.convert(
        text=scene["transcript"],
        voice_id=VOICE_ID,
        model_id="eleven_multilingual_v2",
        output_format="mp3_44100_128",
    )
    if not enable_video:
        audio_bytes = b"".join(audio_bytes_iterator)
        audio_base64 = base64.b64encode(audio_bytes).decode("utf-8")
        return audio_base64
    else:
        return audio_bytes_iterator


async def process_video_data(scene: dict, speaker: str, audio_bytes):
    video_bytes = await img_to_video(scene["video_prompt"])
    with open("videos/video1.mp4", "wb") as f:
        f.write(video_bytes)
    video = VideoFileClip("videos/video1.mp4")
    with open("videos/audio1.mp3", "wb") as f:
        audio = b"".join(audio_bytes)
        f.write(audio)
    audio = AudioFileClip("videos/audio1.mp3")
    video.set_audio(audio)
    video.write_videofile("videos/video.mp4", codec="libx264")
    os.remove("videos/video1.mp4")
    os.remove("videos/audio1.mp3")
    with open("videos/video.mp4", "rb") as f:
        video_bytes = f.read()
    return video_bytes
