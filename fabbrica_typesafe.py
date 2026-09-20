"""Bounded, advisory judgments for the existing Fabbrica planning flow.

No contacts, bookings or permissions are inferred from a model probability.
Only the submitted brief/revision goes to TypeSafe, never the user's archive.
"""
from __future__ import annotations

import hashlib
import json
import logging
import math

from typesafe_sister.client import TypeSafeNotConfigured, system_one
from typesafe_sister.policy import (
    FABBRICA_KINDS as KINDS,
    FABBRICA_LABELS as LABELS,
    FABBRICA_MISSING as MISSING,
    fabbrica_questions as questions,
)

LOGGER = logging.getLogger('terzi.fabbrica')


def probability(value):
    if type(value) not in (float, int) or not math.isfinite(value) or not 0 <= value <= 1:
        raise ValueError('Invalid probability')
    return float(value)


def assess_brief(brief, revision=''):
    state = {'brief': brief, 'revision': revision}
    try:
        result = system_one(state, questions(), timeout=8)
        answers = result['answers']
        occasion = answers['occasion']
        kind = occasion['choice']
        if occasion.get('type') != 'choice' or kind not in KINDS:
            raise ValueError('Invalid occasion')
        confidence = probability(occasion['confidence'])
        distribution = occasion['probabilities']
        if not isinstance(distribution, dict) or set(distribution) != set(KINDS):
            raise ValueError('Incomplete choices')
        distribution = {k: probability(v) for k, v in distribution.items()}
        if abs(sum(distribution.values()) - 1) > .02:
            raise ValueError('Invalid distribution')
        signals = {}
        for key in ['travel', 'music', *('missing_' + k for k in MISSING)]:
            if answers[key].get('type') != 'noul':
                raise ValueError('Invalid signal')
            signals[key] = probability(answers[key]['noul'])
        # Provisional thresholds only select reversible suggestions, never authorize
        # actions. Preserve probabilities for domain evaluation and later tuning.
        suggested_questions = [q for key, (_, q) in MISSING.items()
                               if signals['missing_' + key] >= .75][:3]
        return {'status': 'evaluated', 'provider': 'typesafe',
                'model': str(result.get('model', 'jev-latest'))[:100],
                'occasion': kind, 'label': LABELS[kind], 'confidence': confidence,
                'probabilities': distribution, 'signals': signals,
                'questions': suggested_questions,
                'policy_version': 'fabbrica-advisory-v1',
                'input_sha256': hashlib.sha256(json.dumps(state, sort_keys=True, ensure_ascii=False).encode()).hexdigest()}
    except TypeSafeNotConfigured:
        return {'status': 'not_configured'}
    except Exception as exc:
        # Never log a private brief, credential, or upstream exception body.
        LOGGER.warning(json.dumps({'event': 'typesafe_assessment_unavailable',
                                  'error_class': type(exc).__name__}))
        return {'status': 'unavailable'}
