const subtitleEl = document.getElementById('subtitle');

const syncChannel = new BroadcastChannel('subtitle_sync');

// 立ち絵側からの指示を待つ
syncChannel.onmessage = (event) => {
    if (event.data.action === "show") {
        subtitleEl.innerText = event.data.text;
    } else if (event.data.action === "clear") {
        subtitleEl.innerText = "";
    }
};

subtitleEl.innerText = "";