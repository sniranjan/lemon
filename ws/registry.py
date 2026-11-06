"""Sheet-type registry (plugin pattern, CLAUDE.md §7)."""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import Any, ClassVar

from .exposure import ExposureTracker
from .models import Issue, PageSpec, Sheet
from .plan import LevelPlan

# Every sheet type named in the §7 catalogue. Syllabus YAML may only reference these;
# a name here need not be implemented yet (it is built when the child nears that level).
CATALOGUE: frozenset[str] = frozenset({
    "word_picture_pair", "word_picture_sentence", "review_grid_4", "word_story",
    "phrase_card", "sentence_recite", "letter_trace", "sound_parts", "word_trace",
    "colouring", "line_path",
    "count_and_say", "count_and_point", "number_read", "dots_to_number",
    "number_sequence", "number_trace", "number_write", "next_number", "add_facts",
    "letter_team", "rhyme_match", "sentence_trace",
    "fact_drill",
    # Cubs math (M2): place value, skip counting, column adding/taking away, story problems
    "place_value", "skip_count", "column_arithmetic", "math_story",
    # Puppies Reading (3A): spelling patterns, word endings, syllables, sentence copying
    "pattern_words", "word_endings", "syllable_split", "sentence_copy",
    # Foxes Reading (R3): passages with questions, word builders, full-sentence answers
    "passage_questions", "word_builder", "full_sentence_answer",
    # Foxes math (M3): fractions on a number line, times/sharing story problems
    "fraction_line", "story_problem",
    # Whales math (M9, Algebra 1): exponents and radicals, writing lines, inequalities on a number line, polynomials,
    # factoring, quadratics (graphing lines and inequalities extends coordinate_grid)
    "exponent_rules", "slope_intercept", "inequality_line", "polynomial_ops", "polynomial_factoring",
    "quadratic_solve",
    # Otters math (M5): fraction and decimal arithmetic, parentheses, volume (long division reuses division_house)
    "fraction_ops", "decimal_place_value", "decimal_column", "decimal_ops",
    "order_of_operations", "box_volume",
    # Pandas math (M6; dividing fractions extends fraction_ops): ratios, rates, percents, negatives, the coordinate
    # plane, expressions and one-step equations
    "ratio_table", "rational_story", "percent_problem", "signed_numbers",
    "coordinate_grid", "expression_eval", "equation_solve",
    "word_puzzle", "word_sort", "read_aloud",   # Cubs Reading (2A)
    # Owls math (M4): long multiplication, long division, factors and multiples, fraction bars
    "long_multiplication", "division_house", "factor_pairs", "fraction_bars",
    # Owls Reading (R4): long reads on one page and their questions on the next, context clues, summaries
    "long_read_page", "look_back_questions", "word_detective", "big_idea_summary",
})


@dataclass
class GenContext:
    spec: PageSpec
    rng: random.Random
    banks: dict[str, Any] = field(default_factory=dict)
    exposure: ExposureTracker = field(default_factory=ExposureTracker)
    plan: LevelPlan | None = None

    @property
    def rules(self) -> dict[str, Any]:
        return self.spec.rules

    def tip(self, sheet_type: str) -> str:
        """A parent tip for this page, picked by the seeded RNG.

        A part or section can supply its own under `rules.tips.<sheet_type>`; otherwise
        the subject-wide list in content/tips/<subject>.yaml is used.
        """
        options = self.rules.get("tips", {}).get(sheet_type) or self.banks["tips"].get(sheet_type)
        if not options:
            raise KeyError(f"no parent tips for {sheet_type!r} (add them to content/tips/{self.spec.subject}.yaml)")
        return self.rng.choice(options)


@dataclass
class SheetContent:
    title: str
    parent_tip: str
    items: list[dict[str, Any]]
    answer_key: list[Any] | None = None
    new_words: list[str] = field(default_factory=list)
    review_words: list[str] = field(default_factory=list)


class SheetType:
    name: ClassVar[str]
    template: ClassVar[str]

    def generate(self, ctx: GenContext) -> SheetContent:
        raise NotImplementedError

    def verify(self, sheet: Sheet) -> list[Issue]:
        return []


_REGISTRY: dict[str, type[SheetType]] = {}


def register(name: str):
    if name not in CATALOGUE:
        raise ValueError(f"sheet type {name!r} is not in the catalogue; add it to CATALOGUE first")

    def deco(cls: type[SheetType]) -> type[SheetType]:
        if name in _REGISTRY:
            raise ValueError(f"sheet type {name!r} registered twice")
        cls.name = name
        _REGISTRY[name] = cls
        return cls

    return deco


def get(name: str) -> SheetType:
    load_all()
    try:
        return _REGISTRY[name]()
    except KeyError:
        raise KeyError(f"sheet type {name!r} is not implemented yet") from None


def implemented() -> list[str]:
    load_all()
    return sorted(_REGISTRY)


def load_all() -> None:
    """Import every module in ws.sheet_types so their @register decorators run."""
    import importlib
    import pkgutil

    from . import sheet_types

    for mod in pkgutil.iter_modules(sheet_types.__path__):
        importlib.import_module(f"{sheet_types.__name__}.{mod.name}")
