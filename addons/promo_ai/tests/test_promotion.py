# -*- coding: utf-8 -*-
from odoo.tests.common import TransactionCase, tagged
from odoo.exceptions import ValidationError


@tagged('promotion')
class TestPromoAiPromotion(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Promotion = cls.env['promo_ai.promotion']
        cls.Material = cls.env['promo_ai.material']
        cls.mat_modem = cls.Material.create({'designation': 'Modem', 'price': 100.00, 'active': True})
        cls.mat_stb = cls.Material.create({'designation': 'STB', 'price': 200.00, 'active': True})
        cls.env.flush_all()

    def test_create_percentage_promotion(self):
        promo = self.Promotion.create({
            'name': 'Test -10%',
            'promo_type': 'percentage',
            'value': 10.0,
            'target_type': 'all',
        })
        self.assertEqual(promo.discount_label, '-10.0%')

    def test_create_fixed_promotion(self):
        promo = self.Promotion.create({
            'name': 'Test -20€',
            'promo_type': 'fixed_amount',
            'value': 20.0,
            'target_type': 'all',
        })
        self.assertEqual(promo.discount_label, '-20.0€')

    def test_material_required_when_target_type_material(self):
        with self.assertRaises(ValidationError):
            self.Promotion.create({
                'name': 'Bad',
                'promo_type': 'percentage',
                'value': 10.0,
                'target_type': 'material',
            })

    def test_coupon_code_required_when_target_type_coupon(self):
        with self.assertRaises(ValidationError):
            self.Promotion.create({
                'name': 'Bad Coupon',
                'promo_type': 'fixed_amount',
                'value': 5.0,
                'target_type': 'coupon',
            })

    def test_negative_value_raises(self):
        with self.assertRaises(ValidationError):
            self.Promotion.create({
                'name': 'Negative',
                'promo_type': 'percentage',
                'value': -5.0,
                'target_type': 'all',
            })

    def test_percentage_over_100_raises(self):
        with self.assertRaises(ValidationError):
            self.Promotion.create({
                'name': 'Too Much',
                'promo_type': 'percentage',
                'value': 150.0,
                'target_type': 'all',
            })

    def test_end_before_start_raises(self):
        with self.assertRaises(ValidationError):
            self.Promotion.create({
                'name': 'Bad Dates',
                'promo_type': 'percentage',
                'value': 10.0,
                'target_type': 'all',
                'starts_at': '2025-12-31 00:00:00',
                'ends_at': '2025-01-01 00:00:00',
            })

    def test_state_active(self):
        promo = self.Promotion.create({
            'name': 'Active Promo',
            'promo_type': 'percentage',
            'value': 5.0,
            'target_type': 'all',
            'active': True,
        })
        self.assertEqual(promo.state, 'active')

    def test_state_disabled(self):
        promo = self.Promotion.create({
            'name': 'Disabled Promo',
            'promo_type': 'percentage',
            'value': 5.0,
            'target_type': 'all',
            'active': False,
        })
        self.assertEqual(promo.state, 'disabled')

    def test_state_scheduled(self):
        promo = self.Promotion.create({
            'name': 'Future Promo',
            'promo_type': 'percentage',
            'value': 5.0,
            'target_type': 'all',
            'active': True,
            'starts_at': '2099-01-01 00:00:00',
        })
        self.assertEqual(promo.state, 'scheduled')

    def test_state_expired(self):
        promo = self.Promotion.create({
            'name': 'Expired Promo',
            'promo_type': 'percentage',
            'value': 5.0,
            'target_type': 'all',
            'active': True,
            'ends_at': '2020-01-01 00:00:00',
        })
        self.assertEqual(promo.state, 'expired')

    def test_compute_percentage_discount(self):
        promo = self.Promotion.create({
            'name': 'Perc',
            'promo_type': 'percentage',
            'value': 15.0,
            'target_type': 'all',
        })
        disc_amt, disc_pct, final = promo.compute_discount(100.0)
        self.assertAlmostEqual(disc_amt, 15.0, places=2)
        self.assertAlmostEqual(disc_pct, 15.0, places=2)
        self.assertAlmostEqual(final, 85.0, places=2)

    def test_compute_fixed_discount(self):
        promo = self.Promotion.create({
            'name': 'Fixed',
            'promo_type': 'fixed_amount',
            'value': 20.0,
            'target_type': 'all',
        })
        disc_amt, _, final = promo.compute_discount(100.0)
        self.assertAlmostEqual(disc_amt, 20.0, places=2)
        self.assertAlmostEqual(final, 80.0, places=2)

    def test_fixed_discount_cannot_exceed_price(self):
        promo = self.Promotion.create({
            'name': 'Capped',
            'promo_type': 'fixed_amount',
            'value': 200.0,
            'target_type': 'all',
        })
        disc_amt, _, final = promo.compute_discount(50.0)
        self.assertAlmostEqual(disc_amt, 50.0, places=2)
        self.assertAlmostEqual(final, 0.0, places=2)

    def test_material_specific_beats_global(self):
        self.Promotion.create({
            'name': 'Global Low', 'promo_type': 'percentage',
            'value': 5.0, 'target_type': 'all', 'priority': 0,
        })
        mat_promo = self.Promotion.create({
            'name': 'Mat High', 'promo_type': 'percentage',
            'value': 20.0, 'target_type': 'material',
            'material_id': self.mat_modem.id, 'priority': 10,
        })
        result = self.Promotion.find_applicable_promotions(self.mat_modem)
        self.assertEqual(result, mat_promo)

    def test_global_applies_when_no_material_promo(self):
        self.Promotion.create({
            'name': 'Global Only', 'promo_type': 'percentage',
            'value': 8.0, 'target_type': 'all', 'priority': 0,
        })
        result = self.Promotion.find_applicable_promotions(self.mat_stb)
        self.assertTrue(result)

    def test_coupon_applies_with_code(self):
        self.Promotion.create({
            'name': 'Coupon Test',
            'promo_type': 'fixed_amount',
            'value': 10.0,
            'target_type': 'coupon',
            'code': 'TESTCODE',
            'material_id': self.mat_modem.id,
            'active': True,
        })
        self.env.flush_all()

        result = self.Promotion.find_applicable_promotions(
            self.mat_modem, coupon_code='TESTCODE'
        )
        self.assertTrue(result, "La promo devrait être trouvée")
        self.assertEqual(result.code, 'TESTCODE')

    def test_no_promo_returns_empty(self):
        mat_alone = self.Material.create({'designation': 'AloneNoPromo', 'price': 50.00})
        all_active = self.Promotion.search([('active', '=', True)])
        all_active.write({'active': False})
        result = self.Promotion.find_applicable_promotions(mat_alone)
        all_active.write({'active': True})
        self.assertFalse(result)
