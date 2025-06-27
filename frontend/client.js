import PCMPlayer from "pcm-player";

const serverUrl = "ws://localhost:3000/chat";
const player = new PCMPlayer({
  encoding: "16bitInt",
  channels: 1,
  sampleRate: 24000,
  flushTime: 20,
});

let ws;
let reconnectAttempts = 0;
const maxReconnectDelay = 10000;

function connect() {
  ws = new WebSocket(serverUrl);
  ws.binaryType = "arraybuffer";

  ws.onopen = () => {
    console.log("Connected");
    reconnectAttempts = 0;

    document.getElementById("send").onclick = () => {
      const message = document.getElementById("message").value;
      if (ws.readyState === WebSocket.OPEN) {
        ws.send(message);
      }
    };
  };

  ws.onmessage = (event) => {
    if (event.data instanceof ArrayBuffer) {
      const pcmData = new Int16Array(event.data);
      player.feed(pcmData);
    } else {
      console.log("Text:", event.data);
    }
  };

  ws.onerror = console.error;
  ws.onclose = () => {
    console.warn("Connection lost. Reconnecting...");
    reconnect();
  };
}

function reconnect() {
  reconnectAttempts++;
  const delay = Math.min(1000 * 2 ** reconnectAttempts, maxReconnectDelay);
  setTimeout(connect, delay);
}

connect();
