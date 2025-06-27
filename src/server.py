import asyncio
import os
from typing import Callable
from aiohttp import web
import logging

from chat_service import BaseChatService
from chat_service import SdkChatService
from chat_service import StreamingChatService
from functools import *
import argparse


class Server:
    def __init__(self, create_chat_service: Callable[[str], BaseChatService]):
        """
        Websocket server constructor.
        @create_chat_service - a function that creates any implementation of BaseChatService
        """
        self.app = web.Application()
        self.app.router.add_get("/chat", self.websocket_handler)
        self.clients = {}
        self.chat_factory = create_chat_service

    async def websocket_handler(self, request):
        ws = web.WebSocketResponse()
        await ws.prepare(request)
        self.clients[ws] = self.chat_factory()
        try:
            async for msg in ws:
                if msg.type == web.WSMsgType.TEXT:
                    client = self.clients[ws]
                    user_msg = msg.data
                    # send the response to autio API
                    async for pcm_chunk in client.stream_tts(
                        client.chat_completions(user_msg)
                    ):
                        if pcm_chunk is None:
                            await ws.send_str("Error: TTS failed.")
                            break
                        await ws.send_bytes(pcm_chunk)
                    await ws.send_str("__done__")
                elif msg.type == web.WSMsgType.ERROR:
                    logging.error(
                        f"WebSocket connection closed with exception: {ws.exception()}"
                    )
                    del self.clients[ws]
                    ws.close()
                elif msg.type == web.WSMsgType.CLOSE:
                    # handle closed connections
                    del self.clients[ws]
                    ws.close()
        except asyncio.CancelledError:
            logging.info("WebSocket task cancelled.")
        except Exception as e:
            logging.error(f"Unexpected server error: {e}")
            await ws.send_str(f"Server error, please contact system administrator")
        finally:
            await ws.close()
        return ws

    def run(self, host: str = "0.0.0.0", port: int = 3000):
        web.run_app(server.app, host=host, port=port)


def create_standard_chat(api_key: str) -> BaseChatService:
    return SdkChatService(api_key=api_key)


def create_streaming_chat(api_key: str) -> BaseChatService:
    return StreamingChatService(api_key=api_key)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    parser = argparse.ArgumentParser(
        description="WebSocket server for OpenAI. Accepts text messages and returns binary audio stream in PCM format"
    )
    parser.add_argument("--host", help="Host to bind the server", type=str)
    parser.add_argument("--port", help="Port for the server", type=int)
    parser.add_argument(
        "--client",
        help="OpenAI client: sdk for sdk based (default), streaming for streaming client",
        type=str,
        choices=["sdk", "streaming"],
    )
    parser.add_help = True

    args = parser.parse_args()

    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    if args.client == "streaming":
        logging.info("Starting server with streaming chat")
        server = Server(
            create_chat_service=partial(create_streaming_chat, OPENAI_API_KEY)
        )
    else:
        logging.info("Starting server with sdk-based chat")
        server = Server(
            create_chat_service=partial(create_standard_chat, OPENAI_API_KEY)
        )
    if OPENAI_API_KEY:
        host = args.host if args.host else "0.0.0.0"
        port = args.port if args.port else 3000
        server.run(host=host, port=port)
    else:
        print(
            "ERROR: cannot start the server. Please set OPEN_API_KEY environment variable"
        )
