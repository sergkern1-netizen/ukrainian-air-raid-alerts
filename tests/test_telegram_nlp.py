"""
Regression tests for explicit-form matching in telegram_nlp (see scripts/build_telegram_forms.py).

Negative cases are real false positives from the earlier prefix-stem matcher.
"""

import pytest

from src.ingestion.telegram_nlp import EventClassifier, LocationExtractor


@pytest.fixture(scope="module")
def locations() -> LocationExtractor:
    return LocationExtractor()


@pytest.fixture(scope="module")
def events() -> EventClassifier:
    return EventClassifier()


@pytest.mark.parametrize(
    "text, expected",
    [
        ("Кримінальна справа у Львові", ["lviv"]),  # крим- is not Crimea
        ("Луганськгаз оголосив про ремонт", []),  # company name, not the city
        ("Бучав сильний дощ всю ніч", []),  # verb, not Bucha
        ("Рівне рішення для всіх", []),  # "рівне" = even, lowercase, no preposition
        ("Суми грошей на рахунку зросли", []),  # "суми" = sums, sentence-initial homograph
    ],
)
def test_no_false_location_matches(locations: LocationExtractor, text: str, expected: list) -> None:
    assert locations.extract(text) == expected


@pytest.mark.parametrize(
    "text, expected",
    [
        ("Повітряна тривога у Київській області", ["kyiv"]),  # adjectival form
        ("Тривога в Харкові", ["kharkiv"]),  # locative
        ("Ракетна небезпека у Сумах", ["sumy"]),  # homograph city, locative in context
        ("Кривий Ріг під атакою", ["krivyy-rih"]),  # multi-word place
        ("Атака на Київ, Харків та Одесу", ["kharkiv", "kyiv", "odesa"]),
    ],
)
def test_expected_location_matches(locations: LocationExtractor, text: str, expected: list) -> None:
    assert locations.extract(text) == expected


def test_hyphenated_and_apostrophe_names_match(locations: LocationExtractor) -> None:
    assert locations.extract("Вибухи в Івано-Франківську") == ["ivano-frankivsk"]
    assert locations.extract("Тривога у Слов'янську") == ["slovyansk"]


@pytest.mark.parametrize(
    "text, expected",
    [
        (
            "Атаку дронами та БПЛА по Харкову",
            "uav",
        ),  # атаку (accusative) matches; 2 uav groups beat 1 launch
        ("Крилаті ракети в повітрі", "missile"),  # inflected stems
        ("Відбій повітряної тривоги", "all_clear"),
        ("Запуск ракет з моря", "launch"),
    ],
)
def test_event_inflections_are_recognized(
    events: EventClassifier, text: str, expected: str
) -> None:
    assert events.classify(text) == expected


def test_same_word_in_two_languages_counts_once(events: EventClassifier) -> None:
    """The uk and ru forms of one lemma form a single keyword group."""
    assert events.get_confidence("атака") == pytest.approx(0.65)


def test_unmatched_message_has_zero_confidence(events: EventClassifier) -> None:
    assert events.get_confidence("Тестовое сообщение") == 0.0
    assert events.classify("Тестовое сообщение") == "launch"
