from openerp import models, fields, api, _
from openerp.exceptions import except_orm
import urllib2, httplib, urlparse, gzip, requests, json
from StringIO import StringIO
import openerp.addons.decimal_precision as dp
import logging
#Get the logger
_logger = logging.getLogger(__name__)

class wizard_ntty_product_import_detail(models.TransientModel):
	_name = 'wizard.ntty.product.import.detail'

	import_id = fields.Many2one('wizard.ntty.product.import')
	partner_id = fields.Many2one('res.partner')
	selected = fields.Boolean('Selected')
	partner_data = fields.Char('Partner Data')

class wizard_ntty_product_import(models.TransientModel):
	_name = 'wizard.ntty.product.import'

	ntty_id = fields.Char('NTTY ID')
	detail_ids = fields.One2many(comodel_name='wizard.ntty.product.import.detail',inverse_name='import_id')

	@api.multi
	def action_import_ntty_products(self):
		import pdb;pdb.set_trace()
		return None

	@api.multi
	def pull_ntty_suppliers(self):
		ntty_id = self.ntty_id
		if not ntty_id:
                	return None
	        ntty = self.env['ntty.config.settings'].browse(1)
	        if not ntty:
        	        return None
	        ntty_service_address = ntty.ntty_service_address
	        ntty_service_user_email = ntty.ntty_service_user_email
        	ntty_service_token = ntty.ntty_service_token

	        httplib.HTTPConnection._http_vsn = 10
        	httplib.HTTPConnection._http_vsn_str = 'HTTP/1.0'

	        req = urllib2.Request(str(ntty_service_address) + "/entities/" + str(ntty_id))
        	req.add_header('X-User-Email', str(ntty_service_user_email))
	        req.add_header('X-User-Token', str(ntty_service_token))
        	try:
	            resp = urllib2.urlopen(req)
        	except StandardError:
	            raise except_orm(_('Warning'), _("Error connecting to NTTY."))
        	    return False

	        if not resp.code == 200 and resp.msg == "OK":
        	    raise except_orm(_('Warning'), _("Unable to connect to NTTY."))
	            return {}

        	content = resp.read()
        	res = json.loads(content)
		if res:
			import_id = self.id
			try:
				suppliers = res['entity']['values'].get('supplier_matching',[])
			except:
				suppliers = []
			for supplier in suppliers:
				supplier_id = self.env['res.partner'].search([('name','=',supplier['name'])])
				if supplier_id:
					vals_sup = {
						'import_id': import_id,
						'partner_id': supplier_id[0].id,
						'selected': False,		
						}
					return_id = self.env['wizard.ntty.product.import.detail'].create(vals_sup)
		# return True
		return {
			'type': 'ir.actions.act_window',
			'res_model': self._name, # this model
			'res_id': self.id, # the current wizard record
			'view_type': 'form',
			'view_mode': 'form',
			'target': 'new'}

	
