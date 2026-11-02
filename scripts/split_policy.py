"""Deterministic target-head groups for controlled synthetic experiments.

The same target noun lemma always receives the same split, across constructions,
inflections and linked tasks. Context words and templates may still cross splits;
this is a lexical challenge partition, not an independent gold benchmark.
"""
import hashlib
from functools import lru_cache
from lexicon import NOUNS, adjective_options, object_phrase

SPLITS = ("train", "validation", "test")
POLICY_VERSION = "target-head-v1"

@lru_cache(maxsize=1)
def phrase_heads():
    heads = {}
    for noun in NOUNS:
        for adjective in adjective_options(noun):
            for plural in (False, True):
                if noun.nom == "ტანსაცმელი" and plural:
                    continue
                for case in ("nom", "dat"):
                    phrase = object_phrase(noun, adjective, case, plural)
                    if phrase in heads and heads[phrase] != noun.nom:
                        raise ValueError("Ambiguous target head: " + phrase)
                    heads[phrase] = noun.nom
    return heads

def target_group(row):
    roles = row["roles"]
    for role in ("patient", "stimulus", "possessed", "located"):
        if role not in roles:
            continue
        phrase = roles[role]
        if role == "located":
            prefix = roles["possessor"] + " "
            if not phrase.startswith(prefix):
                raise ValueError("Located phrase lacks its possessive modifier")
            phrase = phrase[len(prefix):]
        try:
            return "noun:" + phrase_heads()[phrase]
        except KeyError as exc:
            raise ValueError("Unregistered target phrase: " + phrase) from exc
    if row["construction"] == "motion":
        return "motion_destination:" + roles["destination"]
    raise ValueError("No target group for " + row["id"])

@lru_cache(maxsize=None)
def group_split(group):
    value = hashlib.sha256((POLICY_VERSION + "|" + group).encode("utf-8")).digest()
    bucket = int.from_bytes(value[:8], "big") % 10000
    return "train" if bucket < 9000 else "validation" if bucket < 9500 else "test"

def row_split(row):
    return group_split(target_group(row))
