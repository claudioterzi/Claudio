"""Stati delle ConversationHandler."""

from __future__ import annotations

from enum import IntEnum


class SanctuaryState(IntEnum):
    WAITING_ENTER = 10
    SILENCE = 11
    LIGHT = 12
    ALTAR = 13
    CANDLE = 14


class PossibilityState(IntEnum):
    WAITING_TEXT = 20
    WAITING_P6 = 21


class ActionState(IntEnum):
    WAITING_DESCRIPTION = 30


class VeloState(IntEnum):
    WAITING_CHOICE = 40


class EtichettaState(IntEnum):
    WAITING_TEXT = 50


class ScacchieraState(IntEnum):
    WAITING_CASA = 60


class LibroState(IntEnum):
    WAITING_PAGE = 70


class TestimoneState(IntEnum):
    WAITING_CHI = 80
    WAITING_ATTO = 81


class FuoriState(IntEnum):
    WAITING_ATTO = 90
