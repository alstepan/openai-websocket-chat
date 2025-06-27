class ChatCompletionError(Exception):
  def __init__(self, details):
    self.details = details

class TTSError(Exception):
  def __init__(self, details):
    self.details = details
