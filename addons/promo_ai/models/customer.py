# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import ValidationError


class PromoAiCustomer(models.Model):
    _name = 'promo_ai.customer'
    _description = 'Customer'
    _rec_name = 'surnom'
    _order = 'surnom asc'

    surnom = fields.Char(string='Nickname', required=True, size=255)
    user_id = fields.Many2one('res.users', string='User', required=True, ondelete='cascade')
    sale_ids = fields.One2many('promo_ai.sale', 'customer_id', string='Sales')
    sale_count = fields.Integer(string='Sales Count', compute='_compute_sale_count', store=True)
    total_revenue = fields.Float(string='Total Revenue', compute='_compute_total_revenue', store=True)

    @api.depends('sale_ids')
    def _compute_sale_count(self):
        for rec in self:
            rec.sale_count = len(rec.sale_ids)

    @api.depends('sale_ids', 'sale_ids.total_amount')
    def _compute_total_revenue(self):
        for rec in self:
            rec.total_revenue = sum(rec.sale_ids.mapped('total_amount'))

    @api.constrains('surnom')
    def _check_surnom_unique(self):
        for rec in self:
            if rec.surnom:
                domain = [
                    ('surnom', '=', rec.surnom),
                    ('id', '!=', rec.id),
                ]
                if self.search_count(domain):
                    raise ValidationError(self.env._('Nickname must be unique.'))

    def action_view_sales(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Sales',
            'res_model': 'promo_ai.sale',
            'view_mode': 'list,form',
            'domain': [('customer_id', '=', self.id)],
        }
