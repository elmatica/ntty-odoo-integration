from openerp import models, fields, api, _
from openerp.exceptions import except_orm
import urllib2, httplib, urlparse, gzip, requests, json
from StringIO import StringIO
import openerp.addons.decimal_precision as dp
import logging
#Get the logger
_logger = logging.getLogger(__name__)


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

    ntty_partner_id = fields.Integer(string= _('Partner ID in NTTY'), help= _('Partner identifier in NTTY'))
    ntty_url = fields.Char(string="NTTY URL",compute='_compute_ntty_url')
    mnda = fields.Char(string='MNDA',size=128)
    short_name = fields.Char(string='Supplier Short Name',size=128)

    @api.onchange('short_name')
    def update_product_name(self):
	ntty = self.env['ntty.config.settings'].search([])
	# ntty = self.env['ntty.config.settings'].browse(1)
        if not ntty:
                return None
	if not ntty.ntty_supplier_short_name:
		return None
	supplier = self.env['res.partner'].search([('ntty_partner_id','=',self.ntty_partner_id)])
        if supplier and len(supplier) == 1:
	    prod_suppliers = self.env['product.supplierinfo'].search([('name','=',supplier.id)])
	    for prod_sup in prod_suppliers:
                prod_template = prod_sup.product_tmpl_id
                new_name = prod_template.article_part_number + ' ' + prod_template.product_code + ' ' +  self.short_name
                prod_template.write({'name': new_name})

class product_product(models.Model):
    _inherit = 'product.product'

    ntty_part_number = fields.Char(string="NTTY Part Number")

class product_template(models.Model):
    _inherit = 'product.template'

    ntty_exists = fields.Boolean(compute='_ntty_id_exists', store=True, string="NTTY", default=False)
    # article_part_number = fields.Char(string="Base Part Number")
    article_part_number = fields.Char(string="Product Owner Reference")
    ntty_name = fields.Char(string="NTTY Name")
    ntty_id = fields.Char(string="NTTY ID")
    ntty_odoo = fields.Char(string="NTTY ID/ODOO")
    ntty_url = fields.Char(string="NTTY URL",readonly=True,compute='compute_ntty_url')
    # customer_pn = fields.Char('Customer PartNum')
    panel_factor = fields.Integer('Panel Factor', help="The number of units/PCB's that fit on one panel")
    panel_weight = fields.Float('Panel Weight', help="The weight of an individual panel",digits=dp.get_precision('Product Weight'))
    panel_width = fields.Float('Panel Width')
    panel_length = fields.Float('Panel Length')
    panel_thickness = fields.Float('Panel Thickness')
    panel_layers = fields.Integer('Layers', help="The number of layers in the Panel/PCB")
    panel_type = fields.Selection((('rigid', 'Rigid'), ('flex', 'Flexible')), 'Panel Type')
    pcb_weight = fields.Float('PCB Weight', help="The Weight of one PCB in grams",digits=dp.get_precision('Product Weight'))
    sqm_pcb = fields.Float('Sqm PCB', help="PCB surface square meters",digits=dp.get_precision('Product UoS'))
    # sqm_pcb = fields.Float('Sqm PCB', help="PCB surface square meters")
    signal_layers = fields.Integer('Signal Layers', help="PCB signal layers")
    product_brand_text = fields.Char('Product Owner as in NTTY')
    product_code = fields.Char('Product Code')
    ntty_ul = fields.Boolean('UL',default=False)
    ntty_rohs = fields.Boolean('ROHS',default=False)
    lifecycle_blocks_orders = fields.Boolean('Lifecycle Blocks Orders',default=False,readonly=True)
    lifecycle_blocks_quotes = fields.Boolean('Lifecycle Blocks Quotes',default=False,readonly=True)
    lifecycle = fields.Char('Lifecycle')

    @api.one
    @api.depends('ntty_id')
    def _ntty_id_exists(self):
        res = False
        if self.ntty_id:
            res = True
            self.ntty_exists = True

        return res

    @api.one
    def compute_ntty_url(self):
        ir_config_parameter = self.env['ir.config_parameter'].search([('key','=','ntty_viewing_address')])
        if ir_config_parameter:
            if self.ntty_id:
                self.ntty_url = ir_config_parameter.value + self.ntty_id
            else:
                self.ntty_url = ir_config_parameter.value
        else:
            if self.ntty_id:
                self.ntty_url = self.ntty_id or ''
            else:
                self.ntty_url = self.ntty_id

    @api.model
    def _scheduled_connect_odoo_ntty(self):
        mapp = {
            "Imagine": 1,
            "Specify": 2,
            "Plan": 3,
            "Innovate": 4,
            "Describe": 5,
            "Define": 6,
            "Develop": 7,
            "Test": 8,
            "Analyze": 9,
            "Validate": 10,
            "Manufacture": 11,
            "Make": 12,
            "Build": 13,
            "Procure": 14,
            "Produce": 15,
            "Sell": 16,
            "Deliver": 17,
            "Use": 18,
            "Operate": 19,
            "Maintain": 20,
            "Support": 21,
            "Sustain": 22,
            "Phase-out": 23,
            "Retire": 24,
            "Recycle": 25,
            "Disposal": 26,
        }

        templates = self.env['product.template'].search([('ntty_id','!=','')])
        _logger.info('Synchronizing products with NTTY')

        templates_list = []
        for template in templates:
	        #http://www.ntty.com/api/v1/lifecycle?entities=["entity.identifier1", "entity_identifier2"]
	        #http://www.ntty.com/api/v1/lifecycle?entities=["1ee966fd8d1b116a1a971b499c", "1ee966fd8d1b116a1a971b499c", "1ee966fd8d1b116a1a971b499c", "1ee966fd8d1b116a1a971b499c", "1ee966fd8d1b116a1a971b499c", "1ee966fd8d1b116a1a971b499c", "1ee966fd8d1b116a1a971b499c", "1ee966fd8d1b116a1a971b499c"]'

	        if str(template.ntty_id) not in templates_list:
		        templates_list.append(str(template.ntty_id))
        if not templates:
	        _logger.warning('No entities to synchronize')
	        return None
        templates_string = str(templates_list)
        templates_string = templates_string.replace("'","\"")

	ntty = self.env['ntty.config.settings'].search([])
        # ntty = self.env['ntty.config.settings'].browse(1)
        if not ntty:
	        return None

        ntty_service_address = ntty['ntty_service_address']
        ntty_service_address = ntty_service_address.replace("http:","https:")
        ntty_service_user_email = ntty['ntty_service_user_email']
        ntty_service_token = ntty['ntty_service_token']

        httplib.HTTPConnection._http_vsn = 10
        httplib.HTTPConnection._http_vsn_str = 'HTTP/1.0'

        request_string = str(ntty_service_address) + "lifecycle?entities=" + str(templates_string)

        req = urllib2.Request(request_string)
        req.add_header('X-User-Email', str(ntty_service_user_email))
        req.add_header('X-User-Token', str(ntty_service_token))
        try:
            resp = urllib2.urlopen(req)
        except urllib2.HTTPError, e:
            raise except_orm('Warning','HTTPError = ' + str(e.code))
            return False
        except urllib2.URLError, e:
            raise except_orm('Warning','URLError = ' + str(e.reason))
            return False
        except httplib.HTTPException, e:
            raise except_orm('Warning','HTTPException')
            return False
        except StandardError:
            raise except_orm(_('Warning'), _("Error connecting to NTTY."))
            return False


        if not resp.code == 200 and resp.msg == "OK":
            raise except_orm(_('Warning'), _("Unable to connect to NTTY."))
            return {}

        content = resp.read()

        res = json.loads(content)

        lifecycle_ntty_id = res["entity_lifecycle"][0]["entity"]
        lifecycle_stage = res["entity_lifecycle"][0]["lifecycle_stage"]
        _logger.info('Mapping NTTY to Lifecycle:' + str(lifecycle_stage) )

        imap = mapp[ lifecycle_stage ]
        _logger.info('Mapping NTTY to Lifecycle imap[]:' + str(imap) )
        outvalue = ""
	lifecycle_mapping = self.env['ntty.lifecycle.mapping'].search([('ntty_id','=',ntty.id),('name','=',str(imap))])
	if lifecycle_mapping:
		outvalue = lifecycle_mapping.state2
	else:
            raise except_orm(_('Warning'), _("Can not map lifecycle."))
            return {}

        #if imap<=10:
        #    outvalue = "draft"
        #elif imap<=22:
        #    outvalue = "sellable"
        #elif imap<=24:
        #    outvalue = "end"
        #elif imap<=26:
        #    outvalue = "obsolete"

        _logger.info('Mapping NTTY to Lifecycle:' + str(outvalue) )
        templates = self.env['product.template'].search([('ntty_id','=',lifecycle_ntty_id)])
        for template in templates:
            products = self.env['product.product'].search([('product_tmpl_id','=', template.id)] )
            products.write({'state2': outvalue })

        #if len(res) > 0:
        #	template.import_product_ntty(template.ntty_id)
        _logger.info('Done synchronizing NTTY with Odoo')

    @api.model
    def _connect_odoo_ntty(self):
        templates = self.search([('ntty_id','!=','')])
        _logger.debug('Synchronizing with NTTY')
        for template in templates:
            _logger.debug('Synchronizing product ' + template.name)
            template.import_product_ntty(template.ntty_id)
        _logger.debug('Done synchronizing NTTY with Odoo')

    @api.one
    def button_import_wizard(self):
        return {
           'name': 'ntty_product_import_wizard',
           'views': [('ntty_product_import_wizard','form')],
           'view_id': 'launch_ntty_import_product_wizard',
           'type': 'ir.actions.act_window',
           'res_model': 'wizard.ntty.product.import',
           'view_mode': 'form',
           'view_type': 'form',
           'target': 'new',
           'context': {},
        }




    @api.one
    def button_import_update_product_ntty(self):
        self.import_product_ntty(self.ntty_id)
        return None

    @api.one
    def import_product_ntty(self,ntty_id=None):
        if not ntty_id:
            return None
	ntty = self.env['ntty.config.settings'].search([])
        # ntty = self.env['ntty.config.settings'].browse(1)
        if not ntty:
            return None
        ntty_service_address = ntty['ntty_service_address']
        ntty_service_user_email = ntty['ntty_service_user_email']
        ntty_service_token = ntty['ntty_service_token']

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

        if len(res) > 0:
            entity = res['entity']
            part_numbers = res['part_numbers']

	    flag_ul = False
	    flag_rohs = False
	    flag_defense = False
	    flag_automotive = False
	    certifications = entity['values'].get('certifications',False)
	    categ_id = 1
        if certifications:
            for certification in certifications:
                if certification['id'] == 131:
                    flag_rohs = True
                if certification['id'] == 132:
                    flag_ul = True
                if 'Automotive' in certification['name']:
                    flag_automotive = True
                    category_id = self.env['product.category'].search([('name','=','Automotive')])
                    if category_id:
                        categ_id = category_id.id
                if 'Defense' in certification['name']:
                    flag_defense = True
                    category_id = self.env['product.category'].search([('name','=','Defense')])
                    if category_id:
                        categ_id = category_id.id

	    # Searches for product_owner
	    product_brand = entity.get('product_owner','')
	    product_brand_text = entity.get('product_owner','')
	    lifecycle_blocks_orders = entity.get('lifecycle_blocks_orders',False)
	    lifecycle_blocks_quotes = entity.get('lifecycle_blocks_quotes',False)
	    lifecycle = entity.get('lifecycle',False)
	    product_brand_id = None
        if product_brand:
            partner_id = self.env['res.partner'].search([('name','=',product_brand)])
        if partner_id:
            product_brand_id = partner_id[0].id
        else:
            unknown_brand = self.env['product.brand'].search([('name','=','N/A')])
            if unknown_brand:
                    product_brand_id = unknown_brand[0].id
            else:
                unknown_brand = self.env['product.brand'].search([('name','=','N/A')])
                product_brand_id = unknown_brand.id

	    # article_part_number = entity.get('article_part_number','')
        article_part_number = entity.get('name','N/A')
        identifier = entity.get('identifier','')
        article_part_name = entity.get('article_part_name','article_part_number')
        short_description = entity.get('short_description','')
        long_description = entity.get('long_description','')
        article_id = entity.get('article_id','')
        panel_factor = int(entity['values'].get('panel_units',entity['values'].get('units',1)))

        try:
            panel_weight = float(entity['values']['weight_calculation_panel'][0]['panel_weight'])
        except KeyError:
            panel_weight = 1.00

        try:
            panel_length = float(entity['values']['pcb_length'])
        except KeyError:
            panel_length = 0.00

        try:
            panel_width = float(entity['values']['pcb_width'])
        except KeyError:
            panel_width = 0.00

        try:
            sqm_pcb = float(entity['values']['sqm_pcb'])
        except KeyError:
            sqm_pcb = 0.00

        try:
            signal_layers = float(entity['values']['signal_layers'])
        except KeyError:
            signal_layers = 0.00

        try:
            weight_calc = (panel_weight / panel_factor) / 1000
        except FloatingPointError:
            weight_calc = 0.00

        try:
            files = entity['files']
            for file in files:
                print file['url']
        except KeyError:
            files = {}


	    # This is the place
	    # prod = self.env['product.template'].search([('ntty_id', '=', identifier)])
        vals = {
                'name': article_part_name,
                'article_part_number': article_part_number,
                'description': long_description,
                'ntty_id': ntty_id,
                'type': "consu",
                'panel_factor': panel_factor,
                'panel_weight': panel_weight,
                'panel_width': panel_width,
                'panel_length': panel_length,
                'weight_net': weight_calc,
                'weight': weight_calc,
                'sqm_pcb': sqm_pcb,
                'signal_layers': signal_layers,
                'product_brand_id': product_brand_id,
                'product_brand_text': product_brand_text,
                'ntty_rohs': flag_rohs,
                'lifecycle_blocks_orders': lifecycle_blocks_orders,
                'lifecycle_blocks_quotes': lifecycle_blocks_quotes,
                'lifecycle': lifecycle,
                'ntty_ul': flag_ul,
                'categ_id': categ_id,}
        product_code = ''
        part_name = ''
        part_description = ''
        for part_number in part_numbers:
            if part_number['part_organization'] == 'ELMATICA AS':
                default_code = part_number.get('part_number','')
            if part_number['part_organization'] != 'ELMATICA AS' and part_number['part_organization'] != product_brand_text:
                part_name = part_number.get('part_name','')
                part_description = part_number.get('part_description','')
                product_code = part_number.get('part_number','')
                vals['product_code'] = product_code
        vals = {
            'default_code': default_code,
            'name': article_part_number + ' ' + product_code,
            'description': part_description,
            # 'product_tmpl_id': prod.id,
        }
		# searches for product with empty default_code
	    #product_id = self.env['product.product'].search([('product_tmpl_id','=',prod.id)])
	    #if not product_id:
	#	    product_id = self.env['product.product'].create(vals)
	 #   else:
	#	    for product in product_id:
	#		    product.write(vals)

            # suppliers = entity['values']['supplier_matching'] #json.loads(str(entity['values']['capable_supplier']).replace("=>",":"))
            # prod.seller_ids.unlink()
        try:
            # suppliers = entity['values']['capable_supplier']
            suppliers = entity['values']['supplier_matching']
            # suppliers = entity['values']['certification_matching']
            if suppliers and suppliers != 'multiple values in the entities':
		supplier = {}
                if type(suppliers) == dict:
                    suppliers = [suppliers]
                    for supplier in suppliers:
                        sup_odoo = self.env['res.partner'].search([('supplier', '=', True), ('is_company', '=', True),\
                     ('ntty_partner_id', '=', supplier['id'])])
                        if not sup_odoo:
                            sup_odoo = self.env['res.partner'].create({'supplier': True,'is_company': True, 'name': supplier['name'], 'ntty_partner_id': supplier['id'], 'partner_approved': True, 'active': True})
                identifier_odoo = identifier + '#' + str(supplier['id'])
                prod = self.env['product.product'].search([('ntty_odoo', '=', identifier_odoo)])
                vals['ntty_odoo'] = identifier_odoo
                vals['ntty_id'] = identifier
                if not prod:
                    prod = prod.create(vals)
                else:
                    prod.write(vals)

                for sup_in_odoo in sup_odoo:
                    vals_supplier = {
                        'name': sup_in_odoo.id,
                        'company_id': 1,
                        'product_tmpl_id': prod.product_tmpl_id.id,
                        }
                prod_sup = self.env['product.supplierinfo'].create(vals_supplier)
            else:
                suppliers = {}
        except KeyError:
            suppliers = {}
        prod.message_post(body="NTTY information \n" + str(entity), context={})
        return prod


    def fetch_ntty_suppliers_prices(self, ntty_id, suppliers, quantities):
        ntty = self.env['ntty.config.settings'].get_default_ntty()
        if not ntty:
            return None
        ntty_service_address = ntty['ntty_service_address']
        ntty_service_user_email = ntty['ntty_service_user_email']
        ntty_service_token = ntty['ntty_service_token']

        if not ntty_id:
            ntty_id = self.ntty_id

        req = urllib2.Request(str(ntty_service_address) + "entities/" + str(ntty_id) + "/calculate?suppliers=" + suppliers + "&quantities=" + quantities + "&return_type=short")
        req.add_header('X-User-Email', str(ntty_service_user_email))
        req.add_header('X-User-Token', str(ntty_service_token))
        try:
            resp = urllib2.urlopen(req)
        except StandardError:
            raise except_orm(_('Warning'), _("Error connecting to NTTY."))
            return False

        if not resp.code == 200 and resp.msg == "OK":
            print "Did not manage to connect to NTTY"
            return {}

        content = resp.read()
        res = json.loads(content)

        if not res:
            raise except_orm(_('Warning'), _("NTTY did not return any information."))
            return False

        return res

