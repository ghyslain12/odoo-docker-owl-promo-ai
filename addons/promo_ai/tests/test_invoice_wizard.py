# -*- coding: utf-8 -*-
from odoo.tests.common import TransactionCase
from odoo.exceptions import UserError


class TestGenerateInvoiceWizard(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Wizard = cls.env['promo_ai.generate.invoice.wizard']
        mat = cls.env['promo_ai.material'].create({'designation': 'InvMat', 'price': 50.00})
        cust = cls.env['promo_ai.customer'].create({
            'surnom': 'invcust',
            'user_id': cls.env.ref('base.user_admin').id,
        })
        cls.sale_with_lines = cls.env['promo_ai.sale'].create({
            'titre': 'Invoice Sale',
            'customer_id': cust.id,
            'line_ids': [(0, 0, {'material_id': mat.id})],
        })
        cls.sale_empty = cls.env['promo_ai.sale'].create({
            'titre': 'Empty Sale',
            'customer_id': cust.id,
        })

    def _make_wizard(self, sale, country='france'):
        return self.Wizard.create({
            'sale_id': sale.id,
            'country': country,
        })

    def test_wizard_sets_invoice_generated(self):
        wizard = self._make_wizard(self.sale_with_lines, 'france')
        wizard.sale_id.write({
            'invoice_country': wizard.country,
            'invoice_generated': True,
        })
        self.assertTrue(self.sale_with_lines.invoice_generated)
        self.assertEqual(self.sale_with_lines.invoice_country, 'france')

    def test_wizard_international(self):
        wizard = self._make_wizard(self.sale_with_lines, 'international')
        wizard.sale_id.write({
            'invoice_country': wizard.country,
            'invoice_generated': True,
        })
        self.assertEqual(self.sale_with_lines.invoice_country, 'international')

    def test_wizard_raises_on_empty_sale(self):
        wizard = self._make_wizard(self.sale_empty, 'france')
        with self.assertRaises(UserError):
            wizard.action_generate()

    def test_wizard_preview_fields(self):
        wizard = self._make_wizard(self.sale_with_lines)
        self.assertEqual(wizard.sale_name, self.sale_with_lines.name)
        self.assertEqual(wizard.customer_name, self.sale_with_lines.customer_id.surnom)
