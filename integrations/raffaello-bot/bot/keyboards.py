"""Tastiere di risposta. Non chiudono possibilità: guidano solo il gesto."""

from __future__ import annotations

from telegram import KeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove

REMOVE = ReplyKeyboardRemove()


def one(label: str) -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        [[KeyboardButton(label)]],
        resize_keyboard=True,
        one_time_keyboard=True,
    )


def grid(*rows: tuple[str, ...]) -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        [[KeyboardButton(c) for c in row] for row in rows],
        resize_keyboard=True,
        one_time_keyboard=False,
    )


def row(*labels: str) -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        [[KeyboardButton(label) for label in labels]],
        resize_keyboard=True,
        one_time_keyboard=True,
    )


KB_ENTRO = one("entro")
KB_LUCE = one("luce")
KB_ALTARE = one("altare")
KB_ACCENDO = one("accendo")
KB_ESCO = row("esco", "/annulla")
KB_VELI = row("1", "2", "3")
KB_P6 = row("/salta", "/annulla")
KB_MENU = grid(
    ("/tesi", "/santuario"),
    ("/tieni_aperto", "/azione"),
    ("/etichetta", "/lista"),
    ("/bussola", "/aiuto"),
)
KB_ROUTE = row("/etichetta", "/tieni_aperto", "/azione")
