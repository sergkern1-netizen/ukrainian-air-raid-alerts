"""
NLP components for Telegram message processing.

Location and event keywords are explicit word-form lists generated offline from
the Ukrainian/Russian dictionaries by scripts/build_telegram_forms.py. Matching
is on whole tokens, so "кримінальна" does not match Crimea, and "луганськгаз"
(a company) does not match Luhansk. Homographs such as "суми" ("sums") only
match when capitalized after a locative preposition.
"""

import json
import logging
import re
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List, Set, Tuple

logger = logging.getLogger(__name__)

DATA_PATH = Path(__file__).resolve().parent / "data" / "telegram_forms.json"

# Letters, with internal apostrophes and hyphens kept ("слов'янськ", "івано-франківськ")
TOKEN_RE = re.compile(r"[^\W\d_]+(?:['’\-][^\W\d_]+)*")

LOCATIVE_PREPOSITIONS = {"в", "у", "на", "до", "з", "із", "від", "біля", "над", "під", "поблизу",
                         "около", "возле", "к"}

EVENT_ORDER = ("launch", "uav", "missile", "all_clear")


@lru_cache(maxsize=1)
def _load_data() -> Dict[str, Any]:
    """Load the generated form lists once per process."""
    with DATA_PATH.open(encoding="utf-8") as f:
        return json.load(f)


def _normalize(token: str) -> str:
    """Lowercase a token and unify the typographic apostrophe with the ASCII one."""
    return token.lower().replace("’", "'")


class LocationExtractor:
    """
    Extract location mentions from text by whole-token matching of generated forms.

    Covers Ukrainian and Russian names, including declined and adjectival forms.
    """

    def __init__(self) -> None:
        """Load the location forms and build the lookup tables."""
        data = _load_data()
        self._forms: Dict[str, str] = {}
        self._phrases: List[Tuple[str, str]] = []
        for canonical, forms in data["locations"].items():
            for form in forms:
                if " " in form:
                    self._phrases.append((form, canonical))
                else:
                    self._forms[form] = canonical
        self._homographs: Set[str] = set(data["location_homographs"])

    def extract(self, text: str) -> List[str]:
        """
        Extract location mentions from text.

        Args:
            text: Message text to extract locations from.

        Returns:
            Sorted list of unique canonical location names found.
        """
        if not text:
            return []

        found: Set[str] = set()
        tokens = list(TOKEN_RE.finditer(text))
        for index, match in enumerate(tokens):
            key = _normalize(match.group(0))
            canonical = self._forms.get(key)
            if canonical is None:
                continue
            if key in self._homographs and not self._is_locative_context(tokens, index):
                continue
            found.add(canonical)

        lowered = text.lower()
        for phrase, canonical in self._phrases:
            if re.search(r"(?<!\w)" + re.escape(phrase) + r"(?!\w)", lowered):
                found.add(canonical)

        logger.debug(f"Found locations: {found}")
        return sorted(found)

    @staticmethod
    def _is_locative_context(tokens: List["re.Match[str]"], index: int) -> bool:
        """
        Check that a homograph is capitalized and follows a locative preposition.

        Args:
            tokens: All word tokens of the message, in order.
            index: Position of the homograph token.

        Returns:
            True if the token looks like a place name in context.
        """
        word = tokens[index].group(0)
        if not word[0].isupper() or index == 0:
            return False
        return _normalize(tokens[index - 1].group(0)) in LOCATIVE_PREPOSITIONS


class EventClassifier:
    """
    Classify event type from Telegram message text.

    Keyword groups are keyed by lemma, so the Ukrainian and Russian forms of one
    word count once. Types: launch, uav, missile, all_clear.
    """

    # Confidence thresholds
    CONFIDENCE_THRESHOLD = 0.7

    def __init__(self) -> None:
        """Load the event keyword groups and build the lookup tables."""
        data = _load_data()
        self._form_groups: Dict[str, Set[Tuple[str, str]]] = {}
        self._phrase_groups: List[Tuple[str, Tuple[str, str]]] = []
        for event_type, groups in data["events"].items():
            for group in groups:
                group_id = (event_type, group["lemma"])
                for form in group["forms"]:
                    if " " in form:
                        self._phrase_groups.append((form, group_id))
                    else:
                        self._form_groups.setdefault(form, set()).add(group_id)

    def _matched_groups(self, text: str) -> Set[Tuple[str, str]]:
        """
        Return the keyword groups (event type, lemma) present in the text.

        Args:
            text: Message text.

        Returns:
            Set of (event type, lemma) pairs.
        """
        groups: Set[Tuple[str, str]] = set()
        for match in TOKEN_RE.finditer(text):
            groups |= self._form_groups.get(_normalize(match.group(0)), set())
        lowered = text.lower()
        for phrase, group_id in self._phrase_groups:
            if re.search(r"(?<!\w)" + re.escape(phrase) + r"(?!\w)", lowered):
                groups.add(group_id)
        return groups

    def classify(self, text: str) -> str:
        """
        Classify event type from message text.

        Args:
            text: Message text to classify.

        Returns:
            Event type: 'launch', 'uav', 'missile', or 'all_clear'.
            Defaults to 'launch' if no keyword matched; check get_confidence to
            tell a match from the default.
        """
        if not text:
            return "launch"

        scores = {event: 0 for event in EVENT_ORDER}
        for event_type, _ in self._matched_groups(text):
            scores[event_type] += 1

        best_event = max(EVENT_ORDER, key=lambda event: scores[event])
        if scores[best_event] == 0:
            logger.debug("No keywords matched, defaulting to 'launch'")
            return "launch"

        logger.debug(f"Classified as '{best_event}' with {scores[best_event]} keyword groups")
        return best_event

    def get_confidence(self, text: str) -> float:
        """
        Get confidence score for classification.

        Args:
            text: Message text being classified.

        Returns:
            0.0 when no keyword matched (the event type is only a default),
            otherwise a score between 0.5 and 1.0 that rises with matched keyword groups.
        """
        if not text:
            return 0.0

        total = len(self._matched_groups(text))
        if total == 0:
            return 0.0

        # 1 group = 0.65, 2 groups = 0.8, 3+ groups = 0.95 (capped at 1.0)
        return min(0.5 + (total * 0.15), 1.0)
