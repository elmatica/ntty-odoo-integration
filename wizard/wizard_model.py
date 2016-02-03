from openerp import models, fields, api, _
from openerp.exceptions import except_orm
from openerp.osv import osv
import urllib2, httplib, urlparse, gzip, requests, json
from StringIO import StringIO
import openerp.addons.decimal_precision as dp
import logging
import ast
#Get the logger
_logger = logging.getLogger(__name__)

class wizard_ntty_product_import_detail(models.TransientModel):
	_name = 'wizard.ntty.product.import.detail'

	import_id = fields.Many2one('wizard.ntty.product.import')
	partner_id = fields.Many2one('res.partner')
	ntty_partner_id = fields.Integer('NTTY Partner ID')
	selected = fields.Selection([('yes','yes'),('no','no')],string="Import",default='no')

class wizard_ntty_product_import(models.TransientModel):
	_name = 'wizard.ntty.product.import'

	@api.one
	def _compute_enable_supplier_button(self):
		return_value = False
		ntty = self.env['ntty.config.settings'].browse(1)
		if not ntty:
			raise osv.except_osv('Error', 'Connection not defined')
			return_value = False
		if ntty and not ntty.ntty_check_supliers:
			return_value = True
               	self.enable_supplier_button = return_value

	ntty_id = fields.Char('NTTY ID')
	detail_ids = fields.One2many(comodel_name='wizard.ntty.product.import.detail',inverse_name='import_id')
	ntty_data = fields.Text('NTTY Data')
	enable_supplier_button = fields.Boolean(string='Enable Supplier Button',default=True,compute=_compute_enable_supplier_button)

	@api.multi
	def create_ntty_products(self):
                ntty_id = self.ntty_id
                if not ntty_id:
                        raise osv.except_osv(('Error'), ('Please enter a NTTY ID'))
                        return None

                ntty = self.env['ntty.config.settings'].browse(1)
                if not ntty:
                        return None
                ntty_service_address = ntty.ntty_service_address
                ntty_service_user_email = ntty.ntty_service_user_email
                ntty_service_token = ntty.ntty_service_token

		ntty_check_supliers = ntty.ntty_check_supliers
		ntty_generate_price_list = ntty.ntty_generate_price_list
		ntty_related_products = ntty.ntty_related_products
		ntty_partner_info = ntty.ntty_partner_info
		ntty_product_category = ntty.ntty_product_category
		ntty_supplier_short_name = ntty.ntty_supplier_short_name

		if len(self.detail_ids) == 0 and ntty_check_supliers:
			raise osv.except_osv(('Error'), ('Please enter a NTTY ID and pull its suppliers'))
                	return None

		identifier = self.ntty_id
		ntty_data = self.ntty_data
		if not ntty_data:

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
		else:
			identifier = self.ntty_id
	        	res = ast.literal_eval(self.ntty_data)
		if not ntty_check_supliers:
			vals_detail = {
				'import_id': self.id,
				'ntty_partner_id': -999,
				'selected': 'yes'
				}
			self.env['wizard.ntty.product.import.detail'].create(vals_detail)
		created_products = []
		for detail in self.detail_ids:
			if detail.selected == 'yes':

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
               	        			#if 'Automotive' in certification['name']:
			                        #        flag_automotive = True
                       				#        category_id = self.env['product.category'].search([('name','=','Automotive')])
		                	        #        if category_id:
                       				#                categ_id = category_id.id
			                        #if 'Defense' in certification['name']:
       	                			#        flag_defense = True
			                        #        category_id = self.env['product.category'].search([('name','=','Defense')])
                       				#        if category_id:
		        	                #                categ_id = category_id.id
						try:
							if certification['certification_type'] == 'Category':
								product_category = self.env['product.category'].search(\
									[('name','=',certification['name'])])
								if product_category and len(product_category) == 1:
									categ_id = product_category.id
						except:
							continue
		   	        # Searches for product_owner
			        product_brand = entity.get('product_owner','')
			        product_brand_text = entity.get('product_owner','')
				lifecycle_blocks_orders = entity.get('lifecycle_blocks_orders',False)
				lifecycle_blocks_quotes = entity.get('lifecycle_blocks_quotes',False)
				lifecycle = entity.get('lifecycle',False)
				product_brand_id = None
				if product_brand:
					product_brand_id = self.env['product.brand'].search([('name','=',product_brand)])
					if product_brand_id:
						product_brand_id = product_brand_id[0].id
					else:
						vals_brand = {
							'name': product_brand
							}
						product_brand_id = self.env['product.brand'].create(vals_brand)
						product_brand_id = product_brand_id.id

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
				vals = {
		                    'name': article_part_name,
                		    'article_part_number': article_part_number,
		                    'description': long_description,
		                    'ntty_id': identifier,
                		    'type': "product",
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
                		    'categ_id': categ_id,
		                    }
			        product_code = ''
		                part_name = ''
		                part_description = ''
				default_code = ''

			        # This is the place
			        # prod = self.env['product.template'].search([('ntty_id', '=', identifier)])
		                for part_number in part_numbers:
			                if part_number['part_organization'] == 'ELMATICA AS':
                        			default_code = part_number.get('part_number','')
			                if part_number['part_organization'] != 'ELMATICA AS'\
						 and part_number['part_organization'] != product_brand_text:
			                        part_name = part_number.get('part_name','')
                        			part_description = part_number.get('part_description','')
			                        product_code = part_number.get('part_number','')
                        			vals['product_code'] = product_code
			        vals['default_code'] = default_code
				if detail.partner_id.short_name and ntty_supplier_short_name and ntty_check_supliers:
				        vals['name'] =  article_part_number + ' ' + product_code + ' ' + detail.partner_id.short_name
				else:
					if detail.partner_id.name:	
					        vals['name'] =  article_part_number + ' ' + product_code + ' ' + detail.partner_id.name 
					else:
					        vals['name'] =  article_part_number + ' ' + product_code 
			        vals['description'] = part_description,
				identifier_odoo = identifier + '#' + str(detail.partner_id.ntty_partner_id)
                                prod = self.env['product.product'].search([('ntty_odoo', '=', identifier_odoo)])
                                vals['ntty_odoo'] = identifier_odoo
                                vals['ntty_id'] = identifier 
				if ntty.ntty_mto:
					routes = self.env['stock.location.route'].search([('name','=','Make To Order')])
					route_ids = []
					if routes:
						for route in routes:
							route_ids.append(route.id)
						vals['route_ids'] = [(6,0,route_ids)]
				if ntty.ntty_sold:
					vals['sale_ok'] = True
				else:
					vals['sale_ok'] = False
				if ntty.ntty_purchased:
					vals['purchase_ok'] = True
				else:
					vals['purchase_ok'] = False


                                if not prod:
                                        prod = prod.create(vals)
                                else:
                                        prod.write(vals)
				created_products.append(prod)
				# Check suppliers setting
				if ntty_check_supliers:
	                                vals_supplier = {
       	                                	'name': detail.partner_id.id,
                                                'company_id': 1,
	                                        'product_tmpl_id': prod.product_tmpl_id.id,
                                                }
	                                prod_sup = self.env['product.supplierinfo'].create(vals_supplier)
				# Creates attributes
				for entity_values_key in entity['values'].keys():
					value = entity['values'][entity_values_key]
					attribute_id = self.env['product.attribute'].search([('name','=',entity_values_key)])
					if attribute_id:
						value_id = self.env['product.attribute.value'].\
							search([('attribute_id','=',attribute_id.id),\
								('name','=',str(value))])
						if not value_id:
							vals_value = {
								'attribute_id': attribute_id.id,
								'name': str(value),
								}
							value_id = self.env['product.attribute.value'].create(vals_value)
							value_id = value_id.id
						else:
							value_id = value_id.id
						vals_attribute_line = {
							'product_tmpl_id': prod.product_tmpl_id.id,
							'attribute_id': attribute_id.id,
							'value_ids': [(6,0,[value_id])]
							}
						attribute_line_id = self.env['product.attribute.line'].\
							create(vals_attribute_line)
		
		for detail in self.detail_ids:
			if detail.selected == 'no' and detail.partner_id:
				prod_sup = self.env['product.supplierinfo'].search([('name','=',detail.partner_id.id)])
				po_sup = self.env['purchase.order'].search([('partner_id','=',detail.partner_id.id)])
				inv_sup = self.env['account.invoice'].search([('partner_id','=',detail.partner_id.id)])
				so_sup = self.env['sale.order'].search(['|',('partner_invoice_id','=',detail.partner_id.id),\
										('partner_id','=',detail.partner_id.id)])
				if not prod_sup and not po_sup and not inv_sup and not so_sup:
					supplier_to_delete = detail.partner_id
					try:
						supplier_to_delete.unlink()
					except:
						pass
			else:
				if detail.ntty_partner_id != -999:
					detail.partner_id.message_post(body="Supplier created. Needs setup", context={})

		if ntty_related_products:
			for prod in created_products:
				related_products = self.env['product.product'].search([('ntty_id','=',self.ntty_id)])
				related = [related_product.product_tmpl_id.id for related_product in related_products \
					if prod.product_tmpl_id.id != related_product.product_tmpl_id.id]
				vals = {
					'alternative_product_ids': [(6,0,related)],
					}
				product_template = prod.product_tmpl_id
				product_template.write(vals)
		return True

	@api.multi
	def pull_ntty_suppliers(self):
		ntty_id = self.ntty_id
		if not ntty_id:
			raise osv.except_osv(('Error'), ('Please enter a NTTY ID'))
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
		self.write({'ntty_data':res})
		if res:
			if not ntty.ntty_check_supliers:
			                return {
	        		                'type': 'ir.actions.act_window',
        	                		'res_model': self._name, # this model
			                        'res_id': self.id, # the current wizard record
			                        'view_type': 'form',
                        			'view_mode': 'form',
			                        'target': 'new'}

			import_id = self.id
			try:
				suppliers = res['entity']['values'].get('supplier_matching',[])
			except:
				suppliers = []
			for supplier in suppliers:
				supplier_id = self.env['res.partner'].search([('ntty_partner_id','=',supplier['id'])])
				if not supplier_id:
					sup_odoo = self.env['res.partner'].create({'supplier': True, \
                                        	'is_company': True, 'name': supplier['name'], 'ntty_partner_id': supplier['id'], \
	                                        'partner_approved': True, 'active': True})
					# sup_odoo.message_post(body="Supplier created. Needs setup", context={})
					supplier_id = sup_odoo.id
				else:	
					if len(supplier_id) > 1:
						supplier_id = supplier_id[0].id
					else:
						supplier_id = supplier_id.id
				vals_sup = {
					'import_id': import_id,
					'partner_id': supplier_id,
					'ntty_partner_id': supplier['id'],
					'selected': 'no',
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


class wizard_ntty_update_lifecycle(models.TransientModel):
	_name = 'wizard.ntty.update.lifecycle'

	@api.multi
	def pull_ntty_lifecycles(self):
		return_value = self.env['product.template']._scheduled_connect_odoo_ntty()
		return True
