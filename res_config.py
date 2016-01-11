
from openerp import models, fields, api, _
import urllib2, urlparse, gzip, requests
from StringIO import StringIO

USER_AGENT = 'OpenAnything/1.0 +http://diveintopython.org/http_web_services/'

class ntty_config_settings(models.Model):
	_name = 'ntty.config.settings'

	ntty_service_address = fields.Char(String="Service Address", store=True)
	ntty_service_user_email = fields.Char(String="Service User Email", store=True)
	ntty_service_token = fields.Char(String="Service Token", store=True)
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
