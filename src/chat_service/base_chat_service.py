class BaseChatService:
    """
    An interface representing chat service. There is no useful implementation here
    """

    async def chat_completions(self, message: str):
        raise Exception("Not implemented")

    async def stream_tts(self, text: str):
        raise Exception("Not implemented")
