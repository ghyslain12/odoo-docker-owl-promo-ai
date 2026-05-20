# -*- coding: utf-8 -*-
from odoo.tests.common import TransactionCase, tagged
from odoo.exceptions import ValidationError


@tagged('customer')
class TestPromoAiCustomer(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Customer = cls.env['promo_ai.customer']
        cls.admin_user = cls.env.ref('base.user_admin')

    def _make_customer(self, surnom='testuser'):
        return self.Customer.create({
            'surnom': surnom,
            'user_id': self.admin_user.id,
        })

    def test_create_customer(self):
        c = self._make_customer('jdoe')
        self.assertEqual(c.surnom, 'jdoe')
        self.assertEqual(c.user_id, self.admin_user)

    def test_surnom_unique(self):
        self._make_customer('unique_val')
        with self.assertRaises(ValidationError):
            self._make_customer('unique_val')

    def test_sale_count_empty(self):
        c = self._make_customer('nocust')
        self.assertEqual(c.sale_count, 0)

    def test_sale_count_increments(self):
        c = self._make_customer('salecust')
        self.env['promo_ai.sale'].create({
            'titre': 'Vente Test',
            'customer_id': c.id,
        })
        c.invalidate_recordset(['sale_count'])
        self.assertEqual(c.sale_count, 1)

    def test_delete_customer(self):
        c = self._make_customer('deleteme')
        c_id = c.id
        c.unlink()
        self.assertFalse(self.Customer.browse(c_id).exists())
