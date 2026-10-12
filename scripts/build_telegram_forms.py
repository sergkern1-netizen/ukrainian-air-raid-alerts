"""
Generate the explicit word-form lists used by src/ingestion/telegram_nlp.py.

Run once (and after editing the lemma lists below) to regenerate:

    pip install -r requirements-gazetteer.txt
    python scripts/build_telegram_forms.py

pymorphy3 expands each lemma into every inflected form in its dictionary. The
runtime only reads the resulting JSON, so pymorphy3 is not a runtime dependency.
Forms are matched as whole tokens, which keeps "кримінальна" from matching Crimea.
"""

import json
from importlib.metadata import version
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

import pymorphy3

OUTPUT = (
    Path(__file__).resolve().parent.parent / "src" / "ingestion" / "data" / "telegram_forms.json"
)

# (canonical name, Ukrainian noun/lemma, Ukrainian adjective lemma or None,
#  Russian noun lemma, Russian adjective lemma or None)
PLACES: List[Tuple[str, str, Optional[str], str, Optional[str]]] = [
    ("kyiv", "київ", "київський", "киев", "киевский"),
    ("kharkiv", "харків", "харківський", "харьков", "харьковский"),
    ("donetsk", "донецьк", "донецький", "донецк", "донецкий"),
    ("luhansk", "луганськ", "луганський", "луганск", "луганский"),
    ("zaporizhzhia", "запоріжжя", "запорізький", "запорожье", "запорожский"),
    ("dnipro", "дніпро", "дніпровський", "днепр", "днепровский"),
    (
        "dnipropetrovsk",
        "дніпропетровськ",
        "дніпропетровський",
        "днепропетровск",
        "днепропетровский",
    ),
    ("odesa", "одеса", "одеський", "одесса", "одесский"),
    ("mykolaiv", "миколаїв", "миколаївський", "николаев", "николаевский"),
    ("kherson", "херсон", "херсонський", "херсон", "херсонский"),
    ("mariupol", "маріуполь", "маріупольський", "мариуполь", "мариупольский"),
    ("melitopol", "мелітополь", "мелітопольський", "мелитополь", "мелитопольский"),
    ("crimea", "крим", "кримський", "крым", "крымский"),
    ("lviv", "львів", "львівський", "львов", "львовский"),
    (
        "ivano-frankivsk",
        "івано-франківськ",
        "івано-франківський",
        "ивано-франковск",
        "ивано-франковский",
    ),
    ("ternopil", "тернопіль", "тернопільський", "тернополь", "тернопольский"),
    ("khmelnytskyi", "хмельницький", None, "хмельницкий", None),
    ("vinnytsia", "вінниця", "вінницький", "винница", "винницкий"),
    ("cherkasy", "черкаси", "черкаський", "черкассы", "черкасский"),
    ("poltava", "полтава", "полтавський", "полтава", "полтавский"),
    ("sumy", "суми", "сумський", "сумы", "сумской"),
    ("chernihiv", "чернігів", "чернігівський", "чернигов", "черниговский"),
    ("zhytomyr", "житомир", "житомирський", "житомир", "житомирский"),
    ("rivne", "рівне", "рівненський", "ровно", "ровенский"),
    ("volyn", "волинь", "волинський", "волынь", "волынский"),
    ("lutsk", "луцьк", "луцький", "луцк", "луцкий"),
    ("chernivtsi", "чернівці", "чернівецький", "черновцы", "черновицкий"),
    ("krivyy-rih", "кривий ріг", "криворізький", "кривой рог", "криворожский"),
    ("makiivka", "макіївка", "макіївський", "макеевка", "макеевский"),
    ("horlivka", "горлівка", "горлівський", "горловка", "горловский"),
    ("severodonetsk", "сєвєродонецьк", "сєвєродонецький", "северодонецк", "северодонецкий"),
    ("lysychansk", "лисичанськ", "лисичанський", "лисичанск", "лисичанский"),
    ("slovyansk", "слов'янськ", "слов'янський", "славянск", "славянский"),
    ("druzhkivka", "дружківка", "дружківський", "дружковка", "дружковский"),
    ("kramatorsk", "краматорськ", "краматорський", "краматорск", "краматорский"),
    ("irpin", "ірпінь", "ірпінський", "ирпень", "ирпенский"),
    ("bucha", "буча", "бучанський", "буча", "бучанский"),
    ("hostomel", "гостомель", "гостомельський", "гостомель", "гостомельский"),
]

# Multi-word place names cannot be inflected per word here, so their forms are listed.
PLACE_PHRASES: Dict[str, List[str]] = {
    "krivyy-rih": ["кривий ріг", "кривого рогу", "кривому розі", "кривим рогом", "кривой рог"],
}

# Forms that are also ordinary Ukrainian/Russian words. They match only when
# capitalized and preceded by a locative preposition ("у Сумах" is a different
# form, so it is unaffected; "суми" = "sums" is the trap this guards against).
LOCATION_HOMOGRAPHS = ["суми", "рівне", "ровно", "дніпро", "буча"]

# Event keywords: (event type, language, lemma, part of speech hint for pymorphy).
# Each lemma is one keyword group; all its inflected forms count toward that group.
EVENT_LEMMAS: List[Tuple[str, str, str]] = [
    ("missile", "uk", "ракета"),
    ("missile", "uk", "крилатий"),
    ("missile", "uk", "стратегічний"),
    ("missile", "ru", "ракета"),
    ("missile", "ru", "крылатый"),
    ("missile", "ru", "стратегический"),
    ("uav", "uk", "дрон"),
    ("uav", "uk", "безпілотник"),
    ("uav", "ru", "дрон"),
    ("uav", "ru", "беспилотник"),
    ("launch", "uk", "запуск"),
    ("launch", "uk", "атака"),
    ("launch", "uk", "раунд"),
    ("launch", "uk", "хвиля"),
    ("launch", "ru", "запуск"),
    ("launch", "ru", "атака"),
    ("launch", "ru", "раунд"),
    ("launch", "ru", "волна"),
    ("all_clear", "uk", "відбій"),
    ("all_clear", "ru", "отбой"),
]

# Forms that pymorphy cannot produce (abbreviations, English, past participles
# written as a fixed phrase). Matched as listed.
EVENT_LITERALS: Dict[str, List[str]] = {
    "missile": ["кх", "missile", "missiles", "cruise", "strategic"],
    "uav": ["бпла", "uav", "uavs", "drone", "drones", "unmanned"],
    "launch": ["launch", "launches", "round", "wave", "attack", "attacks"],
    "all_clear": [
        "all clear",
        "відмінено",
        "закінчено",
        "відміна",
        "отменено",
        "закончено",
        "cancelled",
        "finished",
    ],
}


def lexeme_forms(morph: pymorphy3.MorphAnalyzer, lemma: str) -> Set[str]:
    """Return every form of the dictionary entry whose normal form is exactly `lemma`."""
    forms: Set[str] = set()
    for parse in morph.parse(lemma):
        if parse.normal_form == lemma:
            forms |= {form.word for form in parse.lexeme}
            break
    else:
        raise ValueError(f"lemma not found in dictionary: {lemma!r}")
    return {form.lower() for form in forms}


def build() -> Dict[str, object]:
    uk = pymorphy3.MorphAnalyzer(lang="uk")
    ru = pymorphy3.MorphAnalyzer(lang="ru")
    analyzers = {"uk": uk, "ru": ru}

    locations: Dict[str, List[str]] = {}
    for canonical, uk_noun, uk_adj, ru_noun, ru_adj in PLACES:
        forms: Set[str] = set()
        forms |= lexeme_forms(uk, uk_noun) if " " not in uk_noun else set()
        forms |= lexeme_forms(ru, ru_noun) if " " not in ru_noun else set()
        if uk_adj:
            forms |= lexeme_forms(uk, uk_adj)
        if ru_adj:
            forms |= lexeme_forms(ru, ru_adj)
        forms |= {p.lower() for p in PLACE_PHRASES.get(canonical, [])}
        forms.add(uk_noun.lower())
        forms.add(ru_noun.lower())
        locations[canonical] = sorted(forms)

    events: Dict[str, List[Dict[str, object]]] = {}
    for event_type, lang, lemma in EVENT_LEMMAS:
        forms = lexeme_forms(analyzers[lang], lemma) | {lemma}
        events.setdefault(event_type, []).append(
            {"lemma": lemma, "lang": lang, "forms": sorted(forms)}
        )
    for event_type, literals in EVENT_LITERALS.items():
        events.setdefault(event_type, []).append(
            {
                "lemma": "literal",
                "lang": "literal",
                "forms": sorted({lit.lower() for lit in literals}),
            }
        )

    return {
        "generated_with": {
            "pymorphy3": version("pymorphy3"),
            "dicts_uk": version("pymorphy3-dicts-uk"),
            "dicts_ru": version("pymorphy3-dicts-ru"),
            "note": "run scripts/build_telegram_forms.py to regenerate",
        },
        "locations": locations,
        "location_homographs": sorted(LOCATION_HOMOGRAPHS),
        "events": events,
    }


def main() -> None:
    data = build()
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    total = sum(len(v) for v in data["locations"].values())
    print(f"wrote {OUTPUT} ({len(data['locations'])} places, {total} location forms)")


if __name__ == "__main__":
    main()
