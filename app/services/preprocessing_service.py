import re
import string

from app.schemas.ai import PreprocessedMessage


HINGLISH_NORMALIZATION = {
    "acha": "good",
    "accha": "good",
    "achha": "good",
    "badhiya": "good",
    "badiya": "good",
    "sasta": "affordable",
    "sasti": "affordable",
    "mehenga": "expensive",
    "mahenga": "expensive",
    "dikhao": "show",
    "dikhana": "show",
    "chahiye": "want",
    "chaie": "want",
    "chaye": "want",
    "mujhe": "me",
    "ladies": "women",
    "gents": "men",
}

SHORT_FORMS = {
    "tshirt": "t-shirt",
    "tee": "t-shirt",
    "pls": "please",
    "plz": "please",
    "mob": "mobile",
    "phn": "phone",
    "blk": "black",
    "wht": "white",
    "grn": "green",
}

BASIC_SPELLING = {
    "shrit": "shirt",
    "shrt": "shirt",
    "sneker": "sneaker",
    "sneekers": "sneakers",
    "kurthi": "kurti",
    "denm": "denim",
}

STOPWORDS = {
    "a",
    "an",
    "and",
    "are",
    "for",
    "hai",
    "hain",
    "he",
    "i",
    "is",
    "ka",
    "ke",
    "ki",
    "ko",
    "me",
    "mere",
    "please",
    "the",
    "to",
    "with",
}

PRODUCT_KEEP_WORDS = {
    "black",
    "blue",
    "brand",
    "cheap",
    "discount",
    "green",
    "men",
    "price",
    "red",
    "sale",
    "shirt",
    "size",
    "t-shirt",
    "under",
    "white",
    "women",
}

DEVANAGARI_RE = re.compile(r"[\u0900-\u097f]")
TOKEN_RE = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)?")


class PreprocessingService:
    def preprocess_user_message(self, raw_text: str | None) -> PreprocessedMessage:
        text = (raw_text or "").strip().lower()
        detected_language = self._detect_language(text)

        text = text.translate(str.maketrans({char: " " for char in string.punctuation if char != "-"}))
        text = re.sub(r"\s+", " ", text).strip()

        tokens = []
        for token in TOKEN_RE.findall(text):
            normalized = SHORT_FORMS.get(token, token)
            normalized = HINGLISH_NORMALIZATION.get(normalized, normalized)
            normalized = BASIC_SPELLING.get(normalized, normalized)
            tokens.append(normalized)

        keywords = [
            token
            for token in tokens
            if token not in STOPWORDS or token in PRODUCT_KEEP_WORDS
        ]
        cleaned_text = " ".join(keywords)

        return PreprocessedMessage(
            cleaned_text=cleaned_text,
            detected_language=detected_language,
            keywords=list(dict.fromkeys(keywords)),
        )

    def _detect_language(self, text: str) -> str:
        if DEVANAGARI_RE.search(text):
            return "hi"
        if any(word in text.split() for word in HINGLISH_NORMALIZATION):
            return "hinglish"
        return "en"


def preprocessUserMessage(raw_text: str | None) -> dict:
    return PreprocessingService().preprocess_user_message(raw_text).model_dump()
