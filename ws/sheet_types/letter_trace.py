"""EN 5A-A/C: dotted lowercase letters to trace, with two picture words that start with the letter.

Two layouts, both from the level plan (`ws.plan.plan_letters`):
- `letter`: one letter. Step 1: the letter (capital and small, solid), two big dotted copies and a
  practice row; step 2: three practice rows. Then two picture words with the letter in bold.
- `rows`: three letters, one row each: (capital and) small letter, a dotted row, a picture word.
Dotted letters come from the trace font (`ws.trace_font`); solid ones are Andika text.
"""

from __future__ import annotations

from ..content import vocab_by_word
from ..models import Issue, Sheet
from ..registry import GenContext, SheetContent, SheetType, register
from ..trace_font import andika_has, missing_glyphs
from ._common import error


def marked(word: str, letter: str) -> list[list]:
    """The word in runs, with each copy of the letter marked (the template makes it bold)."""
    runs: list[list] = []
    for ch in word:
        hit = ch == letter
        if runs and runs[-1][1] == hit:
            runs[-1][0] += ch
        else:
            runs.append([ch, hit])
    return runs


def word_item(word: str, letter: str, kind: str = "word") -> dict:
    return {"kind": kind, "letter": letter, "word": word, "picture": vocab_by_word()[word].picture,
            "runs": marked(word, letter)}


@register("letter_trace")
class LetterTrace(SheetType):
    template = "letter_trace.html.j2"

    def generate(self, ctx: GenContext) -> SheetContent:
        entry = ctx.plan.for_page(ctx.spec.page)
        x = entry.extra
        if x["layout"] == "letter":
            items = [{"kind": "letter", "letter": x["letter"], "upper": x["letter"].upper(), "step": x["step"]}]
            items += [word_item(w, x["letter"]) for w in x["words"]]
            title, tip = "Trace the letter", self.name
        else:
            items = [{**word_item(r["word"], r["letter"], "row"), "upper": r["letter"].upper() if x["upper"] else None}
                     for r in x["rows"]]
            title, tip = ("Big and small letters", "letter_trace_pairs") if x["upper"] else \
                ("Trace and say", "letter_trace_review")
        return SheetContent(title=title, parent_tip=ctx.tip(tip), items=items,
                            new_words=list(entry.new_words), review_words=list(entry.review_words))

    def verify(self, sheet: Sheet) -> list[Issue]:
        issues = []
        letters = [i for i in sheet.items if i["kind"] == "letter"]
        words = [i for i in sheet.items if i["kind"] == "word"]
        rows = [i for i in sheet.items if i["kind"] == "row"]
        if letters:
            if len(letters) != 1 or len(words) != 2 or rows:
                issues.append(error(sheet, f"a letter page has 1 letter and 2 words, got "
                                           f"{len(letters)} and {len(words)}"))
        elif not 1 <= len(rows) <= 3 or words:
            issues.append(error(sheet, f"a review page has 1–3 letter rows, got {len(rows)}"))
        for item in sheet.items:
            letter = item["letter"]
            # §8: every traced letter exists in the trace font; solid letters exist in Andika
            if missing_glyphs(letter):
                issues.append(error(sheet, f"the trace font has no {letter!r}"))
            solid = letter + (item.get("upper") or "") + item.get("word", "")
            if not andika_has(solid):
                issues.append(error(sheet, f"Andika can't print {solid!r}"))
            if "word" in item:
                if letter not in item["word"]:
                    issues.append(error(sheet, f"{item['word']!r} has no letter {letter!r}"))
                if "".join(t for t, _ in item["runs"]) != item["word"]:
                    issues.append(error(sheet, f"runs don't spell {item['word']!r}"))
            if item.get("upper") and item["upper"] != letter.upper():
                issues.append(error(sheet, f"capital {item['upper']!r} doesn't match {letter!r}"))
        shown = [i["word"] for i in sheet.items if "word" in i]
        if len(set(shown)) != len(shown):
            issues.append(error(sheet, f"the same word twice on one page: {shown}"))
        return issues
