"""CUSTODE-001 — Sistema integrale di custodia per case Airbnb.

Due sottosistemi che si coprono a vicenda:
- OCCHIO  (custode.visione + custode.confronto): inventario fotografico
  di precisione a zone, confronto baseline vs check-out.
- SOGLIA  (custode.varco): registro micro-tag RFID UHF e varco d'uscita
  con rilevamento di direzione.

Il report di check-out (custode.report) incrocia le due fonti.
Studio completo: idee/CUSTODE-001_sistema-custode-airbnb.md
"""

from custode.modelli import Zona, ConteggioZona, Inventario, Discrepanza
from custode.visione import ContatoreStub, crea_contatore
from custode.confronto import confronta
from custode.varco import RegistroTag, Varco, EventoVarco, Direzione
from custode.report import ReportCheckout

__version__ = "0.1.0"
