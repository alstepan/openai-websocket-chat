import numpy as np
import sounddevice as sd
import aiohttp
import argparse
import logging
import asyncio

SAMPLE_RATE = 24000
CHANNELS = 1
DTYPE = "int16"


async def play(ws, message: str):

    # Open audio output stream
    with sd.OutputStream(
        samplerate=SAMPLE_RATE,
        channels=CHANNELS,
        dtype=DTYPE,
        blocksize=0,  # lowest possible latency
    ) as stream:
        await ws.send_str(message)
        print("Receiving and playing PCM audio...")

        async for msg in ws:
            if msg.type == aiohttp.WSMsgType.BINARY:
                audio = np.frombuffer(msg.data, dtype=np.int16)
                stream.write(audio)
            elif msg.type == aiohttp.WSMsgType.TEXT and msg.data == "__done__":
                break
            elif msg.type in (
                aiohttp.WSMsgType.CLOSE,
                aiohttp.WSMsgType.CLOSED,
            ):
                print("WebSocket is closed by server")
                break
            elif msg.type == aiohttp.WSMsgType.ERROR:
                print("WebSocket error:", ws.exception())
                break


async def main(uri: str):
    try:
        print("Type 'exit' to exit the chat")
        async with aiohttp.ClientSession() as session:
            async with session.ws_connect(uri) as ws:
                message = ""
                while True:
                    message = input("Enter your message: ")
                    if message.lower() == "exit":
                        print("Exiting...")
                        break
                    await play(ws, message)
                await ws.close()
                await session.close()
    except Exception as e:
        print(f"Error while connecting to the websocket: {e}")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    parser = argparse.ArgumentParser(
        description="WebSocket test client. Plays PCM output of the websocket server"
    )
    parser.add_argument("--url", help="Wbesocket server url", type=str)
    parser.add_help = True

    args = parser.parse_args()
    uri = "ws://localhost:3000/chat" if not args.url else args.url
    asyncio.run(main(uri))
