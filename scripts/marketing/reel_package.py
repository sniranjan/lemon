"""Copy rendered challenge reels into marketing/instagram/reels with a caption each.

    apps/reels/render-all.sh                      # render first (out/Level-*.mp4, out/Topic-*.mp4)
    uv run python scripts/marketing/reel_package.py

Level reels → reels/level-NN-<slug>/, topic reels → reels/topics/NN-<slug>/<topic>/, "know by June" reels →
reels/facts/grade-<g>/ (reel.mp4 + caption.md). Topics are read from apps/reels/src/topics/*.ts (level, topic,
seconds per block); facts from apps/reels/src/facts.ts (grade, level, each item's tag and Common Core code).
"""

from __future__ import annotations

import json
import re
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
APP = ROOT / "apps" / "reels"
OUT = ROOT / "marketing" / "instagram" / "reels"
LEVELS = json.loads((APP / "public" / "levels.json").read_text())
INDEX = {lv["slug"]: i for i, lv in enumerate(LEVELS, 1)}
EMOJI = {"chicks": "🐥", "ducklings": "🦆", "bunnies": "🐰", "kittens": "🐱", "puppies": "🐶", "cubs": "🐻", "foxes": "🦊",
         "owls": "🦉", "otters": "🦦", "pandas": "🐼", "penguins": "🐧", "lions": "🦁", "whales": "🐳"}
TAGS = "#homeschool #kidsquiz #momlife #learningathome #printableworksheets #paperlessons"


AUDIO = (APP / "src" / "audio.tsx").read_text()
TITLES = dict(re.findall(r'"?([a-z-]+)"?: \{ title: "([^"]+)"', AUDIO))
QUIZ_TRACK = re.search(r'DEFAULT_TRACK: Track = "([a-z-]+)"', AUDIO)[1]
HANDS_TRACK = re.search(r'<Music track="([a-z-]+)"', (APP / "src" / "Milestones.tsx").read_text())[1]


def credit(track: str) -> str:
    return (f'Music: "{TITLES[track]}" Kevin MacLeod (incompetech.com), licensed under Creative Commons: '
            f"By Attribution 4.0 (creativecommons.org/licenses/by/4.0/)")


def slugify(s: str) -> str:
    return re.sub(r"^-|-$", "", re.sub(r"[^a-z0-9]+", "-", s.lower()))


def caption(lv: dict, topic: str | None, seconds: int) -> str:
    age, name, grade = lv["age"], lv["name"], lv["grade"]
    what = f"{topic}, from the {name} level ({grade} work)" if topic else f"the {name} level ({grade} work)"
    i = INDEX[lv["slug"]]
    hl = f'Add to story, then add it to the "{name}" highlight (cover: stories/highlights/levels/{i:02d}-{lv["slug"]}.png).'
    if age <= 4:
        body = (f"Play along with your {age}-year-old! {EMOJI[lv['slug']]}\n\n5 little questions: {what}. Point, say it "
                f"together, and cheer every try. The last one is a bonus stretch ⭐\n\nHow did they do? 👇")
    else:
        body = (f"Can your {age}-year-old do these? {EMOJI[lv['slug']]}\n\n5 quick questions: {what}. {seconds} seconds "
                f"each. Pause, ask them, and see how far they get.\n\nComment their score: x/5 👇")
    return (f"# {name}{' · ' + topic if topic else ''} (age {age})\n\nMusic and sound are in the video. After posting: {hl}\n\n"
            f"## Caption\n\n{body}\n\n📩 Comment {name.upper()} and we'll DM you free {name} pages.\n\n#{age}yearold {TAGS}\n\n{credit(QUIZ_TRACK)}\n")


def grade_words(g: str) -> tuple[str, str]:
    if g == "k":
        return "kindergarten", "#kindergarten"
    n = int(g)
    suffix = {1: "st", 2: "nd", 3: "rd"}.get(n, "th")
    return f"{n}{suffix} grade", f"#{n}{suffix}grade"


def facts_caption(g: str, who: str, lv: dict, items: list[tuple[str, str]]) -> str:
    grade, tag = grade_words(g)
    lines = "\n".join(f"{k}. {t} ({code})" for k, (t, code) in enumerate(items, 1))
    body = (f"What should a {who} know by June? 👀\n\n{len(items)} things the Common Core standards (used in most US states) "
            f"expect by the end of {grade}, with one to try for each:\n\n{lines}\n\nOur {lv['name']} level is {grade} work "
            f"at age {lv['age']}. Every kid learns at their own pace: start at their level, not their grade.\n\n"
            f"How many did yours get? Comment x/{len(items)} 👇")
    return (f"# Know by June · {grade} ({lv['name']} level)\n\nMusic and sound are in the video.\n\n## Caption\n\n{body}\n\n"
            f"📩 Comment {lv['name'].upper()} and we'll DM you free {lv['name']} pages.\n\n{tag} #commoncore {TAGS}\n\n{credit(QUIZ_TRACK)}\n")


def hands_caption(age: int) -> str:
    body = (f"Hand skills at age {age} 🖍️\n\nWhat most kids (75% or more) can do by age {age}, from the CDC's milestone "
            f"checklist, plus a few of the CDC's easy ways to help at home.\n\nEvery kid grows at their own pace. You know your "
            f"child best: if you have a concern, talk with your child's doctor and ask about developmental screening.\n\n"
            f"Full CDC checklist: cdc.gov/ActEarly")
    return (f"# Little hands · age {age}\n\nMusic is in the video. Source: "
            f"https://www.cdc.gov/act-early/milestones/{age}-years.html\n\n## Caption\n\n{body}\n\n"
            f"#{age}yearold #finemotorskills #preschool #momlife #learningathome #paperlessons\n\n{credit(HANDS_TRACK)}\n")


CTA_LEVEL = {4: "Owls", 8: "Lions"}  # our level teaching that grade's work


def report_caption(grade: int, year: int, naep_id: str, pct: int) -> str:
    cta = (f"📩 Comment {CTA_LEVEL[grade].upper()} and we'll DM you free {CTA_LEVEL[grade]} pages ({grade}th grade work)."
           if grade in CTA_LEVEL else "Free printable pages for ages 3–12: link in bio.")
    body = (f"Only {pct}% of {grade}th graders got this right 😮\n\nA real question from the Nation's Report Card "
            f"(NAEP, {year}), the test given to students across the US. Can you? Can your kid? Pause, pick an answer, "
            f"and comment your letter 👇\n\n{cta}")
    source = (f"Source: U.S. Department of Education, Institute of Education Sciences, National Center for Education "
              f"Statistics, National Assessment of Educational Progress (NAEP), {year} Mathematics Assessment. "
              f"Question {naep_id}, national results.")
    return (f"# Report Card · grade {grade} ({naep_id})\n\nMusic and sound are in the video.\n\n## Caption\n\n{body}\n\n"
            f"#{grade}thgrade #mathchallenge #canyousolveit #momlife #homeschool #paperlessons\n\n{source}\n\n"
            f"{credit('thinking-music')}\n")


HOLIDAY_BAND = {"thanksgiving-little": ("ages 3–5", "#preschool #toddlerlearning"),
                "thanksgiving-kids": ("ages 6–8", "#2ndgrade #3rdgrade"),
                "thanksgiving-big-kids": ("ages 9–12 vs grown-ups", "#5thgrade #6thgrade #mathchallenge")}


def holiday_caption(hid: str) -> str:
    band, tags = HOLIDAY_BAND[hid]
    body = (f"Thanksgiving table quiz, {band} 🦃🥧\n\n5 quick questions to try at the dinner table: pause after each "
            f"one, let everyone shout an answer, and see who wins. The last one is a bonus ⭐\n\n"
            f"Send this to the family group chat before Thursday 📲\n\nWho won at your table? Comment 👇\n\n"
            f"Happy Thanksgiving from paper lessons. Every kid learns at their own pace: free printable pages "
            f"for ages 3–12, link in bio.")
    return (f"# Thanksgiving table quiz · {band}\n\nMusic and sound are in the video.\n\n## Caption\n\n{body}\n\n"
            f"#thanksgiving #thanksgivingwithkids #familygames {tags} #momlife #paperlessons\n\n{credit('easy-lemon')}\n")


def countdown_caption(n: int, age: str, skill: str) -> str:
    who = f"ages {age}" if "+" in age else f"age {age}"
    nxt = "Merry Christmas! 🎄" if n == 24 else f"Follow along: a new puzzle every day until Christmas. Day {n + 1} is tomorrow 🎁"
    body = (f"Christmas countdown, day {n} of 24 🎄\n\nToday's puzzle is for {who} ({skill.lower()}). Pause, ask your kid, "
            f"and comment their answer 👇\n\n{nxt}\n\nEvery kid learns at their own pace: free printable pages for "
            f"ages 3–12, link in bio.")
    return (f"# Christmas countdown · day {n} ({who}, {skill})\n\nMusic and sound are in the video.\n\n## Caption\n\n{body}\n\n"
            f"#christmascountdown #adventcalendar #kidsactivities #momlife #homeschool #paperlessons\n\n"
            f"{credit('jingle-bells-calm')}\n")


def copy(src: Path, dest: Path, text: str) -> None:
    dest.mkdir(parents=True, exist_ok=True)
    shutil.copy(src, dest / "reel.mp4")
    (dest / "caption.md").write_text(text)


def main() -> None:
    n = 0
    for lv in LEVELS:
        src = APP / "out" / f"Level-{lv['slug']}.mp4"
        if src.exists():
            copy(src, OUT / f"level-{INDEX[lv['slug']]:02d}-{lv['slug']}", caption(lv, None, 4))
            n += 1
    by_slug = {lv["slug"]: lv for lv in LEVELS}
    for ts in sorted((APP / "src" / "topics").glob("*.ts")):
        for level, topic, secs in re.findall(r'level: "(\w+)",\s*topic: "([^"]+)",\s*seconds: (\d+)', ts.read_text()):
            src = APP / "out" / f"Topic-{level}-{slugify(topic)}.mp4"
            if not src.exists():
                print("missing render:", src.name)
                continue
            lv = by_slug[level]
            copy(src, OUT / "topics" / f"{INDEX[level]:02d}-{level}" / slugify(topic), caption(lv, topic, int(secs)))
            n += 1
    facts = (APP / "src" / "facts.ts").read_text()
    for g, who, level, block in re.findall(r'grade: "(\w+)", who: "([^"]+)", level: "(\w+)", items: \[(.*?)\n  \] \}', facts, re.S):
        src = APP / "out" / f"Facts-grade-{g}.mp4"
        if not src.exists():
            print("missing render:", src.name)
            continue
        items = re.findall(r'tag: "([^"]+)".*?code: "([^"]+)"', block)
        copy(src, OUT / "facts" / f"grade-{g}", facts_caption(g, who, by_slug[level], items))
        n += 1
    for age in map(int, re.findall(r"\{ age: (\d+), mascot:", (APP / "src" / "Milestones.tsx").read_text())):
        src = APP / "out" / f"Hands-age-{age}.mp4"
        if src.exists():
            copy(src, OUT / "hands" / f"age-{age}", hands_caption(age))
            n += 1
    rep = (APP / "src" / "Report.tsx").read_text()
    for g, y, nid, correct, picked in re.findall(
            r'r\(\{ grade: (\d+), year: (\d+), naepId: "([^"]+)".*?correct: (\d+), picked: \[([\d, ]+)\]', rep, re.S):
        rid = "Report-g" + g + "-" + re.sub(r"[^A-Za-z0-9]+", "-", nid).rstrip("-")
        src = APP / "out" / f"{rid}.mp4"
        if not src.exists():
            print("missing render:", src.name)
            continue
        pct = int(picked.split(",")[int(correct)])
        copy(src, OUT / "report" / rid.lower().removeprefix("report-"), report_caption(int(g), int(y), nid, pct))
        n += 1
        fast = APP / "out" / f"{rid.replace('Report-', 'Fast-')}.mp4"  # hook-first 12 s cut, same caption
        if fast.exists():
            copy(fast, OUT / "report-fast" / rid.lower().removeprefix("report-"), report_caption(int(g), int(y), nid, pct))
            n += 1
    for hid in re.findall(r'\{ id: "([a-z-]+)", band:', (APP / "src" / "holiday.ts").read_text()):
        src = APP / "out" / f"Holiday-{hid}.mp4"
        if src.exists():
            copy(src, OUT / "holiday" / hid, holiday_caption(hid))
            n += 1
    for d, age, skill in re.findall(r'/\* (\d+) \*/ \{ age: "([^"]+)", skill: "([^"]+)"', (APP / "src" / "countdown.ts").read_text()):
        src = APP / "out" / f"Countdown-day-{int(d):02d}.mp4"
        if src.exists():
            copy(src, OUT / "countdown" / f"day-{int(d):02d}", countdown_caption(int(d), age, skill))
            n += 1
    print(f"packaged {n} reels in {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
