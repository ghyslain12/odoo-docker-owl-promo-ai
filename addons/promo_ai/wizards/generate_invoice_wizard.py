# -*- coding: utf-8 -*-
from odoo import models, fields
from odoo.exceptions import UserError


class GenerateInvoiceWizard(models.TransientModel):
    _name = 'promo_ai.generate.invoice.wizard'
    _description = 'Generate Invoice Wizard'

    sale_id = fields.Many2one(
        'promo_ai.sale',
        string='Sale',
        required=True,
        readonly=True,
    )
    country = fields.Selection(
        selection=[
            ('france', 'France'),
            ('international', 'International'),
        ],
        string='Invoice Country',
        required=True,
        default='france',
    )
    # Preview fields (readonly)
    sale_name = fields.Char(related='sale_id.name', readonly=True)
    sale_titre = fields.Char(related='sale_id.titre', readonly=True)
    customer_name = fields.Char(related='sale_id.customer_id.surnom', readonly=True)
    total_amount = fields.Monetary(related='sale_id.total_amount', readonly=True)
    total_discount = fields.Monetary(related='sale_id.total_discount', readonly=True)
    currency_id = fields.Many2one(related='sale_id.currency_id', readonly=True)
    line_ids = fields.One2many(related='sale_id.line_ids', readonly=True)

    def action_generate(self):
        self.ensure_one()
        if not self.sale_id.line_ids:
            raise UserError(self.env._("Cannot generate invoice for a sale with no materials."))

        self.sale_id.write({
            'invoice_country': self.country,
            'invoice_generated': True,
        })

        return self.env.ref('promo_ai.action_sale_invoice_report').report_action(self.sale_id)

    def action_download(self):
        return self.action_generate()
