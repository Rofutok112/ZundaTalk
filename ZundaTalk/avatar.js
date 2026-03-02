let ws = null;
const layerBase = document.getElementById('layer-base');
const layerMouth = document.getElementById('layer-mouth');
const layerEyes = document.getElementById('layer-eyes');
let audioElement = null;
let timeline = [];

// ── 現在の表情 ──
let currentEmotion = 'normal';

// ── 表情ごとの画像パス ──
const EXPRESSIONS = ['normal', 'happy', 'angry', 'sad', 'surprised'];

function getBasePath(emotion) {
    return `Images/base_${emotion}/base_${emotion}.png`;
}

function getEyeOpenPath(emotion) {
    return `Images/base_${emotion}/base_${emotion}_eye.png`;
}

const CLOSED_EYE_PATH = 'Images/closed_eye.png';

// 用意した口画像のファイル名
const mouthImages = {
    'a': 'Images/mouth_a.png',
    'i': 'Images/mouth_i.png',
    'u': 'Images/mouth_u.png',
    'e': 'Images/mouth_e.png',
    'o': 'Images/mouth_o.png',
    'n': 'Images/mouth_n.png'
};

ws = new WebSocket('ws://localhost:8080');

let audioQueue = [];
let isPlaying = false;
const syncChannel = new BroadcastChannel('subtitle_sync');

ws.onmessage = (event) => {
    const data = JSON.parse(event.data);

    if (data.type === "play_voice") {
        audioQueue.push(data);

        playNext();
    }
};

function playNext() {
    if (isPlaying || audioQueue.length === 0) {
        return;
    }

    isPlaying = true;
    const data = audioQueue.shift();

    syncChannel.postMessage({ action: "show", text: data.text });

    // ── 表情の切り替え ──
    if (data.emotion && EXPRESSIONS.includes(data.emotion)) {
        setEmotion(data.emotion);
    }

    audioElement = new Audio("data:audio/wav;base64," + data.audio_b64);

    if (data.query) {
        buildTimeline(data.query);
    } else {
        timeline = [];
    }

    audioElement.onended = () => {
        syncChannel.postMessage({ action: "clear" });
        isPlaying = false;
        layerMouth.src = mouthImages['n'];
        playNext();
    };

    audioElement.play().catch(e => {
        console.error("音声再生エラー:", e);
        isPlaying = false;
        playNext();
    });

    requestAnimationFrame(updateLipSync);
}

// ── 表情切り替え ──
function setEmotion(emotion) {
    if (currentEmotion === emotion) return;

    currentEmotion = emotion;
    layerBase.src = getBasePath(emotion);
    layerEyes.src = getEyeOpenPath(emotion);
    console.log(`[表情] ${emotion} に切り替え`);
}

function buildTimeline(query) {
    timeline = [];
    let currentTime = query.prePhonemeLength || 0.1;
    timeline.push({ time: 0, mouth: 'n' });

    if (query.accent_phrases) {
        query.accent_phrases.forEach(phrase => {
            if (phrase.moras) {
                phrase.moras.forEach(mora => {
                    const c_len = mora.consonant_length || 0;
                    if (c_len > 0) {
                        timeline.push({ time: currentTime, mouth: 'n' });
                        currentTime += c_len;
                    }

                    const v_len = mora.vowel_length || 0;
                    if (mora.vowel) {
                        const v = mora.vowel.toLowerCase();
                        const mouthShape = ['a', 'i', 'u', 'e', 'o'].includes(v) ? v : 'n';
                        timeline.push({ time: currentTime, mouth: mouthShape });
                        currentTime += v_len;
                    }
                });
            }
            if (phrase.pause_mora) {
                const p_c_len = phrase.pause_mora.consonant_length || 0;
                const p_v_len = phrase.pause_mora.vowel_length || 0;
                timeline.push({ time: currentTime, mouth: 'n' });
                currentTime += (p_c_len + p_v_len);
            }
        });
    }
    timeline.push({ time: currentTime, mouth: 'n' });
}

function updateLipSync() {
    if (!audioElement || audioElement.paused || audioElement.ended) {
        layerMouth.src = mouthImages['n'];
        return;
    }

    const t = audioElement.currentTime;
    let currentMouth = 'n';
    for (let i = timeline.length - 1; i >= 0; i--) {
        if (t >= timeline[i].time) {
            currentMouth = timeline[i].mouth;
            break;
        }
    }

    layerMouth.src = mouthImages[currentMouth] || mouthImages['n'];

    requestAnimationFrame(updateLipSync);
}

// ── まばたき（現在の表情に対応）──
function blink() {
    if (!layerEyes) return;

    // 目を閉じる（共通画像）
    layerEyes.src = CLOSED_EYE_PATH;

    setTimeout(() => {
        // 目を開く（現在の表情に対応した目の画像）
        layerEyes.src = getEyeOpenPath(currentEmotion);
    }, 150);

    const nextBlinkTime = Math.random() * 3000 + 3000;
    setTimeout(blink, nextBlinkTime);
}

blink();