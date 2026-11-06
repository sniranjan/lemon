"""Kittens Reading, Letter Teams: four picture words, each with its letter team highlighted
(sh in fish, bl in blocks, -at in cat). The child reads the word, then traces the team in gray
letters (`team_task: trace`) or writes it into empty boxes (`team_task: fill`).

Rows come from the level plan (`ws.phonics.plan_phonics`). The team must really be in the word, at
its place, and the word must be on the team's hand-checked list in content/phonics/english.yaml.
"""

from __future__ import annotations

from ..content import phonics, vocab_by_word
from ..models import Issue, Sheet
from ..phonics import split_team, team_spec, usable
from ..registry import GenContext, SheetContent, SheetType, register
from ._common import error


@register("letter_team")
class LetterTeam(SheetType):
    template = "letter_team.html.j2"

    def generate(self, ctx: GenContext) -> SheetContent:
        entry = ctx.plan.for_page(ctx.spec.page)
        data, bank = phonics(), vocab_by_word()
        task = ctx.rules.get("team_task", "trace")
        items = []
        for row in entry.extra["rows"]:
            spec = team_spec(data, row["team"])
            items.append({"kind": "team_word", "word": row["word"], "picture": bank[row["word"]].picture,
                          "team": row["team"], "letters": spec["letters"],
                          "parts": split_team(row["word"], spec["letters"], spec["where"]), "task": task})
        teams = list(dict.fromkeys(i["letters"] for i in items))
        title = "Letter team: " + teams[0] if len(teams) == 1 else "Letter teams"
        return SheetContent(title=title, parent_tip=ctx.tip(self.name), items=items,
                            new_words=list(entry.new_words), review_words=list(entry.review_words))

    def verify(self, sheet: Sheet) -> list[Issue]:
        from ..syllabus import load_level, resolve_page

        rules = resolve_page(load_level(sheet.subject, sheet.level), sheet.page_number).rules
        data, bank = phonics(), vocab_by_word()
        issues = []
        if len(sheet.items) != rules["rows_per_sheet"]:
            issues.append(error(sheet, f"expected {rules['rows_per_sheet']} words, got {len(sheet.items)}"))
        words = [i["word"] for i in sheet.items]
        if len(set(words)) != len(words):
            issues.append(error(sheet, f"the same word twice on one page: {words}"))
        for item in sheet.items:
            w, team = item["word"], item["team"]
            if team not in rules["teams"]:
                issues.append(error(sheet, f"team {team!r} is not one of this part's teams {rules['teams']}"))
                continue
            spec = team_spec(data, team)
            if w not in spec["words"]:
                issues.append(error(sheet, f"{w!r} is not on the hand-checked list for {team!r}"))
            if item["letters"] != spec["letters"] or item["parts"] != split_team(w, spec["letters"], spec["where"]):
                issues.append(error(sheet, f"{w!r}: the team {spec['letters']!r} isn't at its place ({spec['where']})"))
            elif "".join(item["parts"]) != w:
                issues.append(error(sheet, f"{w!r}: parts {item['parts']} don't spell the word"))
            entry = bank.get(w)
            if entry is not None and (not usable(entry) or item["picture"] != entry.picture):
                issues.append(error(sheet, f"{w!r}: needs its own picture (and no color-word crayon)"))
            if item["task"] != rules.get("team_task", "trace"):
                issues.append(error(sheet, f"{w!r}: task {item['task']!r}, the part says {rules.get('team_task')!r}"))
        missing = [w for w in sheet.new_words if w not in words]
        if missing:
            issues.append(error(sheet, f"new word(s) {missing} are not on the page"))
        return issues
