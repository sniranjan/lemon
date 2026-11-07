"""Cubs Reading Picture Puzzles (2A-A): spell a pictured word by filling in letters, then little crosswords.

Rules (see syllabus/english/2A.yaml): `puzzle: missing` shows `puzzle_items` pictures, each with its word
in letter boxes and `blanks` empty boxes (a number, or `all_but_first`; `blank_letters: vowels` empties a
vowel). `puzzle: crossword` shows `puzzle_items` crosswords of two words that share a letter, with a
picture clue for each (an arrow says across or down); `given` says which squares are filled in
(`first` letters, the `shared` square). Words come from the level plan (`ws.reading`), so they spread
evenly over the section. `answer_key` lists the words top to bottom.
"""

from __future__ import annotations

from ..content import grammar, vocab_by_word
from ..models import Issue, Sheet
from ..reading import VOWELS, crossword_grid
from ..registry import GenContext, SheetContent, SheetType, register
from ._common import error, page_rules


@register("word_puzzle")
class WordPuzzle(SheetType):
    template = "word_puzzle.html.j2"

    def generate(self, ctx: GenContext) -> SheetContent:
        entry = ctx.plan.for_page(ctx.spec.page)
        bank = vocab_by_word()
        items = []
        if ctx.rules["puzzle"] == "missing":
            for p in entry.extra["puzzles"]:
                w = p["words"][0]
                items.append({"kind": "missing", "word": w, "picture": bank[w].picture,
                              "letters": [[ch, i not in p["blanks"]] for i, ch in enumerate(w)]})
            title = "Fill in the letters"
        else:
            for p in entry.extra["puzzles"]:
                across, down = p["words"]
                items.append({"kind": "crossword", "words": [across, down],
                              "pictures": [bank[across].picture, bank[down].picture],
                              "across_row": p["across_row"], "down_col": p["down_col"],
                              "grid": crossword_grid(across, down, p["across_row"], p["down_col"],
                                                     ctx.rules["given"])})
            title = "Picture crosswords"
        answers = [w for i in items for w in ([i["word"]] if i["kind"] == "missing" else i["words"])]
        return SheetContent(title=title, parent_tip=ctx.tip(self.name), items=items, answer_key=answers,
                            review_words=list(entry.review_words))

    def verify(self, sheet: Sheet) -> list[Issue]:
        rules = page_rules(sheet)
        allowed = set(grammar()["puzzle_words"])
        lo, hi = rules["word_length"]
        bank = vocab_by_word()
        issues: list[Issue] = []
        if len(sheet.items) != rules["puzzle_items"]:
            issues.append(error(sheet, f"expected {rules['puzzle_items']} puzzles, got {len(sheet.items)}"))
        words: list[str] = []
        for item in sheet.items:
            ws = [item["word"]] if item["kind"] == "missing" else item["words"]
            words += ws
            for w in ws:
                if w not in allowed:
                    issues.append(error(sheet, f"{w!r} is not in the hand-checked puzzle_words"))
                if not lo <= len(w) <= hi:
                    issues.append(error(sheet, f"{w!r} is not {lo}–{hi} letters long"))
            if item["kind"] == "missing":
                issues += self._check_missing(sheet, item, rules, bank)
            else:
                issues += self._check_crossword(sheet, item, rules, bank)
        if len(set(words)) != len(words):
            issues.append(error(sheet, f"a word appears twice on the page: {words}"))
        if sheet.answer_key != words:
            issues.append(error(sheet, f"answer key {sheet.answer_key} doesn't list the words {words}"))
        return issues

    @staticmethod
    def _check_missing(sheet: Sheet, item: dict, rules: dict, bank) -> list[Issue]:
        w = item["word"]
        out = []
        if "".join(ch for ch, _ in item["letters"]) != w:
            out.append(error(sheet, f"letter boxes don't spell {w!r}"))
        if item["picture"] != bank[w].picture:
            out.append(error(sheet, f"{w!r} shows the wrong picture"))
        blanks = [i for i, (_, shown) in enumerate(item["letters"]) if not shown]
        want = len(w) - 1 if rules["blanks"] == "all_but_first" else rules["blanks"]
        if len(blanks) != want:
            out.append(error(sheet, f"{w!r} has {len(blanks)} empty boxes, the part wants {want}"))
        if rules["blanks"] == "all_but_first" and blanks != list(range(1, len(w))):
            out.append(error(sheet, f"{w!r} should show only its first letter"))
        if rules.get("blank_letters") == "vowels" and any(w[i] not in VOWELS for i in blanks):
            out.append(error(sheet, f"{w!r}: only vowels may be empty in this part"))
        if rules.get("blank_letters") == "vowels" and w.endswith("e") and len(w) - 1 in blanks:
            out.append(error(sheet, f"{w!r}: a silent final e is never the missing sound"))
        if rules.get("blank_letters") == "any" and 0 in blanks:
            out.append(error(sheet, f"{w!r}: the first letter is always shown in this part"))
        return out

    @staticmethod
    def _check_crossword(sheet: Sheet, item: dict, rules: dict, bank) -> list[Issue]:
        across, down = item["words"]
        r, c = item["across_row"], item["down_col"]
        out = []
        if across == down or across[c] != down[r]:
            out.append(error(sheet, f"{across!r} and {down!r} don't cross at a shared letter"))
            return out
        if item["grid"] != crossword_grid(across, down, r, c, rules["given"]):
            out.append(error(sheet, f"crossword grid for {across!r}/{down!r} doesn't match its words"))
        if item["pictures"] != [bank[across].picture, bank[down].picture]:
            out.append(error(sheet, f"crossword {across!r}/{down!r} shows the wrong pictures"))
        empty = sum(1 for row in item["grid"] for cell in row if cell and not cell["given"])
        if empty < 2:
            out.append(error(sheet, f"crossword {across!r}/{down!r} leaves almost nothing to write"))
        return out
