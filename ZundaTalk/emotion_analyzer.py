import warnings
warnings.filterwarnings('ignore')

import os
os.environ['TOKENIZERS_PARALLELISM'] = 'false'

import torch
import transformers
from transformers import AutoTokenizer, AutoModelForSequenceClassification

transformers.logging.set_verbosity_error()


WRIME_LABELS = [
    "joy",          # 喜び
    "sadness",      # 悲しみ
    "anticipation", # 期待
    "surprise",     # 驚き
    "anger",        # 怒り
    "fear",         # 恐れ
    "disgust",      # 嫌悪
    "trust",        # 信頼
]

EMOTION_TO_EXPRESSION = {
    "joy":          "happy",
    "sadness":      "sad",
    "anger":        "angry",
    "surprise":     "surprised",
    "anticipation": "normal",
    "fear":         "sad",
    "disgust":      "angry",
    "trust":        "normal",
}

MODEL_NAME = "patrickramos/bert-base-japanese-v2-wrime-fine-tune"
MAX_SEQ_LENGTH = 512


class EmotionAnalyzer:
    def __init__(self):
        print("[感情分析] モデルを読み込み中...")
        self.tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
        self.model = AutoModelForSequenceClassification.from_pretrained(MODEL_NAME)
        self.model.eval()
        print("[感情分析] モデルの読み込みが完了しました。")

    def analyze(self, text: str) -> str:
        """
        テキストから感情を推定し、立ち絵の表情名を返す。

        Args:
            text: 分析対象のテキスト

        Returns:
            表情名 ("normal", "happy", "sad", "angry", "surprised")
        """
        if not text or not text.strip():
            return "normal"

        tokens = self.tokenizer(
            text,
            truncation=True,
            max_length=MAX_SEQ_LENGTH,
            padding="max_length",
            return_tensors="pt",
        )

        with torch.no_grad():
            output = self.model(
                input_ids=tokens["input_ids"],
                attention_mask=tokens["attention_mask"],
            )

        # 先頭8個が writer 側の感情スコア（回帰値）
        scores = output.logits[0][:8]
        max_index = torch.argmax(scores).item()
        wrime_label = WRIME_LABELS[max_index]
        expression = EMOTION_TO_EXPRESSION.get(wrime_label, "normal")

        print(f"[感情分析] \"{text}\" → {wrime_label}({expression})")

        return expression
