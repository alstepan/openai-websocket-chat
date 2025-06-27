import asyncio
from openai import AsyncOpenAI
import logging

from .base_chat_service import BaseChatService
from .errors import ChatCompletionError, TTSError


class SdkChatService(BaseChatService):
    def __init__(self, api_key: str):
        self.client = AsyncOpenAI(api_key=api_key)
        self.chat_history = [
            {"role": "system", "content": "You are a helpful assistant."}
        ]

    async def chat_completions(self, input: str) -> str:
        """
        Makes request to OpenAI with given input. Reads data eagerly and produces final string.
        The function is also memorises previsou conversation. All the messages are passed to OpenAI on each call
        @input - a string representing a text request to OpenAI chat completion
        @return - returns a response string
        """
        try:
            self.chat_history.append({"role": "user", "content": input})
            completion = await self.client.chat.completions.create(
                model="gpt-4o-mini", messages=self.chat_history
            )

            result = completion.choices[0].message.content
            self.chat_history.append({"role": "system", "content": result})
            return result
        except Exception as e:
            logging.error(f"Chat completions error: {e}")
            raise ChatCompletionError(e)

    async def stream_tts(self, text: str):
        """
        Streams audio data from OpenAI TTS endpoint.
        @text can be sting, coroutine or callable
        @return - returns a binary audio stream in pcm format
        """
        if type(text) == "str":
            input = text
        elif asyncio.iscoroutine(text):
            input = await text
        else:
            input = text()
        try:
            async with self.client.audio.speech.with_streaming_response.create(
                model="gpt-4o-mini-tts",
                voice="coral",
                input=input,
                instructions="Speak in a cheerful and positive tone.",
                response_format="pcm",
            ) as response:
                async for chunk in response.iter_bytes(chunk_size=4096):
                    yield chunk
        except Exception as e:
            logging.error(f"Error in TTS streaming: {e}")
            raise TTSError(e)
