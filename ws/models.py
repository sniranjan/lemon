"""Pydantic models for syllabus, content and generated sheets."""

from __future__ import annotations

import re
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

Subject = Literal["english", "math", "pencil"]
Severity = Literal["error", "warning"]
Source = Literal["chart", "ours"]

SUBJECT_PREFIX: dict[str, str] = {"english": "EN", "math": "MA", "pencil": ""}


class StrictModel(BaseModel):
    """A content or syllabus model that rejects unknown keys (typos in YAML fail loudly)."""

    model_config = ConfigDict(extra="forbid")


PageRange = tuple[int, int]


def _check_range(r: PageRange) -> PageRange:
    if r[0] < 1 or r[1] < r[0]:
        raise ValueError(f"bad page range {list(r)}")
    return r


def _check_tiling(ranges: list[PageRange], start: int, end: int, what: str) -> None:
    """Ranges must be in order, contiguous, and cover start..end exactly."""
    expected = start
    for lo, hi in ranges:
        if lo != expected:
            raise ValueError(f"{what}: expected a range starting at page {expected}, got {lo}")
        expected = hi + 1
    if expected != end + 1:
        raise ValueError(f"{what}: ranges end at page {expected - 1}, expected {end}")


_STANDARD = re.compile(
    r"(K|[1-8])\.[A-Z][A-Za-z]*\.\d+[a-z]?"                     # math K–8: K.CC.1, 3.OA.7, 4.NBT.5
    r"|(RL|RI|RF|W|SL|L)\.(K|[1-8]|9-10|11-12)\.\d+[a-z]?"      # ELA: RL.3.2, L.K.5c, RL.9-10.5
    r"|(HS[NAFGS][.-]|[NAFGS]-)[A-Z]{2,4}\.[A-Z]?\.?\d+[a-z]?"             # high-school math: A-REI.4, N-RN.1, HSN-RN.A.1, HSN.RN.A.1
)


def _check_standards(v: list[str]) -> list[str]:
    for code in v:
        if not _STANDARD.fullmatch(code):
            raise ValueError(f"standards: {code!r} doesn't look like a Common Core code")
    return v


class Part(StrictModel):
    part: int
    pages: PageRange
    name: str | None = None
    sheet_types: list[str] | None = None
    rules: dict[str, Any] = Field(default_factory=dict)
    source: Source | None = None
    standards: list[str] = Field(default_factory=list)   # extra codes for this part only

    @field_validator("pages")
    @classmethod
    def _valid_pages(cls, v: PageRange) -> PageRange:
        return _check_range(v)


    @field_validator("standards")
    @classmethod
    def _valid_standards(cls, v: list[str]) -> list[str]:
        return _check_standards(v)


class Section(StrictModel):
    code: str
    name: str                 # internal (planning) name
    public_name: str          # what parents and children see: our own name (CLAUDE.md §15)
    pages: PageRange
    sheet_types: list[str]
    rules: dict[str, Any] = Field(default_factory=dict)
    sct_minutes_per_page: tuple[float, float] | None = None
    parts: list[Part] = Field(default_factory=list)
    source: Source | None = None
    # Common Core codes this section teaches (CLAUDE.md §15), e.g. [K.CC.1, K.NBT.1]. Chicks is Pre-K
    # work, which has no Common Core codes, so its sections may leave this empty.
    standards: list[str] = Field(default_factory=list)
    # A warm-up or review section whose standards may all sit more than one grade below the level's
    # content_grade (ws/standards.py). Say why in a YAML comment next to the flag.
    on_ramp: bool = False
    review: bool = False

    @field_validator("standards")
    @classmethod
    def _valid_standards(cls, v: list[str]) -> list[str]:
        return _check_standards(v)

    @field_validator("pages")
    @classmethod
    def _valid_pages(cls, v: PageRange) -> PageRange:
        return _check_range(v)

    @model_validator(mode="after")
    def _parts_tile_section(self) -> Section:
        if not self.sheet_types:
            raise ValueError(f"section {self.code}: sheet_types must not be empty")
        if self.parts:
            nums = [p.part for p in self.parts]
            if nums != list(range(1, len(nums) + 1)):
                raise ValueError(f"section {self.code}: parts must be numbered 1..n in order")
            _check_tiling([p.pages for p in self.parts], *self.pages, f"section {self.code} parts")
        return self

    def part_for_page(self, page: int) -> Part | None:
        for p in self.parts:
            if p.pages[0] <= page <= p.pages[1]:
                return p
        return None


class Level(StrictModel):
    subject: Subject
    level: str                # internal code (7A, 6A, ZI): never printed on anything a buyer sees
    title: str
    # Public names come from syllabus/ladder.yaml (filled in by load_level, never set in the level file).
    public_name: str = ""     # e.g. "Chicks" (CLAUDE.md §15)
    public_title: str = ""    # e.g. "First words and counting"
    slug: str = ""            # site + R2 key, e.g. "chicks"
    preview_pages: list[int] = Field(default_factory=list)   # this strand's pages in the level's free preview
    aims: list[str] = Field(default_factory=list)
    pages: int
    daily_pages: int = 5
    sct_minutes_per_page: tuple[float, float] | None = None
    vocab_target: int | None = None
    rules: dict[str, Any] = Field(default_factory=dict)
    sections: list[Section]

    @model_validator(mode="after")
    def _sections_tile_level(self) -> Level:
        codes = [s.code for s in self.sections]
        expected = [chr(ord("A") + i) for i in range(len(codes))]
        if codes != expected:
            raise ValueError(f"{self.level}: section codes must be {expected} in page order, got {codes}")
        _check_tiling([s.pages for s in self.sections], 1, self.pages, f"{self.level} sections")
        bad = [p for p in self.preview_pages if not 1 <= p <= self.pages]
        if bad or len(set(self.preview_pages)) != len(self.preview_pages):
            raise ValueError(f"{self.level}: preview_pages must be distinct pages 1–{self.pages}, got {self.preview_pages}")
        return self

    def section(self, code: str) -> Section:
        for s in self.sections:
            if s.code == code:
                return s
        raise KeyError(f"{self.level} has no section {code!r}")

    def section_for_page(self, page: int) -> Section:
        for s in self.sections:
            if s.pages[0] <= page <= s.pages[1]:
                return s
        raise KeyError(f"page {page} is outside {self.level} (pages 1–{self.pages})")


class LadderLevel(StrictModel):
    """One public level (syllabus/ladder.yaml): a reading strand + a math strand (+ pencil early on)."""

    slug: str
    public_name: str
    public_title: str
    age: int                             # the one age a child on pace does this level
    content_grade: str                   # US grade the work matches: school grade at `age` + 2
    strands: dict[Subject, str]          # subject -> internal level code

    @model_validator(mode="after")
    def _valid(self) -> LadderLevel:
        if not re.fullmatch(r"[a-z][a-z0-9-]*", self.slug):
            raise ValueError(f"ladder: slug {self.slug!r} must be lowercase letters, digits and dashes")
        if not {"english", "math"} <= set(self.strands):
            raise ValueError(f"ladder: {self.slug} needs both an english and a math strand")
        return self


class PageSpec(StrictModel):
    """Everything a generator needs to know about one page, resolved from the syllabus."""

    subject: Subject
    level: str
    section: str
    part: int | None
    page: int
    sheet_type: str
    rules: dict[str, Any]
    # 0.0 on the first page of the part (or section, if it has no parts), 1.0 on the last;
    # lets a generator grow something across a part (e.g. line length).
    progress: float = 0.0


class VocabEntry(StrictModel):
    word: str
    picture: str | None = None   # None: a describing word (big, hot) shown through its noun's picture
    category: str
    level: str
    sentences: list[str] = Field(default_factory=list)
    placeholder: bool = False   # pipeline-test word, replaced by an approved batch
    mass: bool = False          # takes "some", not "a" (milk, bread)
    needs_color: bool = False   # only makes sense printed in color (color words)


class Issue(StrictModel):
    sheet_id: str
    severity: Severity
    message: str


class Sheet(StrictModel):
    id: str
    subject: Subject
    level: str
    section: str
    part: int | None = None
    sheet_type: str
    page_number: int
    variant: int = 1
    seed: int
    title: str
    parent_tip: str
    items: list[dict[str, Any]]
    answer_key: list[Any] | None = None
    new_words: list[str] = Field(default_factory=list)
    review_words: list[str] = Field(default_factory=list)
