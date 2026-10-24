"""Request-scoped website output for the existing Telegram command engine."""
from contextvars import ContextVar
from html.parser import HTMLParser

_output = ContextVar('agora_output', default=None)


class _Text(HTMLParser):
    def __init__(self, value):
        super().__init__(convert_charrefs=True)
        self.parts = []
        self.feed(value)

    def handle_data(self, value):
        self.parts.append(value)


def cattura(testo):
    value = _output.get()
    if value is None:
        return False
    value['messaggi'].append(''.join(_Text(str(testo)).parts))
    return True


def dato(nome, value):
    current = _output.get()
    if current is not None:
        current['dati'][nome] = value


def esito(state, note):
    current = _output.get()
    if current is not None:
        current['stato'] = state
        current['note'].append(note)


def sul_sito():
    return _output.get() is not None


def esegui(comando):
    from sdq1.notifiche import _esegui_singolo_comando
    value = {'stato': 'completato', 'messaggi': [], 'dati': {}, 'note': []}
    token = _output.set(value)
    try:
        _esegui_singolo_comando(comando.lstrip('/'))
        if not value['messaggi'] or any(m.startswith('❌') for m in value['messaggi']):
            value['stato'] = 'errore'
        # Full votes remain readable; Telegram keeps its compact message format.
        council = value['dati'].get('consiglio')
        if council:
            lines = ['Consiglio SDQ-1', council['questione'], '']
            for vote in council['voti']:
                lines.extend([vote['membro'] + ' · ' + (vote.get('modello') or 'nessun modello'),
                              vote['raccomandazione'], vote['motivazione'], ''])
            lines.extend(['Sintesi: ' + council['sintesi_agenti'],
                          'Decisione: ' + council['decisione_finale']])
            value['testo'] = '\n'.join(lines)
        else:
            value['testo'] = '\n\n'.join(value['messaggi'])
        return value
    finally:
        _output.reset(token)
