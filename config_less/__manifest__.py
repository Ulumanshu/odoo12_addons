# -*- coding: utf-8 -*-
{
    'name': "config_less",

    'summary': """
        Consumel.ess Odoo server""",

    'description': """
        Product, Inventory, Web and Accounting hub for home bussiness
    """,

    'author': "Wooden",
    'website': "https://www.facebook.com/consumeL.ESSdesign/",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/12.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'LESS',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'product'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'views/views.xml',
        'views/templates.xml',
        'views/product_view.xml'
    ],
}
