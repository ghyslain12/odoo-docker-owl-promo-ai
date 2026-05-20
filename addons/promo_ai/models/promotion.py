# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import ValidationError


class PromoAiPromotion(models.Model):
    _name = 'promo_ai.promotion'
    _description = 'Promotion'
    _rec_name = 'name'
    _order = 'priority desc, id asc'

    name = fields.Char(
        string='Name',
        required=True,
        size=150,
    )
    code = fields.Char(
        string='Coupon Code',
        size=30,
        copy=False,
    )
    promo_type = fields.Selection(
        selection=[
            ('percentage', 'Percentage'),
            ('fixed_amount', 'Fixed Amount'),
        ],
        string='Discount Type',
        required=True,
        default='percentage',
    )
    value = fields.Float(
        string='Discount Value',
        required=True,
        digits=(8, 2),
        help='Percentage (e.g. 15 = -15%) or fixed amount (e.g. 10 = -10€)',
    )
    target_type = fields.Selection(
        selection=[
            ('material', 'Specific Material'),
            ('all', 'All Materials'),
            ('coupon', 'Coupon Code'),
        ],
        string='Target Type',
        required=True,
        default='all',
    )
    material_id = fields.Many2one(
        'promo_ai.material',
        string='Material',
        ondelete='set null',
        domain="[('active', '=', True)]",
    )
    starts_at = fields.Datetime(string='Start Date')
    ends_at = fields.Datetime(string='End Date')
    priority = fields.Integer(
        string='Priority',
        default=0,
        help='Higher priority promotions are applied first',
    )
    active = fields.Boolean(
        string='Active',
        default=True,
    )
    state = fields.Selection(
        selection=[
            ('active', 'Active'),
            ('scheduled', 'Scheduled'),
            ('expired', 'Expired'),
            ('disabled', 'Disabled'),
        ],
        string='Status',
        compute='_compute_state',
        store=True,
    )
    discount_label = fields.Char(
        string='Discount Label',
        compute='_compute_discount_label',
    )

    @api.depends('active', 'starts_at', 'ends_at')
    def _compute_state(self):
        now = fields.Datetime.now()
        for rec in self:
            if not rec.active:
                rec.state = 'disabled'
            elif rec.starts_at and rec.starts_at > now:
                rec.state = 'scheduled'
            elif rec.ends_at and rec.ends_at < now:
                rec.state = 'expired'
            else:
                rec.state = 'active'

    @api.depends('promo_type', 'value')
    def _compute_discount_label(self):
        for rec in self:
            if rec.promo_type == 'percentage':
                rec.discount_label = f"-{rec.value}%"
            else:
                rec.discount_label = f"-{rec.value}€"

    @api.constrains('target_type', 'material_id')
    def _check_material_required(self):
        for rec in self:
            if rec.target_type == 'material' and not rec.material_id:
                raise ValidationError(self.env._("A material must be selected when target type is 'Specific Material'."))

    @api.constrains('target_type', 'code')
    def _check_coupon_code_required(self):
        for rec in self:
            if rec.target_type == 'coupon' and not rec.code:
                raise ValidationError(self.env._("A coupon code is required when target type is 'Coupon Code'."))

    @api.constrains('value', 'promo_type')
    def _check_value(self):
        for rec in self:
            if rec.value <= 0:
                raise ValidationError(self.env._("Discount value must be positive."))
            if rec.promo_type == 'percentage' and rec.value > 100:
                raise ValidationError(self.env._("Percentage discount cannot exceed 100%."))

    @api.constrains('starts_at', 'ends_at')
    def _check_dates(self):
        for rec in self:
            if rec.starts_at and rec.ends_at and rec.starts_at >= rec.ends_at:
                raise ValidationError(self.env._("End date must be after start date."))

    _code_uniq = models.Constraint(
        'UNIQUE(code)',
        'Promotion code must be unique.'
    )

    def compute_discount(self, price):
        self.ensure_one()
        if self.promo_type == 'percentage':
            discount_amount = round(price * self.value / 100, 2)
            discount_pct = self.value
        else:
            discount_amount = min(self.value, price)
            discount_pct = round(discount_amount / price * 100, 2) if price else 0
        final_price = round(price - discount_amount, 2)
        return discount_amount, discount_pct, final_price

    @api.model
    def find_applicable_promotions(self, material, coupon_code=None):
        domain_base = [
            ('active', '=', True),
            ('state', '=', 'active'),
        ]

        promo = self.search(domain_base + [
            ('target_type', '=', 'material'),
            ('material_id', '=', material.id),
        ], order='priority desc', limit=1)
        if promo:
            return promo

        if coupon_code:
            promo = self.search(domain_base + [
                ('target_type', '=', 'coupon'),
                ('code', '=', coupon_code),
            ], order='priority desc', limit=1)
            if promo:
                return promo

        promo = self.search(domain_base + [
            ('target_type', '=', 'all'),
        ], order='priority desc', limit=1)
        if promo:
            return promo

        return self.env['promo_ai.promotion']
