"""Cubs Reading Read Aloud (2A-C): a short original passage to read aloud, then questions to answer.

Passages live in content/passages/english.yaml and are used in file order, each on `passage_reads`
pages in a row (the second reading has different questions). Each question has three choices to circle;
the answer is word for word in the passage. A box for grown-ups records the reading time (about a minute)
and shows the passage's word count. Verify checks the part's `passage_words` and `max_sentence_words`, the
passage's Flesch-Kincaid grade against the section's `fk_grade` (ws/readability.py, as for later levels), that answers come from the passage, and that the featured `words` really appear.
"""

from __future__ import annotations

from ..content import passages, vocab_by_word
from ..models import Issue, Sheet
from ..readability import fk_grade
from ..reading import in_text, mentions, sentences, word_count
from ..registry import GenContext, SheetContent, SheetType, register
from ._common import error, page_rules

QUESTION_WORDS = ("Who", "What", "Where", "When", "Why", "How")


def passage_by_id(pid: str) -> dict:
    for p in passages()["passages"]:
        if p["id"] == pid:
            return p
    raise KeyError(f"no passage {pid!r} in content/passages/")


@register("read_aloud")
class ReadAloud(SheetType):
    template = "read_aloud.html.j2"

    def generate(self, ctx: GenContext) -> SheetContent:
        entry = ctx.plan.for_page(ctx.spec.page)
        plan = entry.extra["passage"]
        p = passage_by_id(plan["id"])
        text = " ".join(p["text"].split())
        items = [{"kind": "passage", "id": p["id"], "title": p["title"], "picture": p["picture"], "text": text,
                  "words": word_count(text), "read": plan["read"], "reads": plan["reads"]}]
        items += [{"kind": "question", "q": q["q"], "answer": q["answer"], "choices": q["choices"]}
                  for q in plan["questions"]]
        title = "Read it aloud" if plan["read"] == 1 else "Read it again"
        return SheetContent(title=title, parent_tip=ctx.tip(self.name), items=items,
                            answer_key=[q["answer"] for q in plan["questions"]],
                            review_words=list(entry.review_words))

    def verify(self, sheet: Sheet) -> list[Issue]:
        rules = page_rules(sheet)
        issues: list[Issue] = []
        (item,) = [i for i in sheet.items if i["kind"] == "passage"]
        questions = [i for i in sheet.items if i["kind"] == "question"]
        try:
            p = passage_by_id(item["id"])
        except KeyError as e:
            return [error(sheet, e.args[0])]
        text = item["text"]
        if text != " ".join(p["text"].split()) or item["title"] != p["title"]:
            issues.append(error(sheet, f"passage {p['id']!r} doesn't match content/passages/"))
        n = word_count(text)
        lo, hi = rules["passage_words"]
        if item["words"] != n:
            issues.append(error(sheet, f"word count printed as {item['words']}, the passage has {n}"))
        if not lo <= n <= hi:
            issues.append(error(sheet, f"passage {p['id']!r} has {n} words; this part wants {lo}–{hi}"))
        if "fk_grade" not in rules:
            issues.append(error(sheet, "no fk_grade rule for this page in the syllabus, so the passage's "
                                       "readability can't be checked"))
        else:
            fk_lo, fk_hi = rules["fk_grade"]
            fk = fk_grade(text)
            if not fk_lo <= fk <= fk_hi:
                issues.append(error(sheet, f"passage {p['id']!r}: Flesch-Kincaid grade {fk} (needs {fk_lo}–{fk_hi})"))
        for s in sentences(text):
            if word_count(s) > rules["max_sentence_words"]:
                issues.append(error(sheet, f"sentence longer than {rules['max_sentence_words']} words: {s!r}"))
        if item["picture"] != p["picture"]:
            issues.append(error(sheet, f"passage {p['id']!r} shows the wrong picture"))
        bank = vocab_by_word()
        for w in p.get("words", []):
            if w not in bank:
                issues.append(error(sheet, f"featured word {w!r} is not in the word bank"))
            elif not mentions(text, w):
                issues.append(error(sheet, f"featured word {w!r} doesn't appear in passage {p['id']!r}"))
        if sorted(sheet.review_words) != sorted(set(p.get("words", []))):
            issues.append(error(sheet, "review words don't match the passage's featured words"))
        if len(questions) != rules["questions_per_sheet"]:
            issues.append(error(sheet, f"expected {rules['questions_per_sheet']} questions, got {len(questions)}"))
        for q in questions:
            if not q["q"].startswith(QUESTION_WORDS) or not q["q"].endswith("?"):
                issues.append(error(sheet, f"not a who/what/where/when/why/how question: {q['q']!r}"))
            if not in_text(q["answer"], text):
                issues.append(error(sheet, f"answer {q['answer']!r} to {q['q']!r} is not in the passage"))
            if len(q["choices"]) != rules.get("choices", 3) or len(set(c.lower() for c in q["choices"])) != len(q["choices"]) \
                    or q["answer"] not in q["choices"]:
                issues.append(error(sheet, f"choices {q['choices']} for {q['q']!r} must be distinct and include the answer"))
        if [q["answer"] for q in questions] != sheet.answer_key:
            issues.append(error(sheet, "answer key doesn't match the questions"))
        asked = [q["q"] for q in questions]
        if len(set(asked)) != len(asked):
            issues.append(error(sheet, "the same question twice"))
        return issues
