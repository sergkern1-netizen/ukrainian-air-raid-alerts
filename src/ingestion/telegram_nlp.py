"""
NLP components for Telegram message processing.

Includes location extraction (NER + gazetteer matching) and event type
classification (keyword-based) for Ukrainian Air Force channel messages.
"""

import logging
import re
from typing import List

logger = logging.getLogger(__name__)


class LocationExtractor:
    """
    Extract location mentions from text using gazetteer matching.

    Matches Ukrainian and Russian toponyms to known cities/oblasts.
    """

    # Ukrainian oblasts (administrative regions)
    UKRAINIAN_OBLASTS = {
        "kyiv": ["київ", "киев"],
        "kharkiv": ["харків", "харьков"],
        "donetsk": ["донецьк", "донецк"],
        "luhansk": ["луганськ", "луганск"],
        "zaporizhzhia": ["запоріжжя", "запорожье"],
        "dnipropetrovsk": ["дніпропетровськ", "днепропетровск"],
        "odesa": ["одеса", "одесса"],
        "mykolaiv": ["миколаїв", "николаев"],
        "kherson": ["херсон"],
        "crimea": ["крим", "крым"],
        "lviv": ["львів", "львов"],
        "ivano-frankivsk": ["івано-франківськ", "ивано-франковск"],
        "ternopil": ["тернопіль", "тернополь"],
        "khmelnytskyi": ["хмельницький", "хмельницкий"],
        "vinnytsia": ["вінниця", "винница"],
        "cherkasy": ["черкаси", "черкассы"],
        "poltava": ["полтава"],
        "sumy": ["суми", "сумы"],
        "chernihiv": ["чернігів", "чернигов"],
        "zhytomyr": ["житомир"],
        "rivne": ["рівне", "ровно"],
        "volyn": ["волинь", "волынь"],
    }

    # Major Ukrainian cities
    UKRAINIAN_CITIES = {
        # Stems for oblique cases: "Києві" -> "києв", "Харкові" -> "харков"
        "kyiv": ["київ", "києв", "киев", "kiyiv"],
        "kharkiv": ["харків", "харков", "харьков"],
        "donetsk": ["донецьк", "донецк"],
        "luhansk": ["луганськ", "луганск"],
        "zaporizhzhia": ["запоріжжя", "запорожье", "zaporizhia"],
        "dnipro": ["дніпро", "днепр"],
        "odesa": ["одеса", "одесса"],
        "mykolaiv": ["миколаїв", "николаев"],
        "kherson": ["херсон"],
        "mariupol": ["маріуполь", "мариуполь"],
        "melitopol": ["мелітополь", "мелитополь"],
        "lviv": ["львів", "львов"],
        "ivano-frankivsk": ["івано-франківськ", "ивано-франковск"],
        "ternopil": ["тернопіль", "тернополь"],
        "khmelnytskyi": ["хмельницький", "хмельницкий"],
        "vinnytsia": ["вінниця", "винница"],
        "cherkasy": ["черкаси", "черкассы"],
        "poltava": ["полтава"],
        "sumy": ["суми", "сумы"],
        "chernihiv": ["чернігів", "чернигов"],
        "zhytomyr": ["житомир"],
        "rivne": ["рівне", "ровно"],
        "lutsk": ["луцьк", "луцк"],
        "chernivtsi": ["чернівці", "черновцы"],
        "krivyy-rih": ["кривий-ріг", "кривой-рог"],
        "makiivka": ["макіївка", "макеевка"],
        "horlivka": ["горлівка", "горловка"],
        "severodonetsk": ["сєвєродонецьк", "северодонецк"],
        "lysychansk": ["лисичанськ", "лисичанск"],
        "slovyansk": ["слов'янськ", "славянск"],
        "druzhkivka": ["дружківка", "дружковка"],
        "kramatorsk": ["краматорськ", "краматорск"],
        "irpin": ["ірпінь", "ирпень"],
        "bucha": ["буча"],
        "hostomel": ["гостомель"],
    }

    def __init__(self) -> None:
        """Initialize location extractor with gazetteer."""
        self.oblasts = self._build_gazetteer(self.UKRAINIAN_OBLASTS)
        self.cities = self._build_gazetteer(self.UKRAINIAN_CITIES)

    def _build_gazetteer(self, location_dict: dict) -> dict:
        """
        Build gazetteer with normalized variants.

        Args:
            location_dict: Dictionary of location name to variants.

        Returns:
            Flattened gazetteer with all variants normalized.
        """
        gazetteer = {}
        for canonical, variants in location_dict.items():
            for variant in variants:
                # Normalize: lowercase, strip punctuation
                normalized = variant.lower().strip()
                gazetteer[normalized] = canonical
        return gazetteer

    def extract(self, text: str) -> List[str]:
        """
        Extract location mentions from text.

        Args:
            text: Message text to extract locations from.

        Returns:
            List of unique location names found.
        """
        if not text:
            return []

        # Normalize text
        normalized = text.lower()

        # Extract locations by matching gazetteer
        found_locations = set()

        # Check cities first (more specific). Match at word start only, with
        # trailing inflection allowed: Ukrainian/Russian nouns decline
        # ("Київ" -> "Київі", "Харків" -> "Харкові").
        for variant, canonical in self.cities.items():
            pattern = r"\b" + re.escape(variant) + r"\w*"
            if re.search(pattern, normalized):
                found_locations.add(canonical)

        # Check oblasts (less specific)
        for variant, canonical in self.oblasts.items():
            pattern = r"\b" + re.escape(variant) + r"\w*"
            if re.search(pattern, normalized):
                found_locations.add(canonical)

        logger.debug(f"Found locations: {found_locations}")
        return sorted(list(found_locations))


class EventClassifier:
    """
    Classify event type from Telegram message text.

    Uses keyword matching to classify messages into: launch, uav, missile, all_clear.
    """

    # Keywords for each event type
    LAUNCH_KEYWORDS = {
        "uk": ["запуск", "раунд", "хвиля", "атака"],
        "ru": ["запуск", "раунд", "волна", "атака"],
        "en": ["launch", "round", "wave", "attack"],
    }

    UAV_KEYWORDS = {
        "uk": ["дрон", "бпла", "безпілотник"],
        "ru": ["дрон", "бпла", "беспилотник"],
        "en": ["uav", "drone", "unmanned"],
    }

    # Stems: matched as word prefixes, so "ракет" covers ракета/ракети/ракету
    MISSILE_KEYWORDS = {
        "uk": ["ракет", "крилат", "стратег", "кх"],
        "ru": ["ракет", "крылат", "стратег", "кх"],
        "en": ["missile", "cruise", "strategic"],
    }

    ALL_CLEAR_KEYWORDS = {
        "uk": ["відбій", "відмінено", "закінчено"],
        "ru": ["отбой", "отменено", "закончено"],
        "en": ["all clear", "cancelled", "finished"],
    }

    # Confidence thresholds
    CONFIDENCE_THRESHOLD = 0.7

    def __init__(self) -> None:
        """Initialize event classifier with keyword patterns."""
        self.keywords = {
            "launch": self._flatten_keywords(self.LAUNCH_KEYWORDS),
            "uav": self._flatten_keywords(self.UAV_KEYWORDS),
            "missile": self._flatten_keywords(self.MISSILE_KEYWORDS),
            "all_clear": self._flatten_keywords(self.ALL_CLEAR_KEYWORDS),
        }

    def _flatten_keywords(self, keyword_dict: dict) -> List[str]:
        """
        Flatten language-specific keywords into single list.

        Args:
            keyword_dict: Dict of language -> list of keywords.

        Returns:
            Flattened list of keywords.
        """
        # Dedupe: shared stems (e.g. "дрон", "атака") appear in several languages
        # and would otherwise count twice toward the match score
        all_keywords = []
        for keywords in keyword_dict.values():
            all_keywords.extend(keywords)
        return list(dict.fromkeys(all_keywords))

    @staticmethod
    def _matches(keyword: str, normalized_text: str) -> bool:
        """
        Check whether a keyword occurs at the start of a word in the text.

        Args:
            keyword: Keyword stem to look for.
            normalized_text: Lowercased message text.

        Returns:
            True if the keyword starts at a word boundary.
        """
        return re.search(r"\b" + re.escape(keyword), normalized_text) is not None

    def classify(self, text: str) -> str:
        """
        Classify event type from message text.

        Args:
            text: Message text to classify.

        Returns:
            Event type: 'launch', 'uav', 'missile', or 'all_clear'.
            Defaults to 'launch' if no clear match found.
        """
        if not text:
            return "launch"

        normalized = text.lower()

        # Count keyword matches for each event type (word-prefix, so
        # "ракета" also matches "ракети" and "крилаті" matches "крилата")
        scores = {}
        for event_type, keywords in self.keywords.items():
            matches = sum(1 for kw in keywords if self._matches(kw, normalized))
            scores[event_type] = matches

        # Find highest scoring event type
        best_event = max(scores, key=scores.get)
        best_score = scores[best_event]

        # If no keywords matched, default to launch
        if best_score == 0:
            logger.debug("No keywords matched, defaulting to 'launch'")
            return "launch"

        logger.debug(f"Classified as '{best_event}' with {best_score} keyword matches")
        return best_event

    def get_confidence(self, text: str) -> float:
        """
        Get confidence score for classification.

        Args:
            text: Message text being classified.

        Returns:
            0.0 when no keyword matched (the event type is only a default),
            otherwise a score between 0.5 and 1.0 that rises with matches.
        """
        if not text:
            return 0.0

        normalized = text.lower()

        # Count total keyword matches
        total_matches = 0
        for keywords in self.keywords.values():
            total_matches += sum(1 for kw in keywords if self._matches(kw, normalized))

        if total_matches == 0:
            return 0.0

        # Confidence increases with more keyword matches
        # 1 match = 0.65, 2 matches = 0.8, 3+ matches = 0.95 (capped at 1.0)
        return min(0.5 + (total_matches * 0.15), 1.0)
