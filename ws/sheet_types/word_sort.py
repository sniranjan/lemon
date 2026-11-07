"""Cubs Reading Kinds of Words (2A-B): naming words, doing words and describing words.

Layouts (rule `word_kinds`, see syllabus/english/2A.yaml):
- `pick`: `rows` rows of three words; the child circles the one `target` word in each row.
- `sort`: `sort_words` words (the same number of each kind); the child checks its kind in a table.
- `fill`: `fill_sentences` sentences with a blank and two choices; only one is the right kind of word
  (`target`, or `mixed`). Sentences are hand-written in content/grammar/english.yaml.
Parent tips are per layout (`word_sort_pick`, `word_sort_sort`, `word_sort_fill` in content/tips/).
A page that brings a new word shows it first on a word card (picture, word, its sentence from the word bank).
Every word's kind comes from the hand-checked `kinds` lists. `answer_key` follows the page top to bottom (sort: one line per kind).
"""

from __future__ import annotations

from ..content import grammar, vocab_by_word
from ..models import Issue, Sheet
from ..reading import KINDS, distractor_kinds, kind_of
from ..registry import GenContext, SheetContent, SheetType, register
from ._common import error, page_rules

TITLES = {"naming": "Naming words", "doing": "Doing words", "describing": "Describing words"}


def _new_card(word: str) -> dict:
    e = vocab_by_word()[word]
    card = {"kind": "new_word", "word": word, "sentence": e.sentences[0]}
    if e.picture:
        card["picture"] = e.picture
    return card


@register("word_sort")
class WordSort(SheetType):
    template = "word_sort.html.j2"

    def generate(self, ctx: GenContext) -> SheetContent:
        entry = ctx.plan.for_page(ctx.spec.page)
        g = grammar()
        layout = ctx.rules["word_kinds"]
        labels = g["labels"]
        items: list[dict] = [_new_card(w) for w in entry.new_words]
        if layout == "pick":
            target = entry.extra["target"]
            title = TITLES[target]
            items += [{"kind": "pick", "words": r["words"], "answer": r["answer"], "want": target,
                       "ask": f"Circle the {labels[target]}."} for r in entry.extra["rows"]]
            answers = [r["answer"] for r in entry.extra["rows"]]
        elif layout == "sort":
            title = "Sort the words"
            items += [{"kind": "sort", "word": s["word"], "answer": s["kind"]} for s in entry.extra["sort"]]
            # one short line per kind ("naming: lizard & pebble"), so the answers page stays one line a page
            answers = [f"{k}: " + " & ".join(s["word"] for s in entry.extra["sort"] if s["kind"] == k) for k in KINDS]
        else:
            target = ctx.rules["target"]
            title = "Fill in the blank"
            items += [{"kind": "fill", "text": f["text"], "answer": f["answer"], "want": f["kind"],
                       "choices": f["choices"]} for f in entry.extra["fill"]]
            answers = [f["answer"] for f in entry.extra["fill"]]
        return SheetContent(title=title, parent_tip=ctx.tip(f"{self.name}_{layout}"), items=items, answer_key=answers,
                            new_words=list(entry.new_words), review_words=list(entry.review_words))

    def verify(self, sheet: Sheet) -> list[Issue]:
        rules = page_rules(sheet)
        g = grammar()
        bank = vocab_by_word()
        issues: list[Issue] = []
        lists = [set(g["kinds"][k]) for k in KINDS]
        if lists[0] & lists[1] or lists[0] & lists[2] or lists[1] & lists[2]:
            issues.append(error(sheet, "a word is listed under two kinds in content/grammar/english.yaml"))
        cards = [i for i in sheet.items if i["kind"] == "new_word"]
        if [c["word"] for c in cards] != sheet.new_words:
            issues.append(error(sheet, "every new word needs its word card, in order"))
        if rules["word_kinds"] == "sort":
            want = [f"{k}: " + " & ".join(i["word"] for i in sheet.items if i["kind"] == "sort" and i["answer"] == k)
                    for k in KINDS]
            if sheet.answer_key != want:
                issues.append(error(sheet, f"answer key {sheet.answer_key} doesn't match the words' kinds"))
        elif sheet.answer_key != [i["answer"] for i in sheet.items if i["kind"] in ("pick", "fill")]:
            issues.append(error(sheet, "answer key doesn't match the page's answers"))
        for c in cards:
            e = bank.get(c["word"])
            if e and (c.get("picture") != e.picture or c["sentence"] not in e.sentences):
                issues.append(error(sheet, f"word card for {c['word']!r} doesn't match the word bank"))
        layout = rules["word_kinds"]
        work = [i for i in sheet.items if i["kind"] != "new_word"]
        shown: list[str] = []
        if layout == "pick":
            if len(work) != rules["rows"]:
                issues.append(error(sheet, f"expected {rules['rows']} rows, got {len(work)}"))
            for row in work:
                shown += row["words"]
                hits = [w for w in row["words"] if kind_of(w, g) == rules["target"]]
                if hits != [row["answer"]] or len(row["words"]) != 3:
                    issues.append(error(sheet, f"row {row['words']} must have exactly one {rules['target']} "
                                               f"word, the answer {row['answer']!r}"))
                if any(kind_of(w, g) is None for w in row["words"]):
                    issues.append(error(sheet, f"row {row['words']} has a word with no checked kind"))
        elif layout == "sort":
            shown = [i["word"] for i in work]
            if len(work) != rules["sort_words"]:
                issues.append(error(sheet, f"expected {rules['sort_words']} words, got {len(work)}"))
            for i in work:
                if kind_of(i["word"], g) != i["answer"]:
                    issues.append(error(sheet, f"{i['word']!r} is a {kind_of(i['word'], g)} word, not {i['answer']}"))
            per = [sum(1 for i in work if i["answer"] == k) for k in KINDS]
            if len(set(per)) != 1:
                issues.append(error(sheet, f"sort words should be even across the kinds, got {per}"))
        else:
            if len(work) != rules["fill_sentences"]:
                issues.append(error(sheet, f"expected {rules['fill_sentences']} sentences, got {len(work)}"))
            sentences = {s["text"]: s["answer"] for k in KINDS for s in g["fill"][k]}
            for i in work:
                shown += i["choices"]
                if sentences.get(i["text"]) != i["answer"]:
                    issues.append(error(sheet, f"{i['text']!r} isn't a checked fill-in sentence for {i['answer']!r}"))
                if i["text"].count("___") != 1:
                    issues.append(error(sheet, f"{i['text']!r} must have one blank"))
                if rules["target"] != "mixed" and i["want"] != rules["target"]:
                    issues.append(error(sheet, f"{i['text']!r} asks for a {i['want']} word in a {rules['target']} part"))
                kinds = [kind_of(w, g) for w in i["choices"]]
                wrong = [w for w in i["choices"] if w != i["answer"]]
                if any(kind_of(w, g) not in distractor_kinds(i["want"]) for w in wrong):
                    issues.append(error(sheet, f"wrong choice {wrong} for {i['text']!r} could fit the blank; "
                                               f"use a {' or '.join(distractor_kinds(i['want']))} word"))
                if len(i["choices"]) != 2 or i["answer"] not in i["choices"] or kinds.count(i["want"]) != 1 \
                        or kind_of(i["answer"], g) != i["want"]:
                    issues.append(error(sheet, f"choices {i['choices']} for {i['text']!r} need exactly one "
                                               f"{i['want']} word: the answer"))
        if len(set(shown)) != len(shown):
            issues.append(error(sheet, f"a word appears twice on the page: {shown}"))
        missing = [w for w in sheet.new_words if w not in shown]
        if missing:
            issues.append(error(sheet, f"new word(s) {missing} aren't used in the exercise"))
        expected = sorted(set(shown) - set(sheet.new_words))
        if sorted(sheet.review_words) != expected:
            issues.append(error(sheet, "review words don't match the words on the page"))
        return issues
