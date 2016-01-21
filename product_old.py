from openerp.exceptions import except_orm
from openerp.osv import osv,fields
import openerp.addons.decimal_precision as dp
import logging
#Get the logger
_logger = logging.getLogger(__name__)


USER_AGENT = 'OpenAnything/1.0 +http://diveintopython.org/http_web_services/'

class product_attribute_value(osv.osv):
    _inherit = "product.attribute.value"

    def _get_price_extra(self, cr, uid, ids, name, args, context=None):
        result = dict.fromkeys(ids, 0)
        if not context.get('active_id'):
            return result

        for obj in self.browse(cr, uid, ids, context=context):
            for price_id in obj.price_ids:
                if price_id.product_tmpl_id.id == context.get('active_id'):
                    result[obj.id] = price_id.price_extra
                    break
        return result


    def _set_price_extra(self, cr, uid, id, name, value, args, context=None):
        if context is None:
            context = {}
        if 'active_id' not in context:
            return None
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

    _columns = {
        'price_extra': fields.function(_get_price_extra, type='float', string='Attribute Price Extra',
            # fnct_inv=_set_price_extra,
            digits_compute=dp.get_precision('Product Price'),
            help="Price Extra: Extra price for the variant with this attribute value on sale price. eg. 200 price extra, 1000 + 200 = 1200."),
	}

product_attribute_value()
