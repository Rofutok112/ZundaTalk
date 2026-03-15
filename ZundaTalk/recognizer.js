const statusText = document.getElementById("status-text");
const interimText = document.getElementById("interim-text");

const WS_PORT = 8080;
const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;

let ws = null;
let recognition = null;
let isRecognizing = false;
let shouldKeepListening = true;
let reconnectTimer = null;
let isPageUnloading = false;

connectWebSocket();
recreateRecognition();
updateUi();

function connectWebSocket() {
    if (isPageUnloading) {
        return;
    }

    ws = new WebSocket(`ws://localhost:${WS_PORT}`);

    ws.onopen = () => {
        setStatus("Connected. Waiting for microphone permission...");
        updateUi();
        queueRecognitionStart();
    };

    ws.onclose = () => {
        if (isPageUnloading) {
            setStatus("Recognizer closed");
            return;
        }
        setStatus("Disconnected. Reconnecting...");
        updateUi();
        reconnectTimer = setTimeout(connectWebSocket, 1000);
    };

    ws.onerror = () => {
        setStatus("Connection error");
    };
}

function recreateRecognition() {
    if (!SpeechRecognition) {
        return;
    }

    recognition = new SpeechRecognition();
    recognition.lang = "ja-JP";
    recognition.continuous = true;
    recognition.interimResults = true;

    recognition.onstart = () => {
        isRecognizing = true;
        setStatus("Listening...");
        updateUi();
    };

    recognition.onend = () => {
        isRecognizing = false;
        interimText.textContent = "";
        updateUi();
        if (shouldKeepListening) {
            setStatus("Restarting recognition...");
            setTimeout(queueRecognitionStart, 400);
            return;
        }
        setStatus("Recognition stopped");
    };

    recognition.onerror = (event) => {
        setStatus(`Recognition error: ${event.error}`);
        if (event.error === "not-allowed" || event.error === "service-not-allowed") {
            shouldKeepListening = false;
        }
    };

    recognition.onresult = (event) => {
        let interim = "";
        for (let i = event.resultIndex; i < event.results.length; i += 1) {
            const result = event.results[i];
            const transcript = result[0].transcript.trim();
            if (!transcript) {
                continue;
            }

            if (result.isFinal) {
                interimText.textContent = "";
                sendText(transcript);
            } else {
                interim += transcript;
            }
        }
        interimText.textContent = interim;
    };
}

function queueRecognitionStart() {
    if (!shouldKeepListening || isRecognizing || !recognition || isPageUnloading) {
        return;
    }

    try {
        recognition.start();
    } catch (error) {
        if (error.name !== "InvalidStateError") {
            setStatus(`Recognition start failed: ${error.message}`);
        }
    }
}

function sendText(text) {
    if (!ws || ws.readyState !== WebSocket.OPEN) {
        setStatus("WebSocket is not connected");
        return;
    }

    ws.send(text);
    setStatus(`Sent: ${text}`);
}

function updateUi() {
    if (!SpeechRecognition) {
        setStatus("This browser does not support Chrome speech recognition");
    }
}

function setStatus(message) {
    statusText.textContent = message;
}

function shutdownRecognizer() {
    isPageUnloading = true;
    shouldKeepListening = false;

    if (reconnectTimer !== null) {
        clearTimeout(reconnectTimer);
        reconnectTimer = null;
    }

    if (recognition && isRecognizing) {
        try {
            recognition.stop();
        } catch (error) {
            setStatus(`Recognition stop failed: ${error.message}`);
        }
    }

    if (ws && ws.readyState === WebSocket.OPEN) {
        ws.close();
    }
}

window.addEventListener("beforeunload", shutdownRecognizer);
window.addEventListener("pagehide", shutdownRecognizer);
