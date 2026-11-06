"""Readability for reading passages (Foxes Reading on): word counts and the Flesch-Kincaid grade.

FK grade = 0.39 × (words / sentences) + 11.8 × (syllables / words) − 15.59.

Kept deliberately simple and frozen: verify, the tests and the people writing passages all use
these same functions, so a passage's score never depends on which tool measured it.
- Words: runs of letters/digits, with inner apostrophes or hyphens ("didn't", "well-known" = 1 word).
- Sentences end at . ! or ? (plus any closing quote) when the next word starts with a capital
  letter or an opening quote, or at the end of a paragraph. So `"Wait!" said Mia.` is one sentence,
  and so is `Mr. Grant waved.` (no break after Mr. / Mrs. / Ms. / Dr.).
- Syllables: vowel groups, minus a silent final -e / -es / -ed, at least 1; a few exceptions by hand.

    uv run python -m ws.readability file.txt      # or the text on stdin
"""

from __future__ import annotations

import re

_WORD = re.compile(r"[A-Za-z0-9]+(?:['’-][A-Za-z0-9]+)*")
_SENTENCE_END = re.compile(r"(?<!\bMr)(?<!\bMrs)(?<!\bMs)(?<!\bDr)[.!?]+[\"”’')]*(?=\s+[\"“'(]?[A-Z0-9]|\s*$)")

# Words the vowel-group rule miscounts (checked by hand).
_SYLLABLES = {
    "every": 3, "everyone": 3, "everything": 3, "family": 3, "different": 3, "idea": 3, "ideas": 3,
    "quiet": 2, "quietly": 3, "lion": 2, "lions": 2, "poem": 2, "create": 2, "created": 3, "piano": 3,
    "area": 3, "really": 3, "radio": 3, "video": 3, "people": 2, "maybe": 2, "something": 2,
    "someone": 2, "sometimes": 2, "somewhere": 2, "become": 2, "before": 2, "lonely": 2,
    "lovely": 2, "safely": 2, "nicely": 2, "lately": 2, "wise": 1, "fire": 1, "tired": 1, "hour": 1,
    "our": 1, "flour": 2, "flower": 2, "flowers": 2, "science": 2, "giant": 2, "being": 2, "seeing": 2,
    "going": 2, "doing": 2, "toward": 2, "towards": 2, "the": 1, "are": 1, "were": 1, "there": 1,
    "where": 1, "here": 1, "smiled": 1, "liked": 1, "named": 1, "used": 1, "aunt": 1,
    "museum": 3, "cereal": 3, "violin": 3, "tomato": 3, "potato": 3, "banana": 3,
}


def words(text: str) -> list[str]:
    return _WORD.findall(text)


def sentences(text: str) -> list[str]:
    out = []
    for para in re.split(r"\n\s*\n", text.strip()):
        para = " ".join(para.split())
        start = 0
        for m in _SENTENCE_END.finditer(para):
            out.append(para[start:m.end()].strip())
            start = m.end()
        if para[start:].strip():
            out.append(para[start:].strip())
    return [s for s in out if words(s)]


def syllables(word: str) -> int:
    w = word.lower().replace("’", "'")
    if w in _SYLLABLES:
        return _SYLLABLES[w]
    if "-" in w:
        return sum(syllables(p) for p in w.split("-") if p)
    w = re.sub(r"n't$", "nt", w)
    w = re.sub(r"'(s|ll|re|ve|d|m)$", "", w)
    w = re.sub(r"[^a-z]", "", w)
    if len(w) <= 3:
        return 1
    # a silent e before a suffix: care-ful, safe-ly, home-less
    w = re.sub(r"(?<=[^aeiouy])e(?=(ful|less|ly|ment|ness)$)", "", w)
    if w.endswith("es") and not re.search(r"([sxz]|ch|sh|[gc]|[^aeiouy]l)es$", w):
        w = w[:-2]                                   # ride-s, hope-s (but box-es, pag-es, ta-bles)
    elif w.endswith("e") and not re.search(r"([^aeiouy]le|ee|ye)$", w):
        w = w[:-1]                                   # silent final e (but ta-ble, tree)
    elif re.search(r"[^td]ed$", w):
        w = w[:-2]                                   # jump-ed, play-ed (but want-ed)
    w = re.sub(r"^y", "", w)
    return max(1, len(re.findall(r"[aeiouy]{1,2}", w)))


def fk_grade(text: str) -> float:
    ws_, ss = words(text), sentences(text)
    if not ws_ or not ss:
        return 0.0
    syl = sum(syllables(w) for w in ws_)
    return round(0.39 * len(ws_) / len(ss) + 11.8 * syl / len(ws_) - 15.59, 2)


def stats(text: str) -> dict:
    ws_, ss = words(text), sentences(text)
    return {"words": len(ws_), "sentences": len(ss), "fk": fk_grade(text),
            "words_per_sentence": round(len(ws_) / max(1, len(ss)), 1),
            "syllables_per_word": round(sum(syllables(w) for w in ws_) / max(1, len(ws_)), 2)}


if __name__ == "__main__":
    import sys

    src = open(sys.argv[1]).read() if len(sys.argv) > 1 else sys.stdin.read()
    print(stats(src))
