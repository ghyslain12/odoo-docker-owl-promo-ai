# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import ValidationError


class PromoAiMaterial(models.Model):
    _name = 'promo_ai.material'
    _description = 'Material'
    _rec_name = 'designation'
    _order = 'designation asc'

    designation = fields.Char(string='Designation', required=True, size=255)
    price = fields.Monetary(string='Price', required=True, currency_field='currency_id')
    currency_id = fields.Many2one(
        'res.currency',
        string='Currency',
        default=lambda self: self.env.company.currency_id,
        required=True
    )
    sale_ids = fields.Many2many(
        'promo_ai.sale',
        'promo_ai_material_sale_rel',
        'material_id',
        'sale_id',
        string='Sales',
    )
    promotion_ids = fields.One2many('promo_ai.promotion', 'material_id', string='Promotions')

    active_promotion_id = fields.Many2one(
        'promo_ai.promotion',
        string='Active Promotion',
        compute='_compute_active_promotion',
        store=True,
    )
    has_active_promotion = fields.Boolean(
        string='Has Active Promotion',
        compute='_compute_active_promotion',
        store=True,
    )

    active = fields.Boolean(default=True)
    sale_count = fields.Integer(string='Sales Count', compute='_compute_sale_count')

    @api.depends('promotion_ids', 'promotion_ids.active', 'promotion_ids.state')
    def _compute_active_promotion(self):
        for rec in self:
            rec_id = rec._origin.id if rec._origin else rec.id

            promo = self.env['promo_ai.promotion'].search([
                ('material_id', '=', rec_id),
                ('active', '=', True),
                ('state', '=', 'active'),
            ], order='priority desc', limit=1)

            rec.active_promotion_id = promo
            rec.has_active_promotion = bool(promo)

    @api.depends('sale_ids')
    def _compute_sale_count(self):
        for rec in self:
            rec.sale_count = len(rec.sale_ids)

    @api.constrains('price')
    def _check_price(self):
        for rec in self:
            if rec.price < 0:
                raise ValidationError(self.env._("Price must be a positive value."))

    def action_view_sales(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Sales',
            'res_model': 'promo_ai.sale',
            'view_mode': 'tree,form',
            'domain': [('material_ids', 'in', [self.id])],
        }
