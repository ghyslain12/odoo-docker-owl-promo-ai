# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import UserError


class PromoAiSaleMaterialLine(models.Model):

    _name = 'promo_ai.sale.line'
    _description = 'Sale Material Line'
    _order = 'sale_id, material_id'

    sale_id = fields.Many2one(
        'promo_ai.sale',
        string='Sale',
        required=True,
        ondelete='cascade',
        index=True,
    )
    material_id = fields.Many2one(
        'promo_ai.material',
        string='Material',
        required=True,
        ondelete='restrict',
    )
    original_price = fields.Monetary(
        string='Original Price',
        currency_field='currency_id',
    )
    discount_amount = fields.Monetary(
        string='Discount Amount',
        currency_field='currency_id',
        default=0.0,
    )
    discount_percentage = fields.Float(
        string='Discount (%)',
        digits=(5, 2),
        default=0.0,
    )
    final_price = fields.Monetary(
        string='Final Price',
        currency_field='currency_id',
    )
    promotion_id = fields.Many2one(
        'promo_ai.promotion',
        string='Applied Promotion',
        ondelete='set null',
    )
    currency_id = fields.Many2one(
        related='sale_id.currency_id',
        store=True,
    )

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('material_id') and not vals.get('original_price'):
                material = self.env['promo_ai.material'].browse(vals['material_id'])
                vals.setdefault('original_price', material.price)
                vals.setdefault('final_price', material.price)
        return super().create(vals_list)

    @api.onchange('material_id')
    def _onchange_material_id(self):
        if self.material_id:
            self.original_price = self.material_id.price
            self._apply_promotion()

    def _apply_promotion(self, coupon_code=None):
        if not self.material_id:
            return

        promo = self.env['promo_ai.promotion'].find_applicable_promotions(
            self.material_id, coupon_code=coupon_code
        )

        price = self.original_price or self.material_id.price

        if promo:
            disc_amt, disc_pct, final = promo.compute_discount(price)
            self.update({
                'discount_amount': disc_amt,
                'discount_percentage': disc_pct,
                'final_price': final,
                'promotion_id': promo,
            })
        else:
            self.update({
                'discount_amount': 0.0,
                'discount_percentage': 0.0,
                'final_price': price,
                'promotion_id': False,
            })


class PromoAiSale(models.Model):
    _name = 'promo_ai.sale'
    _description = 'Sale'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'titre'
    _order = 'id desc'

    name = fields.Char(
        string='Reference',
        required=True,
        copy=False,
        readonly=True,
        default='New',
    )
    titre = fields.Char(
        string='Title',
        required=True,
        tracking=True,
    )
    description = fields.Text(
        string='Description',
        tracking=True,
    )
    customer_id = fields.Many2one(
        'promo_ai.customer',
        string='Customer',
        required=True,
        ondelete='cascade',
        tracking=True,
    )
    line_ids = fields.One2many(
        'promo_ai.sale.line',
        'sale_id',
        string='Materials',
    )
    material_ids = fields.Many2many(
        'promo_ai.material',
        compute='_compute_material_ids',
        string='Materials (flat)',
    )
    ticket_ids = fields.One2many(
        'promo_ai.ticket',
        'sale_id',
        string='Tickets',
    )
    coupon_code = fields.Char(
        string='Coupon Code',
        size=30,
    )
    total_amount = fields.Monetary(
        string='Total',
        compute='_compute_totals',
        store=True,
        currency_field='currency_id',
    )
    total_discount = fields.Monetary(
        string='Total Discount',
        compute='_compute_totals',
        store=True,
        currency_field='currency_id',
    )
    currency_id = fields.Many2one(
        'res.currency',
        string='Currency',
        default=lambda self: self.env.company.currency_id,
        required=True,
    )
    invoice_country = fields.Selection(
        selection=[
            ('france', 'France'),
            ('international', 'International'),
        ],
        string='Invoice Country',
        default='france',
    )
    invoice_generated = fields.Boolean(
        string='Invoice Generated',
        default=False,
    )
    ticket_count = fields.Integer(
        string='Nb. Tickets',
        compute='_compute_ticket_count',
    )

    @api.depends('line_ids.material_id')
    def _compute_material_ids(self):
        for rec in self:
            rec.material_ids = rec.line_ids.mapped('material_id')

    @api.depends('line_ids.final_price', 'line_ids.discount_amount')
    def _compute_totals(self):
        for rec in self:
            rec.total_amount = sum(rec.line_ids.mapped('final_price'))
            rec.total_discount = sum(rec.line_ids.mapped('discount_amount'))

    def _compute_ticket_count(self):
        for rec in self:
            rec.ticket_count = len(rec.ticket_ids)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'New') == 'New':
                vals['name'] = self.env['ir.sequence'].next_by_code('promo_ai.sale') or 'New'

        sales = super().create(vals_list)
        # pylint: disable=no-member
        sales._apply_promotions()
        return sales

    def write(self, vals):
        result = super().write(vals)
        if 'line_ids' in vals or 'coupon_code' in vals:
            self._apply_promotions()
        return result

    def _apply_promotions(self):
        for rec in self:
            for line in rec.line_ids:
                line._apply_promotion(coupon_code=rec.coupon_code)

    def action_apply_coupon(self):
        self.ensure_one()
        if not self.coupon_code:
            raise UserError(self.env._("Please enter a coupon code first."))

        promo = self.env['promo_ai.promotion'].search([
            ('target_type', '=', 'coupon'),
            ('code', '=', self.coupon_code),
            ('active', '=', True),
            ('state', '=', 'active'),
        ], limit=1)

        if not promo:
            raise UserError(
                self.env._(
                    "Coupon code '%s' is not valid or has expired.",
                    self.coupon_code,
                )
            )

        self._apply_promotions()
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Coupon Applied',
                'message': f"Coupon '{self.coupon_code}' applied successfully!",
                'type': 'success',
            },
        }

    def action_generate_invoice(self):
        self.ensure_one()
        self.invoice_generated = True
        return self.env.ref('promo_ai.action_sale_invoice_report').report_action(self)

    def action_view_tickets(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Tickets',
            'res_model': 'promo_ai.ticket',
            'view_mode': 'list,form',
            'domain': [('sale_id', '=', self.id)],
            'context': {'default_sale_id': self.id},
        }

    def action_open_invoice_wizard(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Generate Invoice',
            'res_model': 'promo_ai.generate.invoice.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_sale_id': self.id,
                'default_country': self.invoice_country or 'france',
            },
        }
