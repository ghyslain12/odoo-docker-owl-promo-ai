# -*- coding: utf-8 -*-
from odoo.tests.common import TransactionCase, tagged
from odoo.exceptions import UserError


@tagged('sale')
class TestPromoAiSale(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Sale = cls.env['promo_ai.sale']
        cls.SaleLine = cls.env['promo_ai.sale.line']
        cls.Material = cls.env['promo_ai.material']
        cls.Customer = cls.env['promo_ai.customer']
        cls.Promotion = cls.env['promo_ai.promotion']

        cls.Promotion.search([]).write({'active': False})

        cls.mat1 = cls.Material.create({'designation': 'SaleTestM1', 'price': 100.00})
        cls.mat2 = cls.Material.create({'designation': 'SaleTestM2', 'price': 200.00})

        cls.customer = cls.Customer.create({
            'surnom': 'testcust_sale',
            'user_id': cls.env.ref('base.user_admin').id,
        })

    def _make_sale(self, with_lines=True, coupon_code=None):
        vals = {
            'titre': 'Test Sale',
            'customer_id': self.customer.id,
        }
        if coupon_code:
            vals['coupon_code'] = coupon_code

        if with_lines:
            vals['line_ids'] = [
                (0, 0, {'material_id': self.mat1.id}),
                (0, 0, {'material_id': self.mat2.id}),
            ]
        return self.Sale.create(vals)

    def test_create_sale_gets_sequence(self):
        sale = self._make_sale()
        self.assertNotEqual(sale.name, 'New')
        self.assertTrue(sale.name.startswith('SALE-'))

    def test_create_sale_computes_original_prices(self):
        sale = self._make_sale()
        line1 = sale.line_ids.filtered(lambda l: l.material_id.id == self.mat1.id)
        line2 = sale.line_ids.filtered(lambda l: l.material_id.id == self.mat2.id)

        self.assertAlmostEqual(float(line1.original_price), 100.00, places=2)
        self.assertAlmostEqual(float(line2.original_price), 200.00, places=2)

    def test_total_without_promotion(self):
        sale = self._make_sale()
        self.assertAlmostEqual(float(sale.total_amount), 300.00, places=2)
        self.assertAlmostEqual(float(sale.total_discount), 0.00, places=2)

    def test_update_sale_title(self):
        sale = self._make_sale()
        sale.write({'titre': 'Updated Title'})
        self.assertEqual(sale.titre, 'Updated Title')

    def test_delete_sale(self):
        sale = self._make_sale()
        sale_id = sale.id
        sale.unlink()
        self.assertFalse(self.Sale.browse(sale_id).exists())

    def test_global_promo_applied_on_create(self):
        self.Promotion.create({
            'name': 'Global -10%', 'promo_type': 'percentage',
            'value': 10.0, 'target_type': 'all', 'priority': 0,
        })
        mat = self.Material.create({'designation': 'PromoMat', 'price': 100.00})
        sale = self.Sale.create({
            'titre': 'Promo Sale',
            'customer_id': self.customer.id,
            'line_ids': [(0, 0, {'material_id': mat.id})],
        })
        line = sale.line_ids[0]
        self.assertAlmostEqual(float(line.final_price), 90.00, places=2)
        self.assertAlmostEqual(float(line.discount_percentage), 10.0, places=2)

    def test_material_specific_promo_takes_priority(self):
        mat = self.Material.create({'designation': 'SpecificMat', 'price': 100.00})
        self.Promotion.create({
            'name': 'Global -5%', 'promo_type': 'percentage',
            'value': 5.0, 'target_type': 'all', 'priority': 0,
        })
        self.Promotion.create({
            'name': 'Mat -20%', 'promo_type': 'percentage',
            'value': 20.0, 'target_type': 'material',
            'material_id': mat.id, 'priority': 10,
        })
        sale = self.Sale.create({
            'titre': 'Specific Promo Sale',
            'customer_id': self.customer.id,
            'line_ids': [(0, 0, {'material_id': mat.id})],
        })
        line = sale.line_ids[0]
        self.assertAlmostEqual(float(line.final_price), 80.00, places=2)
        self.assertAlmostEqual(float(line.discount_percentage), 20.0, places=2)

    def test_coupon_applied(self):
        self.Promotion.create({
            'name': 'Coupon 15%',
            'promo_type': 'percentage',
            'value': 15.0,
            'target_type': 'coupon',
            'code': 'TESTCODE',
            'active': True,
        })

        self.env.flush_all()

        sale = self._make_sale(coupon_code='TESTCODE')
        sale._apply_promotions()

        line = sale.line_ids[0]
        self.assertAlmostEqual(float(line.final_price), 85.00, places=2)

    def test_invalid_coupon_raises(self):
        sale = self.Sale.create({
            'titre': 'Bad Coupon Sale',
            'customer_id': self.customer.id,
            'coupon_code': 'BADCODE',
        })
        with self.assertRaises(UserError):
            sale.action_apply_coupon()

    def test_apply_coupon_no_code_raises(self):
        sale = self.Sale.create({
            'titre': 'No Code Sale',
            'customer_id': self.customer.id,
        })
        with self.assertRaises(UserError):
            sale.action_apply_coupon()

    def test_total_with_discount(self):
        mat = self.Material.create({'designation': 'TotalMat', 'price': 100.00})
        self.Promotion.create({
            'name': 'Total Promo -25%', 'promo_type': 'percentage',
            'value': 25.0, 'target_type': 'material',
            'material_id': mat.id, 'priority': 5,
        })
        sale = self.Sale.create({
            'titre': 'Total Sale',
            'customer_id': self.customer.id,
            'line_ids': [(0, 0, {'material_id': mat.id})],
        })
        self.assertAlmostEqual(float(sale.total_amount), 75.00, places=2)
        self.assertAlmostEqual(float(sale.total_discount), 25.00, places=2)

    def test_ticket_count(self):
        sale = self._make_sale()
        self.assertEqual(sale.ticket_count, 0)
        self.env['promo_ai.ticket'].create({
            'titre': 'T1', 'sale_id': sale.id,
        })
        sale.invalidate_recordset(['ticket_count'])
        self.assertEqual(sale.ticket_count, 1)

    def test_lines_deleted_with_sale(self):
        sale = self._make_sale()
        line_ids = sale.line_ids.ids
        sale.unlink()
        self.assertFalse(self.SaleLine.browse(line_ids).exists())
