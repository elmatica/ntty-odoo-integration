from openerp import models, fields, api, _
from openerp.exceptions import except_orm
import urllib2, httplib, urlparse, gzip, requests, json
from StringIO import StringIO
import openerp.addons.decimal_precision as dp
import logging
#Get the logger
_logger = logging.getLogger(__name__)
from openerp.exceptions import ValidationError


USER_AGENT = 'OpenAnything/1.0 +http://diveintopython.org/http_web_services/'


class res_partner(models.Model):
    _inherit = 'res.partner'

    @api.one
    def _compute_ntty_url(self):
	url = ''
	system_param = self.env['ir.config_parameter'].search([('key','=','ntty_partner_viewing_address')])
	if system_param:
		url = system_param.value + str(self.ntty_partner_id)
	self.ntty_url = url

    @api.one
    @api.constrains('ntty_partner_id')
    def _check_ntty_partner_id(self):
	if self.supplier:
		return_value = self.search([('ntty_partner_id','=',self.ntty_partner_id)])
		if len(return_value) > 1:
			raise ValidationError('NTTY Partner ID must be unique!')
	return True
    
    ntty_partner_id = fields.Integer(string= _('Partner ID in NTTY'), help= _('Partner identifier in NTTY'))
    ntty_url = fields.Char(string="NTTY URL",compute='_compute_ntty_url')
    mnda = fields.Char(string='MNDA',size=128)
    short_name = fields.Char(string='Supplier Short Name',size=128)

