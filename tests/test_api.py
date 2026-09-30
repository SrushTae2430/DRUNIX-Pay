import os
import sys
import unittest
import importlib.util
from starlette.testclient import TestClient

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
server_path = os.path.join(BASE_DIR, 'server.py')
spec = importlib.util.spec_from_file_location('server', server_path)
server_mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(server_mod)

class TestDrunixPayAPI(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        server_mod.init_db(reset=True)
        cls.client = TestClient(server_mod.app)

    def setUp(self):
        server_mod.init_db(reset=True)

    def test_01_connectivity_lifecycle(self):
        # Initial ONLINE
        r = self.client.get('/connectivity/status')
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()['state'], 'ONLINE')

        # Switch to LIMITED
        r_lim = self.client.post('/connectivity/set', json={'state': 'LIMITED', 'latency_ms': 780, 'packet_loss_pct': 34})
        self.assertEqual(r_lim.status_code, 200)
        self.assertEqual(r_lim.json()['state'], 'LIMITED')
        self.assertEqual(r_lim.json()['latency_ms'], 780)
        self.assertEqual(r_lim.json()['packet_loss_pct'], 34)

        # Switch to OFFLINE
        r_off = self.client.post('/connectivity/set', json={'state': 'OFFLINE'})
        self.assertEqual(r_off.status_code, 200)
        self.assertEqual(r_off.json()['state'], 'OFFLINE')

        # Restore to ONLINE
        r_on = self.client.post('/connectivity/set', json={'state': 'ONLINE'})
        self.assertEqual(r_on.status_code, 200)
        self.assertEqual(r_on.json()['state'], 'ONLINE')
        self.assertTrue(r_on.json()['auto_sync_triggered'])

    def test_02_merchant_dashboard(self):
        r = self.client.get('/merchant/dashboard?merchant_id=merch_sharma_01')
        self.assertEqual(r.status_code, 200)
        data = r.json()
        self.assertEqual(data['merchant_name'], 'Sharma General Store')
        self.assertEqual(data['todays_sales'], 24850.0)
        self.assertEqual(data['offline_sales'], 8450.0)
        self.assertTrue(len(data['transactions']) > 0)

    def test_03_risk_evaluation_tiers(self):
        # 1. Normal ₹450 to verified merchant -> LOW RISK
        r_low = self.client.post('/risk/evaluate', json={
            'merchant_id': 'merch_sharma_01',
            'amount': 450.0,
            'customer_id': 'cust_priya_01',
            'is_offline': True
        })
        self.assertEqual(r_low.status_code, 200)
        self.assertTrue(r_low.json()['allowed'])
        self.assertEqual(r_low.json()['risk_level'], 'LOW RISK')

        # 2. Exceeds ₹5,000 max offline cap -> HIGH RISK / Blocked
        r_high = self.client.post('/risk/evaluate', json={
            'merchant_id': 'merch_sharma_01',
            'amount': 5500.0,
            'customer_id': 'cust_priya_01',
            'is_offline': True
        })
        self.assertEqual(r_high.status_code, 200)
        self.assertFalse(r_high.json()['allowed'])
        self.assertEqual(r_high.json()['risk_level'], 'HIGH RISK')

        # 3. Insufficient Balance (> ₹1,850)
        r_bal = self.client.post('/risk/evaluate', json={
            'merchant_id': 'merch_sharma_01',
            'amount': 2500.0,
            'customer_id': 'cust_priya_01',
            'is_offline': True
        })
        self.assertEqual(r_bal.status_code, 200)
        self.assertFalse(r_bal.json()['allowed'])

    def test_04_offline_payment_and_duplicate_prevention(self):
        # Set offline
        self.client.post('/connectivity/set', json={'state': 'OFFLINE'})

        # First Payment: ₹450 to Sharma General Store
        r1 = self.client.post('/payment/offline', json={
            'merchant_id': 'merch_sharma_01',
            'customer_id': 'cust_priya_01',
            'amount': 450.0
        })
        self.assertEqual(r1.status_code, 200)
        d1 = r1.json()
        self.assertEqual(d1['transaction_id'], 'DRX-2026-001284')
        self.assertEqual(d1['status'], 'WAITING_FOR_SYNC')
        self.assertEqual(d1['available_offline_balance'], 1400.0) # 1850 - 450
        self.assertIsNotNone(d1['integrity_hash'])

        # Immediate Second Attempt (Duplicate!): Same merchant, same amount
        r2 = self.client.post('/payment/offline', json={
            'merchant_id': 'merch_sharma_01',
            'customer_id': 'cust_priya_01',
            'amount': 450.0
        })
        self.assertEqual(r2.status_code, 409)
        d2 = r2.json()
        self.assertEqual(d2['error'], 'POSSIBLE_DUPLICATE_PAYMENT')
        self.assertEqual(d2['existing_transaction']['txn_id'], 'DRX-2026-001284')

        # Force bypass duplicate check
        r3 = self.client.post('/payment/offline', json={
            'merchant_id': 'merch_sharma_01',
            'customer_id': 'cust_priya_01',
            'amount': 450.0,
            'bypass_duplicate_check': True
        })
        self.assertEqual(r3.status_code, 200)
        self.assertEqual(r3.json()['status'], 'WAITING_FOR_SYNC')

    def test_05_vault_records_and_integrity_check(self):
        r = self.client.get('/vault/records')
        self.assertEqual(r.status_code, 200)
        d = r.json()
        self.assertEqual(d['vault_title'], 'LOCAL TRANSACTION VAULT')
        self.assertTrue(d['encrypted_records_count'] > 0)
        self.assertEqual(d['integrity_check'], '✓ PASS')

    def test_06_sync_and_reconciliation_flow(self):
        # Trigger Sync
        r_sync = self.client.post('/sync')
        self.assertEqual(r_sync.status_code, 200)
        d_sync = r_sync.json()
        self.assertTrue(d_sync['successful'] > 0)

        # Trigger Reconcile
        r_rec = self.client.post('/reconcile')
        self.assertEqual(r_rec.status_code, 200)
        d_rec = r_rec.json()
        self.assertEqual(d_rec['status'], 'RECONCILIATION_RUN_COMPLETE')
        self.assertTrue(d_rec['summary']['MATCH'] > 0)

    def test_07_demo_control_actions(self):
        actions = [
            'internet_loss',
            'internet_restore',
            'simulate_duplicate',
            'simulate_sync_failure',
            'simulate_timeout',
            'simulate_hash_mismatch',
            'simulate_successful_reconcile',
            'reset_demo'
        ]
        for act in actions:
            r = self.client.post('/demo/action', json={'action': act})
            self.assertEqual(r.status_code, 200, f'Action {act} failed')

    def test_08_observability_metrics(self):
        r = self.client.get('/metrics/observability')
        self.assertEqual(r.status_code, 200)
        d = r.json()
        self.assertEqual(d['metrics']['offline_continuity_rate'], '98%')
        self.assertEqual(d['metrics']['duplicate_prevention_rate'], '94%')
        self.assertEqual(d['metrics']['automatic_reconciliation_rate'], '97%')
        self.assertIn('Prototype simulation metrics', d['disclaimer'])

if __name__ == '__main__':
    unittest.main()
