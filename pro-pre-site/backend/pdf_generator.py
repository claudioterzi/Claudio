"""PDF Contract generator for Pro-pre free trial contracts (Défi de la Bande).
Uses reportlab to create a client-facing PDF contract with:
- Client info + service info + price
- Before photo (embedded)
- Reserved space for After photo (uploaded later by admin)
- Client signature (typed name in cursive/handwriting font)
- Fixed Claudio Terzi signature on the right
"""
from __future__ import annotations

import base64
import io
from datetime import datetime, timezone
from typing import Dict, Optional

from PIL import Image as PILImage
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm, mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    HRFlowable,
    Image,
    KeepInFrame,
    PageBreak,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    SimpleDocTemplate,
)

# Colors matching Pro-pre brand
NAVY = colors.HexColor("#1B2845")
BLUE = colors.HexColor("#5BA4D4")
SOFT = colors.HexColor("#F1F5F9")
BORDER = colors.HexColor("#CBD5E1")
TEXT_MUTED = colors.HexColor("#64748B")

# I18N strings for the PDF (FR, EN, ES, NL, IT)
I18N = {
    "fr": {
        "doc_title": "Contrat de test gratuit — Défi de la Bande",
        "kicker": "Pro-pre · Nettoyage textile professionnel",
        "client_info": "Informations client",
        "full_name": "Nom complet",
        "email": "Email",
        "phone": "Téléphone",
        "address": "Adresse",
        "postal_city": "CP · Ville",
        "date": "Date d'intervention",
        "time_slot": "Créneau",
        "service": "Service concerné",
        "estimated_price": "Prix estimé (si nettoyage complet)",
        "dirty_area": "Zone la plus sale (indiquée par le client)",
        "conditions_title": "Conditions du Défi de la Bande",
        "conditions": [
            "La visite à domicile pour le Défi de la Bande est <b>100 % GRATUITE</b>, sans obligation d'achat.",
            "Un test de nettoyage sera effectué sur une bande visible d'environ 30 × 30 cm dans la zone la plus sale indiquée par le client.",
            "Après le test, le client décide librement s'il souhaite faire nettoyer l'ensemble du meuble aux tarifs indiqués — ou refuser sans frais.",
            "Aucun acompte n'est exigé. Le paiement de 30 € proposé est facultatif et remboursé si le service complet est confirmé.",
            "Les photos avant/après restent la propriété du client et ne sont utilisées qu'avec son consentement explicite.",
        ],
        "deposit": "Acompte (facultatif)",
        "deposit_none": "Aucun acompte — paiement à la fin uniquement",
        "deposit_revolut": "30 € payés via Revolut (checkout en ligne)",
        "deposit_bonifico": "30 € par virement bancaire (IBAN communiqué séparément)",
        "deposit_in_person": "30 € en espèces à l'arrivée du technicien",
        "photo_before": "Photo AVANT (fournie par le client)",
        "photo_after": "Photo APRÈS (à compléter par Pro-pre lors de l'intervention)",
        "photo_after_pending": "Espace réservé — la photo sera ajoutée par Pro-pre à la fin du test",
        "signatures": "Signatures",
        "client_signature": "Signature du client",
        "prestataire_signature": "Signature Pro-pre",
        "prestataire_name": "Claudio Terzi",
        "prestataire_role": "Fondateur — Pro-pre Nettoyage",
        "signed_on": "Signé le",
        "in": "à",
        "footer_legal": "Contrat émis électroniquement — Pro-pre Nettoyage · www.pro-pre.com · Terziclaudio@gmail.com · +33 6 74 93 20 00",
        "page": "Page",
        "of": "sur",
        "contract_id": "Réf. contrat",
        "no_photo": "Photo non fournie",
    },
    "en": {
        "doc_title": "Free Trial Contract — The Band Challenge",
        "kicker": "Pro-pre · Professional textile cleaning",
        "client_info": "Client information",
        "full_name": "Full name",
        "email": "Email",
        "phone": "Phone",
        "address": "Address",
        "postal_city": "ZIP · City",
        "date": "Service date",
        "time_slot": "Time slot",
        "service": "Related service",
        "estimated_price": "Estimated price (for full cleaning)",
        "dirty_area": "Dirtiest area (indicated by client)",
        "conditions_title": "Terms of The Band Challenge",
        "conditions": [
            "The home visit for The Band Challenge is <b>100% FREE</b>, no purchase required.",
            "A cleaning test will be performed on a visible ~30 × 30 cm strip on the dirtiest area indicated by the client.",
            "After the test, the client freely decides whether to have the whole item cleaned at the listed prices — or decline at no cost.",
            "No deposit is required. The 30 € optional payment is refunded if the full service is booked.",
            "Before/after photos remain the client's property and will only be used with explicit consent.",
        ],
        "deposit": "Deposit (optional)",
        "deposit_none": "No deposit — payment at the end only",
        "deposit_revolut": "€30 paid via Revolut (online checkout)",
        "deposit_bonifico": "€30 bank transfer (IBAN sent separately)",
        "deposit_in_person": "€30 cash on arrival",
        "photo_before": "BEFORE photo (provided by client)",
        "photo_after": "AFTER photo (to be added by Pro-pre after the test)",
        "photo_after_pending": "Reserved space — the photo will be added by Pro-pre at the end of the test",
        "signatures": "Signatures",
        "client_signature": "Client signature",
        "prestataire_signature": "Pro-pre signature",
        "prestataire_name": "Claudio Terzi",
        "prestataire_role": "Founder — Pro-pre Nettoyage",
        "signed_on": "Signed on",
        "in": "in",
        "footer_legal": "Electronic contract issued — Pro-pre Nettoyage · www.pro-pre.com · Terziclaudio@gmail.com · +33 6 74 93 20 00",
        "page": "Page",
        "of": "of",
        "contract_id": "Contract ref.",
        "no_photo": "No photo provided",
    },
    "es": {
        "doc_title": "Contrato de prueba gratuita — Desafío de la Franja",
        "kicker": "Pro-pre · Limpieza textil profesional",
        "client_info": "Información del cliente",
        "full_name": "Nombre completo",
        "email": "Email",
        "phone": "Teléfono",
        "address": "Dirección",
        "postal_city": "CP · Ciudad",
        "date": "Fecha del servicio",
        "time_slot": "Franja horaria",
        "service": "Servicio relacionado",
        "estimated_price": "Precio estimado (limpieza completa)",
        "dirty_area": "Zona más sucia (indicada por el cliente)",
        "conditions_title": "Términos del Desafío de la Franja",
        "conditions": [
            "La visita a domicilio para el Desafío de la Franja es <b>100 % GRATUITA</b>, sin compromiso de compra.",
            "Se realizará una prueba de limpieza en una franja visible de ~30 × 30 cm en la zona más sucia indicada por el cliente.",
            "Tras la prueba, el cliente decide libremente si desea limpiar todo el mueble a las tarifas indicadas — o rechazar sin coste.",
            "No se exige anticipo. El pago opcional de 30 € se reembolsa si se confirma el servicio completo.",
            "Las fotos antes/después son propiedad del cliente y solo se usarán con su consentimiento explícito.",
        ],
        "deposit": "Anticipo (opcional)",
        "deposit_none": "Sin anticipo — pago al final",
        "deposit_revolut": "30 € pagados por Revolut (checkout online)",
        "deposit_bonifico": "30 € por transferencia bancaria (IBAN aparte)",
        "deposit_in_person": "30 € en efectivo a la llegada",
        "photo_before": "Foto ANTES (aportada por el cliente)",
        "photo_after": "Foto DESPUÉS (a completar por Pro-pre)",
        "photo_after_pending": "Espacio reservado — la foto será añadida por Pro-pre al final de la prueba",
        "signatures": "Firmas",
        "client_signature": "Firma del cliente",
        "prestataire_signature": "Firma Pro-pre",
        "prestataire_name": "Claudio Terzi",
        "prestataire_role": "Fundador — Pro-pre Nettoyage",
        "signed_on": "Firmado el",
        "in": "en",
        "footer_legal": "Contrato emitido electrónicamente — Pro-pre Nettoyage · www.pro-pre.com · Terziclaudio@gmail.com · +33 6 74 93 20 00",
        "page": "Página",
        "of": "de",
        "contract_id": "Ref. contrato",
        "no_photo": "Sin foto",
    },
    "nl": {
        "doc_title": "Gratis proefcontract — De Bandtest",
        "kicker": "Pro-pre · Professionele textielreiniging",
        "client_info": "Klantgegevens",
        "full_name": "Volledige naam",
        "email": "Email",
        "phone": "Telefoon",
        "address": "Adres",
        "postal_city": "Postcode · Stad",
        "date": "Datum van dienstverlening",
        "time_slot": "Tijdslot",
        "service": "Betreffende dienst",
        "estimated_price": "Geschatte prijs (volledige reiniging)",
        "dirty_area": "Vuilste zone (aangewezen door de klant)",
        "conditions_title": "Voorwaarden van De Bandtest",
        "conditions": [
            "Het huisbezoek voor De Bandtest is <b>100 % GRATIS</b>, zonder aankoopverplichting.",
            "Er wordt een reinigingstest uitgevoerd op een zichtbare strook van ~30 × 30 cm in de vuilste zone.",
            "Na de test beslist de klant vrij of het hele meubel gereinigd wordt tegen de vermelde tarieven — of afwijzen zonder kosten.",
            "Geen aanbetaling vereist. De optionele betaling van 30 € wordt terugbetaald bij bevestiging van de volledige service.",
            "Voor/na foto's blijven eigendom van de klant en worden alleen met expliciete toestemming gebruikt.",
        ],
        "deposit": "Aanbetaling (optioneel)",
        "deposit_none": "Geen aanbetaling — betaling aan het einde",
        "deposit_revolut": "€30 betaald via Revolut (online checkout)",
        "deposit_bonifico": "€30 per bankoverschrijving (IBAN apart)",
        "deposit_in_person": "€30 contant bij aankomst",
        "photo_before": "VOOR foto (door de klant geleverd)",
        "photo_after": "NA foto (in te vullen door Pro-pre)",
        "photo_after_pending": "Gereserveerde ruimte — de foto wordt aan het einde van de test toegevoegd",
        "signatures": "Handtekeningen",
        "client_signature": "Handtekening klant",
        "prestataire_signature": "Handtekening Pro-pre",
        "prestataire_name": "Claudio Terzi",
        "prestataire_role": "Oprichter — Pro-pre Nettoyage",
        "signed_on": "Ondertekend op",
        "in": "in",
        "footer_legal": "Elektronisch contract uitgegeven — Pro-pre Nettoyage · www.pro-pre.com · Terziclaudio@gmail.com · +33 6 74 93 20 00",
        "page": "Pagina",
        "of": "van",
        "contract_id": "Contract ref.",
        "no_photo": "Geen foto",
    },
    "it": {
        "doc_title": "Contratto di prova gratuita — Sfida della Striscia",
        "kicker": "Pro-pre · Pulizia tessile professionale",
        "client_info": "Informazioni cliente",
        "full_name": "Nome completo",
        "email": "Email",
        "phone": "Telefono",
        "address": "Indirizzo",
        "postal_city": "CAP · Città",
        "date": "Data intervento",
        "time_slot": "Fascia oraria",
        "service": "Servizio interessato",
        "estimated_price": "Prezzo stimato (pulizia completa)",
        "dirty_area": "Zona più sporca (indicata dal cliente)",
        "conditions_title": "Condizioni della Sfida della Striscia",
        "conditions": [
            "La visita a domicilio per la Sfida della Striscia è <b>100 % GRATUITA</b>, senza obbligo di acquisto.",
            "Un test di pulizia sarà effettuato su una striscia visibile di circa 30 × 30 cm nella zona più sporca indicata dal cliente.",
            "Dopo il test, il cliente decide liberamente se procedere con la pulizia completa alle tariffe indicate — o rifiutare senza costi.",
            "Nessun acconto è richiesto. Il pagamento di 30 € proposto è facoltativo e viene rimborsato al momento del servizio completo.",
            "Le foto prima/dopo restano di proprietà del cliente e verranno usate solo con consenso esplicito.",
        ],
        "deposit": "Acconto (facoltativo)",
        "deposit_none": "Nessun acconto — pagamento alla fine",
        "deposit_revolut": "30 € pagati con Revolut (checkout online)",
        "deposit_bonifico": "30 € tramite bonifico (IBAN comunicato separatamente)",
        "deposit_in_person": "30 € in contanti all'arrivo del tecnico",
        "photo_before": "Foto PRIMA (fornita dal cliente)",
        "photo_after": "Foto DOPO (da completare da Pro-pre)",
        "photo_after_pending": "Spazio riservato — la foto sarà aggiunta da Pro-pre al termine del test",
        "signatures": "Firme",
        "client_signature": "Firma del cliente",
        "prestataire_signature": "Firma Pro-pre",
        "prestataire_name": "Claudio Terzi",
        "prestataire_role": "Fondatore — Pro-pre Nettoyage",
        "signed_on": "Firmato il",
        "in": "in",
        "footer_legal": "Contratto emesso elettronicamente — Pro-pre Nettoyage · www.pro-pre.com · Terziclaudio@gmail.com · +33 6 74 93 20 00",
        "page": "Pagina",
        "of": "di",
        "contract_id": "Rif. contratto",
        "no_photo": "Nessuna foto",
    },
}


def _t(lang: str, key: str):
    lang = lang if lang in I18N else "fr"
    return I18N[lang].get(key, I18N["fr"].get(key, key))


def _make_styles():
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(
        name="Kicker", parent=styles["Normal"],
        fontName="Helvetica-Bold", fontSize=8, textColor=BLUE,
        spaceAfter=4, alignment=0, tracking=1,
    ))
    styles.add(ParagraphStyle(
        name="TitleNavy", parent=styles["Title"],
        fontName="Helvetica-Bold", fontSize=20, textColor=NAVY,
        spaceAfter=6,
    ))
    styles.add(ParagraphStyle(
        name="H2", parent=styles["Heading2"],
        fontName="Helvetica-Bold", fontSize=12, textColor=NAVY,
        spaceBefore=10, spaceAfter=6,
    ))
    styles.add(ParagraphStyle(
        name="Body", parent=styles["BodyText"],
        fontName="Helvetica", fontSize=9.5, textColor=colors.HexColor("#334155"),
        leading=13, spaceAfter=3,
    ))
    styles.add(ParagraphStyle(
        name="Muted", parent=styles["BodyText"],
        fontName="Helvetica", fontSize=8, textColor=TEXT_MUTED,
    ))
    # Signature "handwriting-like" style (italic, larger)
    styles.add(ParagraphStyle(
        name="Signature", parent=styles["Normal"],
        fontName="Helvetica-Oblique", fontSize=22, textColor=NAVY,
        alignment=1,
    ))
    styles.add(ParagraphStyle(
        name="SignatureFixed", parent=styles["Normal"],
        fontName="Helvetica-BoldOblique", fontSize=22, textColor=NAVY,
        alignment=1,
    ))
    styles.add(ParagraphStyle(
        name="SigLabel", parent=styles["Normal"],
        fontName="Helvetica-Bold", fontSize=8, textColor=TEXT_MUTED,
        alignment=1, spaceAfter=2,
    ))
    styles.add(ParagraphStyle(
        name="SigRole", parent=styles["Normal"],
        fontName="Helvetica", fontSize=8, textColor=TEXT_MUTED,
        alignment=1,
    ))
    return styles


def _decode_image_bytes(data_url_or_b64: Optional[str]) -> Optional[bytes]:
    if not data_url_or_b64:
        return None
    try:
        raw = data_url_or_b64
        if raw.startswith("data:"):
            _, b64 = raw.split(",", 1)
        else:
            b64 = raw
        return base64.b64decode(b64)
    except Exception:
        return None


def _fit_image(data: bytes, max_w: float, max_h: float) -> Optional[Image]:
    try:
        bio = io.BytesIO(data)
        pil = PILImage.open(bio)
        pil.thumbnail((1600, 1600))
        out = io.BytesIO()
        pil = pil.convert("RGB") if pil.mode not in ("RGB", "L") else pil
        pil.save(out, format="JPEG", quality=82)
        out.seek(0)
        img = Image(out, width=max_w, height=max_h, kind="proportional")
        return img
    except Exception:
        return None


def _placeholder_box(text: str, w: float, h: float, styles) -> Table:
    """Empty framed box with dashed border for the AFTER photo placeholder."""
    p = Paragraph(f"<i>{text}</i>", styles["Muted"])
    t = Table([[p]], colWidths=[w], rowHeights=[h])
    t.setStyle(TableStyle([
        ("BOX", (0, 0), (-1, -1), 1, BORDER),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("BACKGROUND", (0, 0), (-1, -1), SOFT),
    ]))
    return t


def generate_contract_pdf(
    contract: Dict,
    photo_before_b64: Optional[str] = None,
    photo_after_b64: Optional[str] = None,
) -> bytes:
    """Generate a PDF contract given the contract dict.
    contract keys used: id, client_name, client_email, client_phone, address, city, postal_code,
        date, time_slot, service_label, service_price, dirty_area_description,
        signature_typed, deposit_choice, language, city_signed, signed_at (ISO)
    """
    lang = (contract.get("language") or "fr").lower()
    if lang not in I18N:
        lang = "fr"

    styles = _make_styles()
    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=A4,
        leftMargin=1.5 * cm, rightMargin=1.5 * cm,
        topMargin=1.5 * cm, bottomMargin=1.5 * cm,
        title=f"Pro-pre — {_t(lang, 'doc_title')}",
        author="Pro-pre Nettoyage Professionnel",
    )
    story = []

    # --- HEADER ---
    story.append(Paragraph(_t(lang, "kicker"), styles["Kicker"]))
    story.append(Paragraph(_t(lang, "doc_title"), styles["TitleNavy"]))
    ref_line = f"{_t(lang,'contract_id')}: <b>{contract.get('id','')[:8].upper()}</b>"
    story.append(Paragraph(ref_line, styles["Muted"]))
    story.append(HRFlowable(width="100%", thickness=1, color=BLUE, spaceBefore=6, spaceAfter=10))

    # --- CLIENT INFO (2-column table) ---
    story.append(Paragraph(_t(lang, "client_info"), styles["H2"]))

    def kv(key, val):
        return [Paragraph(f"<font color='#64748B'>{_t(lang, key)}</font>", styles["Body"]),
                Paragraph(f"<b>{val or '—'}</b>", styles["Body"])]

    info_rows = [
        kv("full_name", contract.get("client_name", "")),
        kv("email", contract.get("client_email", "")),
        kv("phone", contract.get("client_phone", "")),
        kv("address", contract.get("address", "")),
        kv("postal_city", f"{contract.get('postal_code','')} · {contract.get('city','')}"),
        kv("date", contract.get("date", "")),
        kv("time_slot", contract.get("time_slot", "")),
        kv("service", contract.get("service_label", "")),
        kv("estimated_price", f"€ {contract.get('service_price', 0)}"),
        kv("dirty_area", contract.get("dirty_area_description", "")),
    ]
    info_table = Table(info_rows, colWidths=[5 * cm, 12 * cm])
    info_table.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("ROWBACKGROUNDS", (0, 0), (-1, -1), [colors.white, SOFT]),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("BOX", (0, 0), (-1, -1), 0.5, BORDER),
    ]))
    story.append(info_table)
    story.append(Spacer(1, 8))

    # --- CONDITIONS ---
    story.append(Paragraph(_t(lang, "conditions_title"), styles["H2"]))
    for c in _t(lang, "conditions"):
        story.append(Paragraph(f"• {c}", styles["Body"]))
    story.append(Spacer(1, 4))

    # --- DEPOSIT LINE ---
    deposit_choice = (contract.get("deposit_choice") or "none").lower()
    dep_key = f"deposit_{deposit_choice}" if deposit_choice in ("revolut", "bonifico", "in_person") else "deposit_none"
    story.append(Paragraph(f"<b>{_t(lang, 'deposit')}:</b> {_t(lang, dep_key)}", styles["Body"]))
    story.append(Spacer(1, 10))

    # --- PHOTOS SIDE BY SIDE ---
    photo_w = 7.5 * cm
    photo_h = 7.5 * cm

    before_bytes = _decode_image_bytes(photo_before_b64)
    if before_bytes:
        before_img = _fit_image(before_bytes, photo_w, photo_h)
        before_cell = before_img if before_img else _placeholder_box(_t(lang, "no_photo"), photo_w, photo_h, styles)
    else:
        before_cell = _placeholder_box(_t(lang, "no_photo"), photo_w, photo_h, styles)

    after_bytes = _decode_image_bytes(photo_after_b64)
    if after_bytes:
        after_img = _fit_image(after_bytes, photo_w, photo_h)
        after_cell = after_img if after_img else _placeholder_box(_t(lang, "photo_after_pending"), photo_w, photo_h, styles)
    else:
        after_cell = _placeholder_box(_t(lang, "photo_after_pending"), photo_w, photo_h, styles)

    photo_table = Table(
        [
            [Paragraph(f"<b>{_t(lang, 'photo_before')}</b>", styles["Body"]),
             Paragraph(f"<b>{_t(lang, 'photo_after')}</b>", styles["Body"])],
            [before_cell, after_cell],
        ],
        colWidths=[photo_w, photo_w],
    )
    photo_table.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 4),
    ]))
    story.append(photo_table)
    story.append(Spacer(1, 12))

    # --- SIGNATURES ---
    story.append(Paragraph(_t(lang, "signatures"), styles["H2"]))
    signature_typed = contract.get("signature_typed") or contract.get("client_name") or ""
    signed_at_raw = contract.get("signed_at") or datetime.now(timezone.utc).isoformat()
    try:
        dt = datetime.fromisoformat(signed_at_raw.replace("Z", "+00:00"))
    except Exception:
        dt = datetime.now(timezone.utc)
    signed_str = dt.strftime("%d/%m/%Y %H:%M UTC")
    city_signed = contract.get("city_signed") or contract.get("city") or "Bruxelles"

    sig_col_w = 8.5 * cm
    sig_table = Table(
        [
            [Paragraph(_t(lang, "client_signature"), styles["SigLabel"]),
             Paragraph(_t(lang, "prestataire_signature"), styles["SigLabel"])],
            [Paragraph(signature_typed, styles["Signature"]),
             Paragraph(_t(lang, "prestataire_name"), styles["SignatureFixed"])],
            [Paragraph(contract.get("client_name") or "", styles["SigRole"]),
             Paragraph(_t(lang, "prestataire_role"), styles["SigRole"])],
            [Paragraph(f"{_t(lang,'signed_on')} {signed_str} · {_t(lang,'in')} {city_signed}", styles["SigRole"]),
             Paragraph(f"{_t(lang,'signed_on')} {signed_str} · {_t(lang,'in')} {city_signed}", styles["SigRole"])],
        ],
        colWidths=[sig_col_w, sig_col_w],
    )
    sig_table.setStyle(TableStyle([
        ("BOX", (0, 0), (0, -1), 0.5, BORDER),
        ("BOX", (1, 0), (1, -1), 0.5, BORDER),
        ("LEFTPADDING", (0, 0), (-1, -1), 12),
        ("RIGHTPADDING", (0, 0), (-1, -1), 12),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("LINEBELOW", (0, 1), (0, 1), 0.5, colors.HexColor("#94A3B8")),
        ("LINEBELOW", (1, 1), (1, 1), 0.5, colors.HexColor("#94A3B8")),
    ]))
    story.append(sig_table)

    # --- FOOTER ---
    def _footer(canvas_obj, doc_obj):
        canvas_obj.saveState()
        canvas_obj.setFont("Helvetica", 7)
        canvas_obj.setFillColor(TEXT_MUTED)
        canvas_obj.drawString(1.5 * cm, 1 * cm, _t(lang, "footer_legal"))
        page_num = canvas_obj.getPageNumber()
        canvas_obj.drawRightString(A4[0] - 1.5 * cm, 1 * cm, f"{_t(lang,'page')} {page_num}")
        canvas_obj.restoreState()

    doc.build(story, onFirstPage=_footer, onLaterPages=_footer)
    return buf.getvalue()
