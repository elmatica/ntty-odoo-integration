
from openerp import models, fields, api, _
import urllib2, urlparse, gzip, requests
from StringIO import StringIO

USER_AGENT = 'OpenAnything/1.0 +http://diveintopython.org/http_web_services/'

class ntty_lifecycle_mapping(models.Model):
	_name = 'ntty.lifecycle.mapping'

	ntty_id = fields.Many2one('ntty.config.settings')
	name = fields.Char('Value in NTTY')
	description = fields.Char('Description in NTTY')
	state2 = fields.Selection([('draft', 'In Development'),('sellable', 'Normal'),('end', 'End of Lifecycle'),('obsolete', 'Obsolete')], default='draft', string='State', copy=False)

	

class ntty_config_settings(models.Model):
	_name = 'ntty.config.settings'

	ntty_service_address = fields.Char(String="Service Address", store=True)
	ntty_service_user_email = fields.Char(String="Service User Email", store=True)
	ntty_service_token = fields.Char(String="Service Token", store=True)
	ntty_check_supliers = fields.Boolean(string='Check Suppliers',default=True)
	ntty_generate_price_list = fields.Boolean(string='Generate PriceList',default=True)
	ntty_related_products = fields.Boolean(string='Include Related Products',default=True)
	ntty_partner_info = fields.Boolean(string='Include Partner Information',default=True)
	ntty_product_category = fields.Boolean(string='Include Product Category',default=True)
	ntty_supplier_short_name = fields.Boolean(string='Include Supplier Short Name',default=True)
	ntty_update_lifecycle_manually = fields.Boolean(string='Update Lifecycle Manually',default=True)
	ntty_lifecycle_ids = fields.One2many(comodel_name='ntty.lifecycle.mapping',inverse_name='ntty_id')
	#ntty_service_type = fields.Char(String="Export type", default='odoo_export', store=True)

	"""
	@api.one
	def get_default_ntty(self):
		if len(self) < 1:
			return {}			
		res = {}
		for record in self[0]:
			res['ntty_service_address'] = self.ntty_service_address
			res['ntty_service_user_email'] = self.ntty_service_address
			res['ntty_service_token'] = self.ntty_service_token
		return res
	"""
