import aiohttp
import json
from .base_chat_service import BaseChatService
from .errors import *
import logging


class StreamingChatService(BaseChatService):
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.chat_history = [
            {"role": "system", "content": "You are a helpful assistant."}
        ]

    async def chat_completions(self, message: str):
        """
        Streams response from chat completion endpoint. Memorises previous conversation.
        All messages from the history are being passed to OpenAI
        @message - an input string
        @return - returns a text stream representing OpenAI answer on the message
        """
        self.chat_history.append({"role": "user", "content": message})
        url = "https://api.openai.com/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        async def payload():
            yield '{ "model" : "gpt-4o-mini", "stream": true, '.encode("utf-8")
            yield '"messages" : ['.encode("utf-8")
            for ind, message in enumerate(self.chat_history):
                yield json.dumps(message).encode("utf-8")
                if ind != len(self.chat_history) - 1:
                    yield ",".encode("utf-8")
            yield "]}".encode("utf-8")

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=headers, data=payload()) as resp:
                    if resp.ok:
                        self.chat_history.append({"role": "system", "content": ""})
                        async for line in resp.content:
                            if line.startswith(b"data: "):
                                data = line[6:].strip()
                                if data == b"[DONE]":
                                    break
                                if data:
                                    chunk = json.loads(data)
                                    delta = chunk["choices"][0]["delta"]
                                    if "content" in delta:
                                        self.chat_history[-1]["content"] += delta[
                                            "content"
                                        ]
                                        yield delta["content"]
                    else:
                        raise ChatCompletionError(await resp.content.read())
        except Exception as e:
            logging.error(f"Chat completion error: {e}")
            raise ChatCompletionError(e)

    async def stream_tts(self, text_stream):
        """
        Stream PCM audio chunks from OpenAI TTS API.
        @text_stream is an async generator producing text tokens
        @return - returns audio stream in PCM format
        """

        async def payload():
            yield '{ "model": "gpt-4o-mini-tts", "voice": "alloy", "response_format": "pcm", "input": "'.encode(
                "utf-8"
            )
            async for t in text_stream:
                yield t.replace('"', '\\"').replace("\n", " ").encode("utf-8")
            yield '"}'.encode("utf-8")

        url = "https://api.openai.com/v1/audio/speech"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json; charset=utf-8",
        }
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=headers, data=payload()) as resp:
                    if not resp.ok:
                        error_text = await resp.text()
                        raise Exception(
                            f"OpenAI TTS API error: {resp.status} {error_text}"
                        )

                    async for chunk in resp.content.iter_chunked(4096):
                        yield chunk
        except Exception as e:
            logging.error(f"Error in TTS streaming: {e}")
            raise TTSError(e)
