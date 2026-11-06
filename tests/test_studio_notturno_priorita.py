"""Regressioni senza rete: perimetro lavorato, ordine, provenienza e fallimenti."""

import datetime
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from scripts import studio_priorita as p, studio_notturno as s

OGGI = datetime.date(2026, 11, 6)


class PrioritaTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        (self.root / 'studio').mkdir()
        (self.root / 'output/task_output').mkdir(parents=True)
        (self.root / 'output/morning_brief').mkdir()
        self.config = {'modalita': 'solo_temi_lavorati', 'temi': []}
        self.registro = []
        for indice, priorita in enumerate(['MEDIA', 'ALTA', 'MEDIA', 'MEDIA', 'ALTA', 'BASSA']):
            task_id = f'RESEARCH-TOPIC-{indice:03d}'
            file = f'output/task_output/{task_id}.md'
            self.registro.append(f'## {priorita} PRIORITÀ\n### [DONE 2026-06-20 UTC] {task_id} — Dossier {indice}\n**Output atteso:** `{file}`\n')
            (self.root / file).write_text(f'# Dossier {indice}\nContenuto storico, non una fonte verificata.')
            self.config['temi'].append({'indice': indice, 'task_completati': [task_id], 'ambito': f'Ambito studiato {indice}'})
        self.scrivi()

    def scrivi(self):
        (self.root / 'studio/temi_lavorati.json').write_text(json.dumps(self.config))
        (self.root / 'TASK_AUTONOMI.md').write_text('\n'.join(self.registro))

    def seleziona(self, oggi=OGGI):
        return p.seleziona_temi(s.TEMI, oggi, self.root)

    def test_priorita_documentata_non_giorno_settimana(self):
        selezioni = self.seleziona()
        self.assertEqual([t['indice'] for t in selezioni], [1, 4, 0])
        self.assertEqual([t['punteggio'] for t in selezioni], [900, 900, 800])
        self.assertIn('priorità ALTA in TASK_AUTONOMI.md', selezioni[0]['motivo'])

    def test_ricomparsa_dopo_un_rinnovo_lascia_spazio_ai_temi_trascurati(self):
        testo = p.descrivi_selezione(self.seleziona(), s.TEMI, OGGI)
        (self.root / 'output/morning_brief/2026-11-06.md').write_text(testo)
        self.assertEqual([t['indice'] for t in self.seleziona(OGGI + datetime.timedelta(days=1))], [2, 3, 5])
        self.assertEqual([t['indice'] for t in self.seleziona()], [1, 4, 0])

    def test_non_confonde_un_vecchio_brief_con_un_rinnovo(self):
        (self.root / 'output/morning_brief/2026-11-05.md').write_text('# Un titolo su SkyRights')
        self.assertEqual([t['indice'] for t in self.seleziona()], [1, 4, 0])

    def test_metadata_malformati_futuri_o_data_differente_ignorati(self):
        for contenuto in ('non json', '{"data":"2026-11-04","temi":[1,4]}', 'null'):
            (self.root / 'output/morning_brief/2026-11-05.md').write_text(p.MARKER + contenuto + ' -->\n')
            self.assertEqual([t['indice'] for t in self.seleziona()], [1, 4, 0])
        (self.root / 'output/morning_brief/2026-11-07.md').write_text(p.MARKER + '{"data":"2026-11-07","temi":[1,4]}' + ' -->\n')
        self.assertEqual([t['indice'] for t in self.seleziona()], [1, 4, 0])

    def test_file_assente_o_vuoto_non_ammette_un_tema(self):
        (self.root / 'output/task_output/RESEARCH-TOPIC-001.md').unlink()
        (self.root / 'output/task_output/RESEARCH-TOPIC-004.md').write_text('  ')
        self.assertEqual([t['indice'] for t in self.seleziona()], [0, 2, 3])

    def test_un_dossier_corrotto_non_blocca_gli_altri(self):
        self.registro[1] = self.registro[1].replace('2026-06-20', '2026-02-30')
        (self.root / 'output/task_output/RESEARCH-TOPIC-004.md').write_bytes(b'\xff\xfe')
        self.scrivi()
        self.assertEqual([t['indice'] for t in self.seleziona()], [0, 2, 3])

    def test_un_dossier_futuro_non_e_lavoro_gia_svolto(self):
        self.registro[1] = self.registro[1].replace('2026-06-20', '2026-12-01')
        self.scrivi()
        self.assertEqual([t['indice'] for t in self.seleziona()], [4, 0, 2])

    def test_pending_non_e_evidenza_di_lavoro_completato(self):
        self.registro = [b.replace('DONE 2026-06-20 UTC', 'PENDING') for b in self.registro]
        self.scrivi()
        with self.assertRaisesRegex(RuntimeError, 'Nessun tema già lavorato'):
            self.seleziona()

    def test_nessun_fallback_nuovo_tema_senza_dossier(self):
        self.config['temi'] = []
        self.scrivi()
        with self.assertRaises(RuntimeError):
            self.seleziona()

    def test_wildcard_duplicati_o_indice_non_intero_rifiutati(self):
        for indice in (6, 0, False, '2'):
            self.config['temi'][-1]['indice'] = indice
            self.scrivi()
            with self.subTest(indice=indice), self.assertRaises(ValueError):
                self.seleziona()

    def test_file_fuori_archivio_e_symlink_non_ammettono_temi(self):
        self.registro[1] = self.registro[1].replace('output/task_output/RESEARCH-TOPIC-001.md', '../privato.md')
        target = self.root / 'output/task_output/RESEARCH-TOPIC-004.md'
        target.unlink()
        (self.root / 'fuori.md').write_text('non è un dossier')
        target.symlink_to(self.root / 'fuori.md')
        self.scrivi()
        self.assertEqual([t['indice'] for t in self.seleziona()], [0, 2, 3])

    def test_hash_link_data_e_testo_storico_troncato(self):
        contenuto = 'Storico\n' * 1000
        file = self.root / 'output/task_output/RESEARCH-TOPIC-001.md'
        file.write_text(contenuto)
        selezioni = self.seleziona()
        dossier = selezioni[0]['dossier'][0]
        self.assertEqual(dossier['sha256'], hashlib.sha256(contenuto.encode()).hexdigest())
        self.assertEqual(len(dossier['testo']), 6000)
        self.assertTrue(dossier['troncato'])
        self.assertEqual(file.read_text(), contenuto)
        testo = p.descrivi_selezione(selezioni, s.TEMI, OGGI)
        self.assertIn('../task_output/RESEARCH-TOPIC-001.md', testo)
        self.assertIn('2026-06-20', testo)
        self.assertIn('non una valutazione di urgenze in tempo reale', testo)

    def test_task_pending_solo_con_associazione_esplicita(self):
        self.registro.append('## ALTA PRIORITÀ\n### [PENDING] NEW-001 — Nuovo lavoro\nParola Avatar\n')
        self.scrivi()
        self.assertEqual([t['indice'] for t in self.seleziona()], [1, 4, 0])
        self.registro[-1] += '**Tema studio:** 5\n'
        self.scrivi()
        self.assertEqual(self.seleziona()[0]['indice'], 5)
        self.assertIn('NEW-001', self.seleziona()[0]['motivo'])

    def test_selezione_esplicitamente_vuota_non_avvia_il_provider(self):
        with patch.object(s, 'genera_brief') as genera:
            with self.assertRaisesRegex(RuntimeError, 'Nessun tema'):
                s.genera_brief_parallelo(None, [])
            genera.assert_not_called()

    def test_generazione_riceve_solo_ambiti_e_dossier_selezionati(self):
        selezioni = self.seleziona()
        with patch.object(s, 'genera_brief', return_value='Fixture') as genera:
            testo = s.genera_brief_parallelo(None, selezioni)
        self.assertEqual(genera.call_count, 3)
        for chiamata, scelta in zip(genera.call_args_list, selezioni):
            tema = chiamata.args[0]
            self.assertEqual(tema['focus'], scelta['ambito'])
            self.assertEqual(tema['dossier'], scelta['dossier'])
            self.assertNotIn('Starlink', str(tema['domande']))
        self.assertNotIn('Connessioni Globali', testo)
        self.assertNotIn('anticipazione domani', testo)

    def test_config_del_repository_copre_solo_dossier_esistenti(self):
        selezioni = p.seleziona_temi(s.TEMI, OGGI)
        self.assertEqual([t['indice'] for t in selezioni], [1, 4, 0])
        self.assertEqual([d['id'] for d in selezioni[1]['dossier']], ['ASBL-001', 'EU-FUNDING-004'])


if __name__ == '__main__':
    unittest.main()
