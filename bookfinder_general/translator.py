"""Translation module for BookFinder.

Translates extracted book text to English for AI consumption.
Uses free translation APIs — output is optimized for machine readability,
not human publication quality.
"""

import re
import time


def translate_text(text: str, source_lang: str = "auto", target_lang: str = "en") -> str:
    """
    Translate text to the target language.

    Splits text into chunks to handle API limits, preserves markdown formatting.
    Uses Google Translate via deep-translator (free, no API key needed).

    Args:
        text: The markdown text to translate.
        source_lang: Source language code (e.g. 'de', 'fr') or 'auto' to detect.
        target_lang: Target language code (default: 'en').

    Returns:
        Translated text with markdown structure preserved.
    """
    if not text.strip():
        return text

    # Don't translate if already in target language
    if source_lang == target_lang:
        return text

    from deep_translator import GoogleTranslator

    translator = GoogleTranslator(source=source_lang, target=target_lang)

    # Split into chunks that respect paragraph boundaries
    # Google Translate has a ~5000 char limit per request
    chunks = _split_for_translation(text, max_chars=4500)

    translated_chunks = []
    for i, chunk in enumerate(chunks):
        # Skip chunks that are only markdown formatting / whitespace
        if not chunk.strip() or re.match(r"^[\s\-#=|>*`~\n]+$", chunk):
            translated_chunks.append(chunk)
            continue

        try:
            result = translator.translate(chunk)
            translated_chunks.append(result)
        except Exception:
            # If translation fails for a chunk, keep original
            translated_chunks.append(chunk)

        # Rate limiting — be polite to the free API
        if i < len(chunks) - 1:
            time.sleep(0.5)

    return "\n\n".join(translated_chunks)


def _split_for_translation(text: str, max_chars: int = 4500) -> list[str]:
    """Split text into translation-friendly chunks at paragraph boundaries."""
    paragraphs = text.split("\n\n")
    chunks = []
    current_chunk = ""

    for para in paragraphs:
        # If a single paragraph exceeds max, split it by sentences
        if len(para) > max_chars:
            if current_chunk:
                chunks.append(current_chunk.strip())
                current_chunk = ""
            sentence_chunks = _split_by_sentences(para, max_chars)
            chunks.extend(sentence_chunks)
            continue

        if len(current_chunk) + len(para) + 2 > max_chars:
            chunks.append(current_chunk.strip())
            current_chunk = para
        else:
            current_chunk = current_chunk + "\n\n" + para if current_chunk else para

    if current_chunk.strip():
        chunks.append(current_chunk.strip())

    return chunks


def _split_by_sentences(text: str, max_chars: int) -> list[str]:
    """Split a long paragraph into sentence-based chunks."""
    sentences = re.split(r"(?<=[.!?])\s+", text)
    chunks = []
    current = ""

    for sentence in sentences:
        if len(current) + len(sentence) + 1 > max_chars:
            if current:
                chunks.append(current.strip())
            current = sentence
        else:
            current = current + " " + sentence if current else sentence

    if current.strip():
        chunks.append(current.strip())

    return chunks


def detect_language(text: str) -> str:
    """
    Detect the language of a text sample.

    Returns ISO 639-1 language code (e.g. 'en', 'de', 'fr').
    """
    # Take a sample from the middle of the text for better detection
    sample = text[len(text)//4 : len(text)//4 + 2000]

    try:
        from deep_translator import single_detection
        return single_detection(sample, api_key="")  # Uses free detection
    except Exception:
        pass

    # Fallback: simple heuristic based on common words
    sample_lower = sample.lower()
    lang_indicators = {
        "de": ["und", "der", "die", "das", "ist", "von", "mit", "auch", "auf", "den"],
        "fr": ["les", "des", "une", "est", "dans", "pour", "pas", "sur", "avec", "que"],
        "es": ["los", "las", "del", "una", "por", "con", "para", "como", "que", "más"],
        "it": ["gli", "del", "una", "per", "con", "che", "sono", "come", "più", "nel"],
        "pt": ["dos", "das", "uma", "por", "com", "para", "como", "que", "mais", "não"],
        "ru": ["что", "это", "как", "для", "при", "или", "все", "они", "его", "так"],
        "nl": ["het", "een", "van", "dat", "met", "zijn", "voor", "ook", "aan", "maar"],
        "la": ["est", "sunt", "cum", "sed", "non", "quod", "enim", "etiam", "aut", "quae"],
    }

    scores = {}
    for lang, words in lang_indicators.items():
        scores[lang] = sum(1 for w in words if f" {w} " in f" {sample_lower} ")

    if scores:
        best = max(scores, key=scores.get)
        if scores[best] >= 3:
            return best

    return "en"  # Default assumption
