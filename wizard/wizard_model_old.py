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


class product_attribute_value(osv.osv):
    _inherit = "product.attribute.value"

    def _set_price_extra(self, cr, uid, id, name, value, args, context=None):
        if context is None:
            context = {}
        if 'active_id' not in context:
            return None
	import pdb;pdb.set_trace()
	if context['active_model'] != 'wizard.ntty.product.import':
	        p_obj = self.pool['product.attribute.price']
	        p_ids = p_obj.search(cr, uid, [('value_id', '=', id), ('product_tmpl_id', '=', context['active_id'])], context=context)
        	if p_ids:
	            p_obj.write(cr, uid, p_ids, {'price_extra': value}, context=context)
        	else:
	            p_obj.create(cr, uid, {
        	            'product_tmpl_id': context['active_id'],
                	    'value_id': id,
	                    'price_extra': value,
        	        }, context=context)
	else:
	        p_obj = self.pool['product.attribute.price']
	        p_obj.create(cr, uid, {
        		'product_tmpl_id': context['active_id'],
                	'value_id': id,
	        	'price_extra': value,
        	        }, context=context)
		
	
product_attribute_value()
