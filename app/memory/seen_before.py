"""Opt-in "you've seen this before". Stores fingerprints of pitches, never the user's messages.

TODO (if time): store (user_id, fingerprint, dossier_id) for opted-in users; match new pitches by fingerprint
or by company name / URL overlap with earlier dossiers; one-tap delete.
"""
from __future__ import annotations

import hashlib
import re


def fingerprint(text: str) -> str:
    normalised = re.sub(r"\W+", " ", text.lower()).strip()
    return hashlib.sha256(normalised.encode()).hexdigest()[:16]
