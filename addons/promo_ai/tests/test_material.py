# -*- coding: utf-8 -*-
from odoo.tests.common import TransactionCase, tagged
from odoo.exceptions import ValidationError
from odoo.tools import mute_logger
from psycopg2 import IntegrityError


@tagged('material')
class TestPromoAiMaterial(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Material = cls.env['promo_ai.material']

    def _make_material(self, designation='Modem', price=99.99):
        return self.Material.create({'designation': designation, 'price': price})

    def test_create_material(self):
        mat = self._make_material('Test Router', 49.99)
        self.assertEqual(mat.designation, 'Test Router')
        self.assertAlmostEqual(float(mat.price), 49.99, places=2)

    def test_read_material(self):
        mat = self._make_material('STB', 120.00)
        found = self.Material.browse(mat.id)
        self.assertEqual(found.designation, 'STB')

    def test_update_material(self):
        mat = self._make_material('VoIP', 75.00)
        mat.write({'price': 80.00})
        self.assertAlmostEqual(float(mat.price), 80.00, places=2)

    def test_delete_material(self):
        mat = self._make_material('Delete Me', 10.00)
        mat_id = mat.id
        mat.unlink()
        self.assertFalse(self.Material.browse(mat_id).exists())

    def test_negative_price_raises(self):
        with self.assertRaises(ValidationError):
            self._make_material('Bad Material', -5.00)

    def test_designation_required(self):
        with mute_logger('odoo.sql_db'), self.assertRaises(IntegrityError):
            self.Material.create({'price': 10.00})
            self.env.flush_all()

    def test_sale_count_empty(self):
        mat = self._make_material('Lonely Material', 50.00)
        self.assertEqual(mat.sale_count, 0)

    def test_archive_material(self):
        mat = self._make_material('Archivable', 30.00)
        mat.active = False
        self.assertFalse(mat.active)
        result = self.Material.search([('designation', '=', 'Archivable')])
        self.assertFalse(result)
