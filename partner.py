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

    ntty_partner_id = fields.Integer(string= _('Partner ID in NTTY'), help= _('Partner identifier in NTTY'))
    ntty_url = fields.Char(string="NTTY URL",compute='_compute_ntty_url')
    mnda = fields.Char(string='MNDA',size=128)
    short_name = fields.Char(string='Supplier Short Name',size=128)
    ntty_country_code = fields.Char(string='NTTY country code',size=128)
    verificationstate = fields.Char(string='NTTY verification state',size=128)
    company_number = fields.Char(string='NTTY company number',size=128)
    jurisdiction_code = fields.Char(string='NTTY jurisdiction code',size=128)
    organization_type = fields.Char(string='NTTY organization type',size=128)

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

    @api.model
    def _scheduled_connect_odoo_ntty(self):

        partners = self.env['res.partner'].search([('ntty_partner_id','!=','')])
        _logger.info('Synchronizing partners with NTTY')

        #http://www.ntty.com/api/v1/companies/

        if not partners:
	        _logger.warning('No partners (ntty_partner_id) entities to synchronize')
	        return None

 #       templates_string = str(templates_list)
 #       templates_string = templates_string.replace("'","\"")

        ntty = self.env['ntty.config.settings'].browse(1)
        if not ntty:
	        return None

        ntty_service_address = ntty['ntty_service_address']
        ntty_service_address = ntty_service_address.replace("http:","https:")
        ntty_service_user_email = ntty['ntty_service_user_email']
        ntty_service_token = ntty['ntty_service_token']


        httplib.HTTPConnection._http_vsn = 10
        httplib.HTTPConnection._http_vsn_str = 'HTTP/1.0'

        _errors = {}

        for partner in partners:
#            import pdb; pdb.set_trace()
            partner_string = partner.ntty_partner_id
            request_string = str(ntty_service_address) + "companies/" + str(partner_string)
            req = urllib2.Request(request_string)
            req.add_header('X-User-Email', str(ntty_service_user_email))
            req.add_header('X-User-Token', str(ntty_service_token))

            _logger.info(_('NTTY Check company (url): ')+str(request_string))

            try:
                resp = urllib2.urlopen(req)

                if not resp.code == 200 and resp.msg == "OK":
                    #raise except_orm(_('Warning'), _("Unable to connect to NTTY: string: ") + str(partner_string) + _(" code: ") + str(resp.code) )
                    _errors[ partner_string ] =  _("Unable to connect to NTTY: string: ") + str(partner_string) + _(" code: ") + str(resp.code)
                else:
                    content = resp.read()
                    res = json.loads(content)
                    _logger.info(_('NTTY Company info update >>> ')+str(content))
    #               {"id":106,
    #               "name":"Amphenol Printed Circuits, Inc.",
    #               "url":null,
    #               "country_code":null,
    #               "verificationstate":"Unverified",
    #               "company_number":"310626",
    #               "jurisdiction_code":"us_nh",
    #               "registered_address_in_full":"358 Hall Avenue\nWallingford CT 06492",
    #               "inactive":false,
    #               "organization_type":"COMPANY"}
                    if res["inactive"]:
                        act = False
                    else:
                        act = True

                    uvalues = {
                        'name': res["name"],
                        'ntty_url': res["url"],
                        'country_code': res["country_code"],
                        'verificationstate': res["verificationstate"],
                        'company_number': res["company_number"],
                        'jurisdiction_code': res["jurisdiction_code"],
                        'contact_address': res["registered_address_in_full"],
                        'active': act,
                        #'organization_type': res["organization_type"],
                    }
                    par = self.env['res.partner'].search([('ntty_partner_id','=', partner.ntty_partner_id)] )
                    if par:
                        result = par.write(uvalues)

            except StandardError, error:
#            except urllib2.HTTPError, error:
                contents = error.read()
                #raise except_orm(_('Warning'), _("Error connecting to NTTY: ") + str(partner_string)+_(" error:") + str(contents) )
                _errors[ partner_string ] =  _("Error connecting to NTTY: ") + str(partner_string)+_(" error:") + str(contents)


        if len(_errors)>0:
            #raise except_orm(_('Warning'), _("We found some errors: ") + str(_errors) )
            _logger.error( _("We found some errors: ") + str(_errors) )
