# -*- coding: utf-8 -*-

import json
import logging

from odoo import http
from odoo.http import request, Response
from odoo.exceptions import ValidationError, UserError, AccessError

_logger = logging.getLogger(__name__)


def _json_response(data, status=200):
    return Response(
        json.dumps(data, default=str),
        status=status,
        content_type='application/json',
    )


def _error_response(message, status=400):
    return _json_response({'error': message}, status=status)


class PromoAiMaterialController(http.Controller):

    @http.route('/promo_ai/materials', type='http', auth='user', methods=['GET'], csrf=False)
    def list_materials(self, **kwargs):
        try:
            materials = request.env['promo_ai.material'].search([('active', '=', True)])
            data = [{
                'id': m.id,
                'designation': m.designation,
                'price': float(m.price),
                'sale_count': m.sale_count,
                'active_promotion': m.active_promotion_id.name if m.active_promotion_id else None,
            } for m in materials]
            return _json_response({'data': data, 'count': len(data)})
        except AccessError:
            return _error_response('Access denied', 403)

    @http.route('/promo_ai/materials/<int:material_id>', type='http', auth='user',
                methods=['GET'], csrf=False)
    def get_material(self, material_id, **kwargs):
        mat = request.env['promo_ai.material'].browse(material_id)
        if not mat.exists():
            return _error_response('Material not found', 404)
        return _json_response({
            'id': mat.id,
            'designation': mat.designation,
            'price': float(mat.price),
            'sale_count': mat.sale_count,
            'active': mat.active,
        })

    @http.route('/promo_ai/materials', type='jsonrpc', auth='user', methods=['POST'], csrf=False)
    def create_material(self, **post):
        data = request.get_json_data()
        if not data.get('designation'):
            return {'error': 'Missing designation'}

        mat = request.env['promo_ai.material'].create({
            'designation': data.get('designation'),
            'price': float(data.get('price', 0)),
        })
        return {'id': mat.id, 'designation': mat.designation}


class PromoAiSaleController(http.Controller):

    @http.route('/promo_ai/sales', type='http', auth='user', methods=['GET'], csrf=False)
    def list_sales(self, **kwargs):
        try:
            sales = request.env['promo_ai.sale'].search([], order='id desc', limit=100)
            data = [{
                'id': s.id,
                'name': s.name,
                'titre': s.titre,
                'customer': s.customer_id.surnom,
                'total_amount': float(s.total_amount),
                'total_discount': float(s.total_discount),
                'ticket_count': s.ticket_count,
                'invoice_generated': s.invoice_generated,
            } for s in sales]
            return _json_response({'data': data, 'count': len(data)})
        except AccessError:
            return _error_response('Access denied', 403)

    @http.route('/promo_ai/sales/<int:sale_id>', type='http', auth='user',
                methods=['GET'], csrf=False)
    def get_sale(self, sale_id, **kwargs):
        sale = request.env['promo_ai.sale'].browse(sale_id)
        if not sale.exists():
            return _error_response('Sale not found', 404)
        data = {
            'id': sale.id,
            'name': sale.name,
            'titre': sale.titre,
            'description': sale.description or '',
            'customer': {
                'id': sale.customer_id.id,
                'surnom': sale.customer_id.surnom,
            },
            'lines': [{
                'material': line.material_id.designation,
                'original_price': float(line.original_price),
                'discount_percentage': line.discount_percentage,
                'discount_amount': float(line.discount_amount),
                'final_price': float(line.final_price),
                'promotion': line.promotion_id.name if line.promotion_id else None,
            } for line in sale.line_ids],
            'tickets': [{
                'id': t.id,
                'titre': t.titre,
                'state': t.state,
                'priority': t.priority,
            } for t in sale.ticket_ids],
            'total_amount': float(sale.total_amount),
            'total_discount': float(sale.total_discount),
            'invoice_generated': sale.invoice_generated,
            'invoice_country': sale.invoice_country,
        }
        return _json_response(data)

    @http.route('/promo_ai/sales/<int:sale_id>/invoice', type='http', auth='user',
                methods=['GET'], csrf=False)
    def download_invoice(self, sale_id, country='france', **kwargs):
        sale = request.env['promo_ai.sale'].browse(sale_id)
        if not sale.exists():
            return _error_response('Sale not found', 404)
        if not sale.line_ids:
            return _error_response('Cannot generate invoice: no materials', 400)

        sale.write({'invoice_country': country, 'invoice_generated': True})
        pdf_content, _ = request.env['ir.actions.report']._render_qweb_pdf(
            'promo_ai.report_sale_invoice_template', [sale.id]
        )
        filename = f"{sale.name}-{country.upper()}.pdf"
        return request.make_response(
            pdf_content,
            headers=[
                ('Content-Type', 'application/pdf'),
                ('Content-Disposition', f'attachment; filename="{filename}"'),
            ]
        )


class PromoAiPromotionController(http.Controller):

    @http.route('/promo_ai/promotions', type='http', auth='user', methods=['GET'], csrf=False)
    def list_promotions(self, **kwargs):
        promos = request.env['promo_ai.promotion'].search([('active', '=', True)])
        data = [{
            'id': p.id,
            'name': p.name,
            'code': p.code or '',
            'promo_type': p.promo_type,
            'value': p.value,
            'target_type': p.target_type,
            'material': p.material_id.designation if p.material_id else None,
            'discount_label': p.discount_label,
            'state': p.state,
            'priority': p.priority,
        } for p in promos]
        return _json_response({'data': data, 'count': len(data)})

    @http.route('/promo_ai/promotions/validate/<string:code>', type='http', auth='user',
                methods=['GET'], csrf=False)
    def validate_coupon(self, code, **kwargs):
        promo = request.env['promo_ai.promotion'].search([
            ('target_type', '=', 'coupon'),
            ('code', '=', code),
            ('active', '=', True),
            ('state', '=', 'active'),
        ], limit=1)
        if not promo:
            return _json_response({'valid': False, 'message': 'Invalid or expired coupon'})
        return _json_response({
            'valid': True,
            'promo_id': promo.id,
            'name': promo.name,
            'discount_label': promo.discount_label,
        })


class PromoAiDashboardController(http.Controller):

    @http.route('/promo_ai/dashboard/stats', type='http', auth='user',
                methods=['GET'], csrf=False)
    def dashboard_stats(self, **kwargs):
        env = request.env
        Sale = env['promo_ai.sale']
        Material = env['promo_ai.material']
        Customer = env['promo_ai.customer']
        Ticket = env['promo_ai.ticket']
        Promotion = env['promo_ai.promotion']

        all_sales = Sale.search([])
        total_revenue = sum(all_sales.mapped('total_amount'))
        total_discount = sum(all_sales.mapped('total_discount'))

        open_tickets = Ticket.search_count([('state', 'in', ['new', 'in_progress'])])
        active_promos = Promotion.search_count([('state', '=', 'active')])

        return _json_response({
            'sales': {
                'total': len(all_sales),
                'total_revenue': total_revenue,
                'total_discount': total_discount,
                'with_invoice': Sale.search_count([('invoice_generated', '=', True)]),
            },
            'materials': {
                'total': Material.search_count([('active', '=', True)]),
                'with_promo': Material.search_count([('active_promotion_id', '!=', False)]),
            },
            'customers': {
                'total': Customer.search_count([]),
            },
            'tickets': {
                'total': Ticket.search_count([]),
                'open': open_tickets,
                'resolved': Ticket.search_count([('state', 'in', ['resolved', 'closed'])]),
            },
            'promotions': {
                'active': active_promos,
                'total': Promotion.search_count([]),
            },
        })
