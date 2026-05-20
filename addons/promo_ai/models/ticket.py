# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import ValidationError


class PromoAiTicket(models.Model):
    _name = 'promo_ai.ticket'
    _description = 'Ticket'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'titre'
    _order = 'id desc'

    titre = fields.Char(
        string='Title',
        required=True,
        tracking=True,
    )
    description = fields.Text(
        string='Description',
        tracking=True,
    )
    sale_id = fields.Many2one(
        'promo_ai.sale',
        string='Sale',
        required=True,
        ondelete='cascade',
        index=True,
        tracking=True,
    )
    customer_id = fields.Many2one(
        related='sale_id.customer_id',
        string='Customer',
        store=True,
        readonly=True,
    )
    state = fields.Selection(
        selection=[
            ('new', 'New'),
            ('in_progress', 'In Progress'),
            ('resolved', 'Resolved'),
            ('closed', 'Closed'),
        ],
        string='Status',
        default='new',
        tracking=True,
    )
    priority = fields.Selection(
        selection=[
            ('0', 'Normal'),
            ('1', 'Important'),
            ('2', 'Very Urgent'),
            ('3', 'Critical'),
        ],
        string='Priority',
        default='0',
    )

    def action_in_progress(self):
        self.state = 'in_progress'

    def action_resolve(self):
        self.state = 'resolved'

    def action_close(self):
        self.state = 'closed'

    def action_reset(self):
        self.state = 'new'
