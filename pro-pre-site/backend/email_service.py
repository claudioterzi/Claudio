"""Email service for Pro-pre using Resend.
Multi-language templates for booking confirmations, admin notifications, and magic link auth.
"""
from __future__ import annotations

import asyncio
import logging
import os
from typing import Optional

import resend

logger = logging.getLogger(__name__)

FROM_EMAIL = os.environ.get("RESEND_FROM_EMAIL", "onboarding@resend.dev")
ADMIN_EMAIL = "Terziclaudio@gmail.com"


def _init():
    api_key = os.environ.get("RESEND_API_KEY")
    if not api_key:
        raise RuntimeError("RESEND_API_KEY missing")
    resend.api_key = api_key


# --- Template rendering ---

BASE_STYLES = """
  <style>
    body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; background:#F8FAFC; margin:0; padding:0; color:#1B2845; }
    .wrap { max-width: 600px; margin: 0 auto; padding: 24px; background:#fff; }
    .kicker { color:#5BA4D4; font-size:11px; letter-spacing:0.15em; text-transform:uppercase; font-weight:700; }
    h1 { color:#1B2845; font-size:24px; margin: 8px 0 16px; }
    p  { line-height: 1.55; font-size:15px; margin: 0 0 12px; color:#334155; }
    .btn { display:inline-block; background:#1B2845; color:#fff !important; padding:12px 22px; border-radius:10px; text-decoration:none; font-weight:600; }
    .info { background:#F1F5F9; padding:16px 18px; border-radius:12px; margin: 12px 0; }
    .info b { color:#1B2845; }
    .footer { color:#64748B; font-size:12px; margin-top:24px; border-top:1px solid #E2E8F0; padding-top:16px; }
    .divider { height:1px; background:#E2E8F0; margin: 20px 0; }
  </style>
"""

I18N = {
    "fr": {
        "hello": "Bonjour",
        "sig": "L'équipe Pro-pre",
        "contract_subject": "Votre contrat Défi de la Bande — Pro-pre",
        "contract_intro": "Merci d'avoir accepté le Défi de la Bande. Nous avons enregistré votre demande de test gratuit et généré votre contrat.",
        "your_appointment": "Votre rendez-vous",
        "date": "Date",
        "time": "Créneau",
        "address": "Adresse",
        "download_pdf": "Télécharger le contrat PDF",
        "access_space": "Accéder à mon espace client",
        "help_line": "Une question ? Répondez à cet email ou WhatsApp au +33 6 74 93 20 00.",
        "magic_subject": "Votre lien d'accès Pro-pre",
        "magic_intro": "Cliquez sur le bouton ci-dessous pour accéder à votre espace personnel et retrouver vos contrats.",
        "magic_btn": "Ouvrir mon espace",
        "magic_expiry": "Ce lien expire dans 15 minutes.",
        "magic_ignore": "Si vous n'avez pas demandé ce lien, ignorez cet email.",
        "admin_subject": "🆕 Nouveau contrat Défi de la Bande",
        "admin_intro": "Nouveau contrat signé par un client. Détails ci-dessous.",
        "client": "Client",
        "service": "Service",
        "price": "Prix estimé",
        "deposit": "Acompte",
        "open_admin": "Ouvrir le tableau de bord admin",
    },
    "en": {
        "hello": "Hello",
        "sig": "The Pro-pre team",
        "contract_subject": "Your Band Challenge contract — Pro-pre",
        "contract_intro": "Thanks for accepting The Band Challenge. We have recorded your free trial request and generated your contract.",
        "your_appointment": "Your appointment",
        "date": "Date",
        "time": "Time slot",
        "address": "Address",
        "download_pdf": "Download PDF contract",
        "access_space": "Access my client space",
        "help_line": "Any question? Reply to this email or WhatsApp +33 6 74 93 20 00.",
        "magic_subject": "Your Pro-pre access link",
        "magic_intro": "Click the button below to access your personal space and review your contracts.",
        "magic_btn": "Open my space",
        "magic_expiry": "This link expires in 15 minutes.",
        "magic_ignore": "If you didn't request this link, please ignore this email.",
        "admin_subject": "🆕 New Band Challenge contract",
        "admin_intro": "A client just signed a new contract. Details below.",
        "client": "Client",
        "service": "Service",
        "price": "Estimated price",
        "deposit": "Deposit",
        "open_admin": "Open admin dashboard",
    },
    "es": {
        "hello": "Hola",
        "sig": "El equipo Pro-pre",
        "contract_subject": "Tu contrato Desafío de la Franja — Pro-pre",
        "contract_intro": "Gracias por aceptar el Desafío de la Franja. Hemos registrado tu solicitud de prueba gratuita y generado tu contrato.",
        "your_appointment": "Tu cita",
        "date": "Fecha",
        "time": "Franja horaria",
        "address": "Dirección",
        "download_pdf": "Descargar contrato PDF",
        "access_space": "Acceder a mi espacio cliente",
        "help_line": "¿Preguntas? Responde a este email o WhatsApp +33 6 74 93 20 00.",
        "magic_subject": "Tu enlace de acceso Pro-pre",
        "magic_intro": "Haz clic en el botón para acceder a tu espacio personal y ver tus contratos.",
        "magic_btn": "Abrir mi espacio",
        "magic_expiry": "Este enlace expira en 15 minutos.",
        "magic_ignore": "Si no has solicitado este enlace, ignora este correo.",
        "admin_subject": "🆕 Nuevo contrato Desafío de la Franja",
        "admin_intro": "Un cliente acaba de firmar un nuevo contrato. Detalles debajo.",
        "client": "Cliente",
        "service": "Servicio",
        "price": "Precio estimado",
        "deposit": "Anticipo",
        "open_admin": "Abrir dashboard admin",
    },
    "nl": {
        "hello": "Hallo",
        "sig": "Het Pro-pre team",
        "contract_subject": "Uw Bandtest contract — Pro-pre",
        "contract_intro": "Bedankt voor het accepteren van De Bandtest. Wij hebben uw gratis proef geregistreerd en uw contract opgesteld.",
        "your_appointment": "Uw afspraak",
        "date": "Datum",
        "time": "Tijdslot",
        "address": "Adres",
        "download_pdf": "PDF-contract downloaden",
        "access_space": "Naar mijn klantomgeving",
        "help_line": "Vragen? Beantwoord deze e-mail of WhatsApp +33 6 74 93 20 00.",
        "magic_subject": "Uw Pro-pre toegangslink",
        "magic_intro": "Klik op de knop hieronder om uw persoonlijke ruimte te openen en uw contracten in te zien.",
        "magic_btn": "Mijn ruimte openen",
        "magic_expiry": "Deze link vervalt over 15 minuten.",
        "magic_ignore": "Heeft u deze link niet aangevraagd? Negeer deze e-mail.",
        "admin_subject": "🆕 Nieuw Bandtest contract",
        "admin_intro": "Een klant heeft zojuist een nieuw contract getekend. Details hieronder.",
        "client": "Klant",
        "service": "Dienst",
        "price": "Geschatte prijs",
        "deposit": "Aanbetaling",
        "open_admin": "Open admin dashboard",
    },
    "it": {
        "hello": "Ciao",
        "sig": "Il team Pro-pre",
        "contract_subject": "Il tuo contratto Sfida della Striscia — Pro-pre",
        "contract_intro": "Grazie per aver accettato la Sfida della Striscia. Abbiamo registrato la tua richiesta di prova gratuita e generato il tuo contratto.",
        "your_appointment": "Il tuo appuntamento",
        "date": "Data",
        "time": "Fascia oraria",
        "address": "Indirizzo",
        "download_pdf": "Scarica contratto PDF",
        "access_space": "Accedi alla mia area cliente",
        "help_line": "Domande? Rispondi a questa email o WhatsApp +33 6 74 93 20 00.",
        "magic_subject": "Il tuo link di accesso Pro-pre",
        "magic_intro": "Clicca sul pulsante qui sotto per accedere alla tua area personale e consultare i tuoi contratti.",
        "magic_btn": "Apri la mia area",
        "magic_expiry": "Questo link scade tra 15 minuti.",
        "magic_ignore": "Se non hai richiesto questo link, ignora questa email.",
        "admin_subject": "🆕 Nuovo contratto Sfida della Striscia",
        "admin_intro": "Un cliente ha appena firmato un nuovo contratto. Dettagli sotto.",
        "client": "Cliente",
        "service": "Servizio",
        "price": "Prezzo stimato",
        "deposit": "Acconto",
        "open_admin": "Apri dashboard admin",
    },
}


def _t(lang: str, key: str) -> str:
    lang = lang if lang in I18N else "fr"
    return I18N[lang].get(key, I18N["fr"].get(key, key))


async def _send_async(to: str, subject: str, html: str) -> Optional[str]:
    """Send email in a thread (Resend SDK is sync). Returns email_id or None on error."""
    try:
        _init()
        params = {"from": FROM_EMAIL, "to": [to], "subject": subject, "html": html}
        result = await asyncio.to_thread(resend.Emails.send, params)
        eid = result.get("id") if isinstance(result, dict) else None
        logger.info(f"[email] sent to={to} subject={subject!r} id={eid}")
        return eid
    except Exception as e:
        logger.error(f"[email] send failed to={to}: {e}")
        return None


# --- Public helpers ---

async def send_contract_confirmation(
    to: str,
    lang: str,
    client_name: str,
    date_str: str,
    time_slot: str,
    address: str,
    contract_pdf_url: str,
    space_url: str,
) -> Optional[str]:
    subject = _t(lang, "contract_subject")
    html = f"""<!DOCTYPE html><html><head><meta charset="utf-8">{BASE_STYLES}</head><body>
      <div class="wrap">
        <div class="kicker">Pro-pre · Nettoyage textile</div>
        <h1>{_t(lang,'hello')} {client_name.split(' ')[0] if client_name else ''} 👋</h1>
        <p>{_t(lang,'contract_intro')}</p>
        <div class="info">
          <b>{_t(lang,'your_appointment')}</b><br>
          {_t(lang,'date')}: <b>{date_str}</b><br>
          {_t(lang,'time')}: <b>{time_slot}</b><br>
          {_t(lang,'address')}: <b>{address}</b>
        </div>
        <p><a class="btn" href="{contract_pdf_url}">{_t(lang,'download_pdf')} →</a></p>
        <div class="divider"></div>
        <p><a href="{space_url}" style="color:#5BA4D4">{_t(lang,'access_space')} →</a></p>
        <div class="footer">
          <p>{_t(lang,'help_line')}</p>
          <p>— {_t(lang,'sig')}</p>
        </div>
      </div>
    </body></html>"""
    return await _send_async(to, subject, html)


async def send_magic_link(to: str, lang: str, magic_url: str) -> Optional[str]:
    subject = _t(lang, "magic_subject")
    html = f"""<!DOCTYPE html><html><head><meta charset="utf-8">{BASE_STYLES}</head><body>
      <div class="wrap">
        <div class="kicker">Pro-pre</div>
        <h1>🔑 {_t(lang,'magic_subject')}</h1>
        <p>{_t(lang,'magic_intro')}</p>
        <p><a class="btn" href="{magic_url}">{_t(lang,'magic_btn')} →</a></p>
        <p style="font-size:13px; color:#64748B">{_t(lang,'magic_expiry')}</p>
        <div class="divider"></div>
        <p style="font-size:12px; color:#94A3B8">{_t(lang,'magic_ignore')}</p>
      </div>
    </body></html>"""
    return await _send_async(to, subject, html)


async def send_generic_email(to: str, subject: str, body_text: str) -> Optional[str]:
    """Simple text-to-HTML wrapper used by admin tools (custom emails, cancel notice, resend link)."""
    safe_body = (body_text or "").replace("<", "&lt;").replace(">", "&gt;").replace("\n", "<br>")
    html = f"""<!DOCTYPE html><html><head><meta charset="utf-8">{BASE_STYLES}</head><body>
      <div class="wrap">
        <div class="kicker">Pro-pre</div>
        <div style="font-size:15px; color:#1B2845; line-height:1.7">{safe_body}</div>
        <div class="divider"></div>
        <div class="footer">
          <p>Claudio — Pro-pre · +33 6 74 93 20 00</p>
        </div>
      </div>
    </body></html>"""
    return await _send_async(to, subject, html)


async def send_contract_pdf_email(contract: dict) -> Optional[str]:
    """Re-send the contract PDF link to the client (used by admin tools)."""
    lang = contract.get("language", "fr")
    to = contract.get("client_email")
    if not to:
        return None
    backend_url = os.environ.get("BACKEND_URL", "").rstrip("/")
    if not backend_url:
        # Derive from FRONTEND_URL by convention
        frontend = os.environ.get("FRONTEND_URL", "https://pro-pre.com").rstrip("/")
        backend_url = frontend
    pdf_url = f"{backend_url}/api/contracts/{contract.get('id')}/pdf"
    space_url = f"{os.environ.get('FRONTEND_URL', 'https://pro-pre.com').rstrip('/')}/mon-espace"
    return await send_contract_confirmation(
        to=to,
        lang=lang,
        client_name=contract.get("client_name", ""),
        date_str=contract.get("date", ""),
        time_slot=contract.get("time_slot", ""),
        address=contract.get("client_address", ""),
        contract_pdf_url=pdf_url,
        space_url=space_url,
    )



async def send_admin_new_contract(
    lang: str,
    client_name: str,
    client_email: str,
    client_phone: str,
    date_str: str,
    time_slot: str,
    service_label: str,
    service_price: float,
    deposit_choice: str,
    admin_url: str,
) -> Optional[str]:
    subject = _t(lang, "admin_subject")
    html = f"""<!DOCTYPE html><html><head><meta charset="utf-8">{BASE_STYLES}</head><body>
      <div class="wrap">
        <div class="kicker">Pro-pre · Admin</div>
        <h1>🆕 {subject}</h1>
        <p>{_t(lang,'admin_intro')}</p>
        <div class="info">
          <b>{_t(lang,'client')}:</b> {client_name} — {client_email} — {client_phone}<br>
          <b>{_t(lang,'date')}:</b> {date_str} · {time_slot}<br>
          <b>{_t(lang,'service')}:</b> {service_label}<br>
          <b>{_t(lang,'price')}:</b> € {service_price:.2f}<br>
          <b>{_t(lang,'deposit')}:</b> {deposit_choice}
        </div>
        <p><a class="btn" href="{admin_url}">{_t(lang,'open_admin')} →</a></p>
      </div>
    </body></html>"""
    return await _send_async(ADMIN_EMAIL, subject, html)
