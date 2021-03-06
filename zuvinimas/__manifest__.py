# -*- coding: utf-8 -*-
{
    'name': "zuvinimas",

    'summary': """
        Model to monitor fish releases into water bodies.
        """,

    'description': """
        Model to monitor fish releases into water bodies.
        Posibilities to sort data, and export to excel.
    """,

    'author': "Karolis",
    'website': "https://b5277.k.dedikuoti.lt",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/12.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'EKOI',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'web'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'wizard/exel_export_wiz_view.xml',
        'views/templates.xml',
        'views/assets.xml',
        'views/zuvinimas.xml',
        'views/regions.xml',
        'views/lakes.xml',
        'views/releases.xml',
        'views/species.xml',
        'views/age_groups.xml',
        'views/rep_timeframe.xml'
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}
