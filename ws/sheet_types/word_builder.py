"""Foxes Reading (R3-B): build words from a known word and a word part, then use them.

One page, three activities on the same 4 words (planned level-wide, `ws.passages.plan_passages`):
1. Build it: "un + kind = ____" (compound words: two pictures, "star + fish = ____").
2. Circle the meaning (2 of the words): the right meaning, the meaning with the other word part
   ("careless" vs "full of care"; "unkind" vs "kind again") and another word's meaning.
3. Circle the word that fits (the other 2): a sentence with a blank and two choices, the built word
   and its hand-checked foil (unhappy / happy, careful / careless).
Content: content/wordparts/<level>.yaml. Answer key: the built words, letters and chosen words.
"""

from __future__ import annotations

from ..models import Issue, Sheet
from ..passages import BLANK, LETTERS, affixes, affixes_kind, first_and_second, word_parts, wordpart_problems
from ..registry import GenContext, SheetContent, SheetType, register
from ._common import error

OTHER_PATTERN = {"un": "{base} again", "re": "not {base}"}   # the other prefix's meaning, as a wrong choice
PARTNER = {"ful": "less", "less": "ful"}


def wrong_meanings(w, pool, rng) -> list[str]:
    """Two wrong meanings: the other word part's meaning (when there is one), then another word's."""
    by_built = {p.built: p for p in pool}
    wrong = []
    if w.affix in OTHER_PATTERN:
        wrong.append(OTHER_PATTERN[w.affix].format(base=w.base))
    elif w.affix in PARTNER and w.base + PARTNER[w.affix] in by_built:
        wrong.append(by_built[w.base + PARTNER[w.affix]].meaning)
    others = sorted({p.meaning for p in pool if p.affix == w.affix and p.built != w.built
                     and (w.base is None or p.base != w.base) and p.meaning not in wrong})
    while len(wrong) < 2:
        pick = rng.choice(others)
        others.remove(pick)
        wrong.append(pick)
    return wrong


@register("word_builder")
class WordBuilder(SheetType):
    template = "word_builder.html.j2"

    def generate(self, ctx: GenContext) -> SheetContent:
        rng, level = ctx.rng, ctx.spec.level
        pool = word_parts(level)
        by_built = {w.built: w for w in pool}
        words = [by_built[b] for b in ctx.plan.for_page(ctx.spec.page).extra["builds"]]
        rng.shuffle(words)
        n_mean = ctx.rules.get("meanings", 2)
        picked = rng.sample(range(len(words)), len(words))
        for_meaning = [words[i] for i in sorted(picked[:n_mean])]
        for_sentence = [words[i] for i in sorted(picked[n_mean:])]
        info = affixes(level)
        shown = list(dict.fromkeys(w.affix for w in words))
        items: list[dict] = [{"kind": "rule", "parts": [{"show": info[a]["show"], "means": info[a]["means"]}
                                                         for a in shown]}]
        key: list[str] = []
        n = 0
        for w in words:
            n += 1
            first, second = first_and_second(w)
            item = {"kind": "build", "n": n, "first": first, "second": second, "built": w.built}
            kind = affixes_kind(w)
            if kind != "compound":
                item["part"] = "first" if kind == "prefix" else "second"   # the word part, in the subject color
            if w.pictures:
                item["pictures"] = list(w.pictures)
            items.append(item)
            key.append(f"{n}. {w.built}")
        for w in for_meaning:
            n += 1
            choices = [w.meaning, *wrong_meanings(w, pool, rng)]
            rng.shuffle(choices)
            right = LETTERS[choices.index(w.meaning)]
            items.append({"kind": "meaning", "n": n, "built": w.built, "choices": choices, "answer": right})
            key.append(f"{n}. {right} ({w.meaning})")
        for w in for_sentence:
            n += 1
            before, after = w.sentence.split(BLANK)
            options = [w.built, w.foil]
            rng.shuffle(options)
            items.append({"kind": "sentence", "n": n, "before": before, "after": after, "options": options,
                          "answer": w.built})
            key.append(f"{n}. {w.built}")
        title = info[shown[0]]["title"] if len(shown) == 1 else "Build new words"
        return SheetContent(title=title, parent_tip=ctx.tip(self.name), items=items, answer_key=key)

    def verify(self, sheet: Sheet) -> list[Issue]:
        from ..syllabus import load_level, resolve_page

        rules = resolve_page(load_level(sheet.subject, sheet.level), sheet.page_number).rules
        pool = word_parts(sheet.level)
        by_built = {w.built: w for w in pool}
        issues: list[Issue] = []
        builds = [i for i in sheet.items if i["kind"] == "build"]
        if len(builds) != rules.get("builds", 4):
            issues.append(error(sheet, f"{len(builds)} words to build; expected {rules.get('builds', 4)}"))
        built = [i["built"] for i in builds]
        if len(set(built)) != len(built):
            issues.append(error(sheet, f"the same word twice: {built}"))
        key = []
        for i in sheet.items:
            if i["kind"] == "rule":
                continue
            w = by_built.get(i.get("built") or i.get("answer"))
            if w is None:
                issues.append(error(sheet, f"{i} is not in the word-builder list"))
                continue
            issues += [error(sheet, m) for m in wordpart_problems(w, set(by_built))]
            if w.affix not in rules["affixes"]:
                issues.append(error(sheet, f"{w.built}: {w.affix} words don't belong on this page"))
            if i["kind"] == "build":
                if (i["first"], i["second"]) != first_and_second(w) or i.get("pictures", []) != w.pictures:
                    issues.append(error(sheet, f"{w.built}: the pieces don't match the list"))
                key.append(f"{i['n']}. {w.built}")
            elif i["kind"] == "meaning":
                if len(set(i["choices"])) != 3 or i["choices"][LETTERS.index(i["answer"])] != w.meaning:
                    issues.append(error(sheet, f"{w.built}: meaning choices are wrong"))
                key.append(f"{i['n']}. {i['answer']} ({w.meaning})")
            elif i["kind"] == "sentence":
                if sorted(i["options"]) != sorted([w.built, w.foil]) or \
                        i["before"] + BLANK + i["after"] != w.sentence:
                    issues.append(error(sheet, f"{w.built}: sentence or choices don't match the list"))
                key.append(f"{i['n']}. {w.built}")
            if w.built not in built:
                issues.append(error(sheet, f"{w.built} is used but wasn't built on this page"))
        if [i["n"] for i in sheet.items if "n" in i] != list(range(1, len(key) + 1)):
            issues.append(error(sheet, "items are not numbered 1, 2, 3, ..."))
        if sheet.answer_key != key:
            issues.append(error(sheet, "answer key doesn't match the items"))
        kinds = {affixes_kind(by_built[b]) for b in built if b in by_built}
        if "compound" in kinds and len(kinds) > 1:
            issues.append(error(sheet, "compound words and word parts on one page"))
        return issues
