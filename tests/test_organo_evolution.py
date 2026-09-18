import copy
import json
import tempfile
import unittest
from pathlib import Path
from studio.parfums.organo_evolution import composition_catalog, set_status, admit_material

class EvolutionTests(unittest.TestCase):
    def setUp(self):
        self.catalog={'materie':[{'n':1,'nome':'Storica'}], 'totale_materie':1}
        self.registry={'schema_version':1,'revision':1,'overrides':[], 'events':[],
                       'proposals':[{'id':'EV-X','name':'Nuova','status':'proposed'}]}
    def test_proposal_is_not_inventory_and_suspension_does_not_delete_history(self):
        original=copy.deepcopy(self.catalog)
        self.assertEqual(composition_catalog(self.catalog,self.registry)['materie'],self.catalog['materie'])
        self.registry['overrides']=[{'n':1,'status':'suspended'}]
        self.assertEqual(composition_catalog(self.catalog,self.registry)['materie'],[])
        self.assertEqual(self.catalog,original)
        self.registry['overrides']=[{'n':900,'status':'active'}]
        with self.assertRaises(ValueError):composition_catalog(self.catalog,self.registry)
    def test_lifecycle_records_changes_and_keeps_old_snapshot(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);cp=root/'catalog.json';rp=root/'registry.json'
            cp.write_text(json.dumps(self.catalog));rp.write_text(json.dumps(self.registry));original=cp.read_bytes()
            set_status(1,'suspended','Campione non disponibile',rp,cp)
            self.assertEqual(cp.read_bytes(),original)
            self.assertEqual(json.loads(rp.read_text())['revision'],2)
            set_status(1,'active','Disponibilità ripristinata',rp,cp)
            with self.assertRaises(ValueError):admit_material('EV-X',{},rp,cp,root/'snapshots')
            self.assertEqual(cp.read_bytes(),original)
            evidence=dict(availability_confirmed_by='Claudio',supplier='Fornitore',supplier_product='Prodotto',
                          preparation='10% in etanolo',technical_document='Scheda tecnica identificata',
                          material=dict(nome='Nuova',tipo='SIN',livello='MASTER',forza=3,famiglia='Legni',nota='F'))
            self.assertEqual(admit_material('EV-X',evidence,rp,cp,root/'snapshots'),2)
            snapshots=[p.read_bytes() for p in (root/'snapshots').iterdir()]
            self.assertIn(original,snapshots);self.assertIn(cp.read_bytes(),snapshots)
            self.assertEqual(json.loads(cp.read_text())['materie'][0],self.catalog['materie'][0])
            with self.assertRaises(ValueError):admit_material('EV-X',evidence,rp,cp,root/'snapshots')
