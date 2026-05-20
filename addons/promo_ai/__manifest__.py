# -*- coding: utf-8 -*-
{
    'name': 'Promo AI — Sales, Ticketing & Promotions',
    'version': '19.0.1.1.0',
    'summary': 'Complete CRUD for Sales, Materials, Customers, Tickets & Promotions with PDF invoice generation',
    'description': """
        Module équivalent au projet Laravel/Angular promo-ai.

        Fonctionnalités :
        - Gestion des Matériels (désignation + prix)
        - Gestion des Clients (liés aux utilisateurs Odoo)
        - Gestion des Ventes (titre, description, client, matériels)
        - Gestion des Tickets (liés aux ventes)
        - Système de Promotions (coupon, global, par matériel)
        - Calcul automatique des remises lors de la création de ventes
        - Génération de factures PDF localisées (France / international)
        - Dashboard avec statistiques
        - Tests unitaires et d'intégration
    """,
    'author': 'Promo AI',
    'category': 'Sales',
    'depends': [
        'base',
        'mail',
        'web',
    ],
    'data': [
        # Security
        'security/ir.model.access.csv',
        'security/promo_ai_security.xml',

        # Data
        'data/promo_ai_sequence.xml',

        # Views
        'views/material_views.xml',
        'views/customer_views.xml',
        'views/ticket_views.xml',
        'views/promotion_views.xml',
        'views/sale_views.xml',
        'views/dashboard_views.xml',
        'views/dashboard_action.xml',
        'views/menu_views.xml',

        # Reports
        'report/sale_invoice_report.xml',
        'report/sale_invoice_template.xml',

        # Wizards
        'wizards/generate_invoice_wizard_views.xml',

        # Templates
        'templates/login.xml',
        'templates/webclient_templates.xml',
    ],
    'demo': [
        'demo/promo_ai_demo.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            # Login page gets the same CSS variables
            'promo_ai/static/src/css/promo_ai.css',
        ],
        'web.assets_backend': [
            'promo_ai/static/src/css/promo_ai.css',
            'promo_ai/static/src/js/dashboard.js',
            'promo_ai/static/src/xml/dashboard.xml',
        ],
    },
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'LGPL-3',
}
