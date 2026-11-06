"""Kittens Reading, Rhyme Time: four rows of pictures that rhyme, from the hand-checked rhyme groups in
content/phonics/english.yaml.

`rhyme_task`: `pair` (two rhyming words to say together, the shared ending highlighted when it is spelled
the same), `pick` (a word, then `choices` pictures: circle the one that rhymes) or `odd_one` (three
pictures: two rhyme, circle the one that doesn't). Wrong choices never share the prompt's vowel sound,
so there are no near rhymes (sun / drum).
"""

from __future__ import annotations

from ..content import phonics, vocab_by_word
from ..models import Issue, Sheet
from ..phonics import rhyme_group, shared_ending, usable
from ..registry import GenContext, SheetContent, SheetType, register
from ._common import error

TITLES = {"pair": "Words that rhyme", "pick": "Which one rhymes?", "odd_one": "Which one doesn't rhyme?"}


def _split(word: str, ending: str) -> list[str]:
    return [word[: len(word) - len(ending)], ending] if ending else [word, ""]


@register("rhyme_match")
class RhymeMatch(SheetType):
    template = "rhyme_match.html.j2"

    def generate(self, ctx: GenContext) -> SheetContent:
        entry = ctx.plan.for_page(ctx.spec.page)
        bank = vocab_by_word()
        task = ctx.rules["rhyme_task"]
        items, answers = [], []
        for row in entry.extra["rows"]:
            if task == "pair":
                a, b = row["words"]
                end = shared_ending(a, b)
                items.append({"kind": "rhyme_pair", "words": [a, b], "pictures": [bank[a].picture, bank[b].picture],
                              "parts": [_split(a, end), _split(b, end)]})
                continue
            item = {"kind": "rhyme_" + task, "choices": row["choices"],
                    "pictures": [bank[w].picture for w in row["choices"]], "answer": row["answer"]}
            if "prompt" in row:
                item = {"kind": item["kind"], "prompt": row["prompt"], "picture": bank[row["prompt"]].picture, **item}
            items.append(item)
            answers.append(row["answer"])
        return SheetContent(title=TITLES[task], parent_tip=ctx.tip(self.name), items=items,
                            answer_key=answers or None, review_words=list(entry.review_words))

    def verify(self, sheet: Sheet) -> list[Issue]:
        from ..syllabus import load_level, resolve_page

        rules = resolve_page(load_level(sheet.subject, sheet.level), sheet.page_number).rules
        data, bank = phonics(), vocab_by_word()
        task = rules["rhyme_task"]
        issues = []
        if len(sheet.items) != rules["rows_per_sheet"]:
            issues.append(error(sheet, f"expected {rules['rows_per_sheet']} rows, got {len(sheet.items)}"))

        def group(w):
            g = rhyme_group(data, w)
            if g is None:
                issues.append(error(sheet, f"{w!r} is not in a hand-checked rhyme group"))
            return g

        page_words = []
        for item in sheet.items:
            if item["kind"] != f"rhyme_{task}":
                issues.append(error(sheet, f"row kind {item['kind']!r}, the part says {task!r}"))
                continue
            words = ([item["prompt"]] if "prompt" in item else []) + item.get("choices", item.get("words", []))
            page_words += words
            for w in words:
                e = bank.get(w)
                if e is not None and not usable(e):
                    issues.append(error(sheet, f"{w!r} has no picture of its own (or is a color word)"))
            shown = item["pictures"] + ([item["picture"]] if "picture" in item else [])
            if sorted(shown) != sorted(bank[w].picture for w in words if w in bank):
                issues.append(error(sheet, f"pictures {shown} don't match the words {words}"))
            if task == "pair":
                a, b = item["words"]
                if group(a) is None or group(a) is not group(b):
                    issues.append(error(sheet, f"{a!r} and {b!r} don't rhyme"))
                end = shared_ending(a, b)
                if item["parts"] != [_split(a, end), _split(b, end)]:
                    issues.append(error(sheet, f"{a!r}/{b!r}: highlighted ending should be {end!r}"))
                continue
            choices, answer = item["choices"], item["answer"]
            if answer not in choices:
                issues.append(error(sheet, f"answer {answer!r} is not one of {choices}"))
                continue
            if task == "pick":
                if len(choices) != rules["choices"]:
                    issues.append(error(sheet, f"expected {rules['choices']} choices, got {choices}"))
                g = group(item["prompt"])
                if g is None or group(answer) is not g:
                    issues.append(error(sheet, f"{answer!r} doesn't rhyme with {item['prompt']!r}"))
                for w in choices:
                    o = group(w)
                    if w != answer and g is not None and o is not None and o["vowel"] == g["vowel"]:
                        issues.append(error(sheet, f"wrong choice {w!r} sounds too close to {item['prompt']!r}"))
            else:
                rest = [w for w in choices if w != answer]
                if len(choices) != 3 or len(rest) != 2 or group(rest[0]) is None or group(rest[0]) is not group(rest[1]):
                    issues.append(error(sheet, f"odd one out needs two rhyming pictures and one more: {choices}"))
                else:
                    o = group(answer)
                    if o is not None and o["vowel"] == group(rest[0])["vowel"]:
                        issues.append(error(sheet, f"odd one {answer!r} sounds too close to {rest}"))
        if len(set(page_words)) != len(page_words):
            issues.append(error(sheet, f"the same word twice on one page: {page_words}"))
        if task != "pair":
            answers = [i["answer"] for i in sheet.items]
            if sheet.answer_key != answers:
                issues.append(error(sheet, f"answer key {sheet.answer_key} doesn't match the rows {answers}"))
            positions = [i["choices"].index(i["answer"]) for i in sheet.items if i["answer"] in i["choices"]]
            if len(positions) > 1 and len(set(positions)) == 1:
                issues.append(error(sheet, "the answer is in the same place on every row"))
        return issues
