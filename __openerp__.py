{
    'name': 'NTTY - Odoo Integration',
    'category': 'Sales',
    'version': '0.1',
    'depends': ['base','product','product_brand','product_lifecycle','stock','website_sale'],
    'data': [
	'views/ntty_view.xml',
	'wizard/wizard_view.xml',
    ],
    'demo': [
    ],
    'qweb': [],
    'installable': True,
}
