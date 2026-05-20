# -*- coding: utf-8 -*-

import json
from odoo.tests.common import HttpCase


class TestPromoAiControllers(HttpCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.mat = cls.env['promo_ai.material'].create({
            'designation': 'Ctrl Material', 'price': 55.00,
        })
        cls.promo = cls.env['promo_ai.promotion'].create({
            'name': 'Ctrl Promo', 'promo_type': 'fixed_amount',
            'value': 10.0, 'target_type': 'coupon', 'code': 'CTRLTEST',
        })
        cls.customer = cls.env['promo_ai.customer'].create({
            'surnom': 'ctrlcust',
            'user_id': cls.env.ref('base.user_admin').id,
        })
        cls.sale = cls.env['promo_ai.sale'].create({
            'titre': 'Ctrl Sale',
            'customer_id': cls.customer.id,
            'line_ids': [(0, 0, {'material_id': cls.mat.id})],
        })

    def _auth(self):
        self.authenticate('admin', 'admin')

    def test_materials_list_requires_auth(self):
        resp = self.url_open('/promo_ai/materials')
        self.assertIn(resp.status_code, [200, 302, 303])
        self.assertIn('/web/login', resp.url)

    def test_materials_list_authenticated(self):
        self._auth()
        resp = self.url_open('/promo_ai/materials')
        self.assertEqual(resp.status_code, 200)
        data = json.loads(resp.text)
        self.assertIn('data', data)
        self.assertIsInstance(data['data'], list)
        self.assertGreater(data['count'], 0)

    def test_material_get_by_id(self):
        self._auth()
        resp = self.url_open(f'/promo_ai/materials/{self.mat.id}')
        self.assertEqual(resp.status_code, 200)
        data = json.loads(resp.text)
        self.assertEqual(data['id'], self.mat.id)
        self.assertEqual(data['designation'], 'Ctrl Material')

    def test_material_not_found(self):
        self._auth()
        resp = self.url_open('/promo_ai/materials/999999')
        self.assertEqual(resp.status_code, 404)

    def test_sales_list(self):
        self._auth()
        resp = self.url_open('/promo_ai/sales')
        self.assertEqual(resp.status_code, 200)
        data = json.loads(resp.text)
        self.assertIn('data', data)
        self.assertGreater(data['count'], 0)

    def test_sale_detail(self):
        self._auth()
        resp = self.url_open(f'/promo_ai/sales/{self.sale.id}')
        self.assertEqual(resp.status_code, 200)
        data = json.loads(resp.text)
        self.assertEqual(data['titre'], 'Ctrl Sale')
        self.assertIn('lines', data)
        self.assertIn('tickets', data)

    def test_sale_not_found(self):
        self._auth()
        resp = self.url_open('/promo_ai/sales/999999')
        self.assertEqual(resp.status_code, 404)

    def test_promotions_list(self):
        self._auth()
        resp = self.url_open('/promo_ai/promotions')
        self.assertEqual(resp.status_code, 200)
        data = json.loads(resp.text)
        self.assertIn('data', data)

    def test_valid_coupon(self):
        self._auth()
        resp = self.url_open('/promo_ai/promotions/validate/CTRLTEST')
        self.assertEqual(resp.status_code, 200)
        data = json.loads(resp.text)
        self.assertTrue(data['valid'])
        self.assertEqual(data['promo_id'], self.promo.id)

    def test_invalid_coupon(self):
        self._auth()
        resp = self.url_open('/promo_ai/promotions/validate/BADCODE')
        self.assertEqual(resp.status_code, 200)
        data = json.loads(resp.text)
        self.assertFalse(data['valid'])

    def test_dashboard_stats(self):
        self._auth()
        resp = self.url_open('/promo_ai/dashboard/stats')
        self.assertEqual(resp.status_code, 200)
        data = json.loads(resp.text)
        self.assertIn('sales', data)
        self.assertIn('materials', data)
        self.assertIn('customers', data)
        self.assertIn('tickets', data)
        self.assertIn('promotions', data)
        self.assertIsInstance(data['sales']['total'], int)
        self.assertIsInstance(data['sales']['total_revenue'], (int, float))
