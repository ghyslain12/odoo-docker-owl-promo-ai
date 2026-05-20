# -*- coding: utf-8 -*-
from odoo.tests.common import TransactionCase, tagged


@tagged('ticket')
class TestPromoAiTicket(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Ticket = cls.env['promo_ai.ticket']
        cls.env['promo_ai.material'].create({'designation': 'M', 'price': 10.00})
        cust = cls.env['promo_ai.customer'].create({
            'surnom': 'ticketcust',
            'user_id': cls.env.ref('base.user_admin').id,
        })
        cls.sale = cls.env['promo_ai.sale'].create({
            'titre': 'Ticket Sale',
            'customer_id': cust.id,
        })

    def _make_ticket(self, titre='Issue #1', state='new'):
        return self.Ticket.create({
            'titre': titre,
            'sale_id': self.sale.id,
            'state': state,
        })

    def test_create_ticket(self):
        t = self._make_ticket()
        self.assertEqual(t.state, 'new')
        self.assertEqual(t.sale_id, self.sale)

    def test_customer_from_sale(self):
        t = self._make_ticket()
        self.assertEqual(t.customer_id, self.sale.customer_id)

    def test_state_transitions(self):
        t = self._make_ticket()
        t.action_in_progress()
        self.assertEqual(t.state, 'in_progress')
        t.action_resolve()
        self.assertEqual(t.state, 'resolved')
        t.action_close()
        self.assertEqual(t.state, 'closed')
        t.action_reset()
        self.assertEqual(t.state, 'new')

    def test_delete_ticket(self):
        t = self._make_ticket()
        t_id = t.id
        t.unlink()
        self.assertFalse(self.Ticket.browse(t_id).exists())

    def test_cascade_delete_with_sale(self):
        sale2_cust = self.env['promo_ai.customer'].create({
            'surnom': 'cascadetest',
            'user_id': self.env.ref('base.user_admin').id,
        })
        sale2 = self.env['promo_ai.sale'].create({
            'titre': 'Cascade Sale',
            'customer_id': sale2_cust.id,
        })
        t = self.Ticket.create({'titre': 'Cascade Ticket', 'sale_id': sale2.id})
        t_id = t.id
        sale2.unlink()
        self.assertFalse(self.Ticket.browse(t_id).exists())

    def test_priority_field(self):
        t = self._make_ticket()
        t.priority = '3'
        self.assertEqual(t.priority, '3')
