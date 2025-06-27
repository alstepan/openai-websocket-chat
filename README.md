# openai-websocket-chat

A test project to play with chat completions and tts OpenAI api's.
The server contains two implementations:

- OpenAI SDK-based
- Pure aiohttp streaming implementation (should mimimize the memory usage assumimg OPENAI allows to send messages larger than 4096 chars to TTS API)

Server protocol:

- Server waits for text message from the websocket
- Server responds with a chunk of binary messages containing PCM audio (so that audio could be streamed close to real time).
- Once all audio data is sent the server sends text message `__done__`.

The implementation can be chosen during the server startup. The server stores previsou chat history in RAM (should be replaced in production-grade code).\
I tried to minimise number of dependencies and also implement streaming where possible

# Prerequisites:

- Python 3.11
- Python environment and installed requirements from requirements txt.
- (Optional) npm to run html/javascript client

## Create python environment and install the requirements:

```
$ python -m venv .venv
$ source ./.venv/bin/activate
$ python -m pip install -r requirements.txt
```

# Running the backend server:

Note: please make sure the python environment is activated before you start the server
Setup OPENAI_API_KEY environment variable:

```
$ export OPENAI_API_KEY=<your api key>
```

Launch the server

```
$ python src/server.py

```

By default the server runs on `ws://localhost:3000/chat`\
Note: server is configurable, you can see all available parameters by running `python src/server.py --help`

# Running test clients

There are two clients availabe: html/javascript and python

## Running python client

Note: please make sure the python environment is activated in the terminal before you start the client

```
$ python test/test_client.py
```

Client is also configurable, use `--help` option to see available option\
Client plays audio using sounddevice librady.

## Running html/javasctip client

Run following commands:

```
$ cd frontend
$ npm install
$ npm start
```

Open browser and enter the message. Listen to the server response.
Note: The frontend is very very draft.
