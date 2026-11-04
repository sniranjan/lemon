"""Pydantic models for syllabus, content and generated sheets."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

Subject = Literal["english", "math", "pencil"]
Severity = Literal["error", "warning"]
Source = Literal["chart", "ours"]

SUBJECT_PREFIX: dict[str, str] = {"english": "EN", "math": "MA", "pencil": ""}


class _Strict(BaseModel):
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


class Part(_Strict):
    part: int
    pages: PageRange
    name: str | None = None
    sheet_types: list[str] | None = None
    rules: dict[str, Any] = Field(default_factory=dict)
    source: Source | None = None

    @field_validator("pages")
    @classmethod
    def _valid_pages(cls, v: PageRange) -> PageRange:
        return _check_range(v)


class Section(_Strict):
    code: str
    name: str
    pages: PageRange
    sheet_types: list[str]
    rules: dict[str, Any] = Field(default_factory=dict)
    sct_minutes_per_page: tuple[float, float] | None = None
    parts: list[Part] = Field(default_factory=list)
    source: Source | None = None

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


class Level(_Strict):
    subject: Subject
    level: str
    title: str
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


class PageSpec(_Strict):
    """Everything a generator needs to know about one page, resolved from the syllabus."""

    subject: Subject
    level: str
    section: str
    part: int | None
    page: int
    sheet_type: str
    rules: dict[str, Any]


class VocabEntry(_Strict):
    word: str
    picture: str
    category: str
    level: str
    sentences: list[str] = Field(default_factory=list)
    placeholder: bool = False   # pipeline-test word, replaced by an approved batch


class Issue(_Strict):
    sheet_id: str
    severity: Severity
    message: str


class Sheet(_Strict):
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
