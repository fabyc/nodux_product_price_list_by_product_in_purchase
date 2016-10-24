#This file is part of Tryton.  The COPYRIGHT file at the top level of
#this repository contains the full copyright notices and license terms.
import datetime
from itertools import chain
from decimal import Decimal
from sql import Table, Literal
from sql.functions import Overlay, Position
from sql.aggregate import Count
from sql.operators import Concat

from trytond.model import Workflow, ModelView, ModelSQL, fields
from trytond.modules.company import CompanyReport
from trytond.wizard import Wizard, StateAction, StateView, StateTransition, \
    Button
from trytond import backend
from trytond.pyson import Eval, Bool, If, PYSONEncoder, Id
from trytond.transaction import Transaction
from trytond.pool import Pool, PoolMeta

__all__ = ['PurchaseLine', 'AddListPrice', 'WizardAddListPrice']
__metaclass__ = PoolMeta


class PurchaseLine():
    __name__ = 'purchase.line'

    @classmethod
    def __setup__(cls):
        super(PurchaseLine, cls).__setup__()

        cls._buttons.update({
                'wizard_add_list_price': {
                    'invisible': ~Eval('product', [0])
                },
                'update_price': {
                    'invisible': ~Eval('product', [0])
                },
        })

    @classmethod
    @ModelView.button_action('nodux_product_price_list_by_product_in_purchase.wizard_add_list_price')
    def wizard_add_list_price(cls, sales):
        pass

    @classmethod
    @ModelView.button
    def update_price(cls, lines):
        for line in lines:
            line.update_list_price()

    def update_list_price(self):
        pool = Pool()
        Taxes1 = pool.get('product.category-customer-account.tax')
        Taxes2 = pool.get('product.template-customer-account.tax')
        PriceList = pool.get('product.price_list')
        User = pool.get('res.user')

        percentage = 0
        precio_final = Decimal(0.0)
        user =  User(Transaction().user)
        precio_total = Decimal(0.0)
        precio_total_iva = Decimal(0.0)
        iva = Decimal(0.0)
        precio_para_venta = Decimal(0.0)

        if self.product.template.taxes_category == True:
            if self.product.template.category.taxes_parent == True:
                taxes1= Taxes1.search([('category','=', self.product.template.category.parent)])
                taxes2 = Taxes2.search([('product','=', self.product.template.id)])
            else:
                taxes1= Taxes1.search([('category','=', self.product.template.category)])
        else:
            taxes1= Taxes1.search([('category','=', self.product.template.category)])
            taxes2 = Taxes2.search([('product','=', self.product.template.id)])

        if self.product and self.unit_price:
            for line_listas in self.product.listas_precios:
                for line in line_listas.lista_precio.lines:
                    if line.percentage > 0:
                        percentage = line.percentage/100
                    use_new_formula = line.use_new_formula

                if use_new_formula == True:
                    if line_listas.lista_precio.definir_precio_tarjeta == True:
                        precio_final = precio_para_venta / (1 - percentage)
                    else:
                        precio_final = self.unit_price / (1 - percentage)
                else:
                    if line_listas.lista_precio.definir_precio_tarjeta == True:
                        precio_final = precio_para_venta * (1 + percentage)
                    else:
                        precio_final = self.unit_price * (1 + percentage)

                if taxes1:
                    for t in taxes1:
                        iva = precio_final * t.tax.rate
                elif taxes2:
                    for t in taxes2:
                        iva = precio_final * t.tax.rate

                precio_total = precio_final + iva

                line_listas.fijo = Decimal(str(round(precio_final, 6)))
                line_listas.fijo_con_iva = Decimal(str(round(precio_total, 6)))
                line_listas.save()

                if line_listas.lista_precio.definir_precio_venta == True:
                    precio_para_venta = precio_final
                    precio_total_iva = precio_total
                    self.product.template.list_price = Decimal(str(round(precio_para_venta, 6)))
                    self.product.template.save()


class AddListPrice(ModelView):
    'Add List Price'
    __name__ = 'nodux_product_price_list_by_product_in_purchase.add_price_list_form'

    listas_precios = fields.One2Many('product.list_by_product', 'template', 'Listas de precio')

class WizardAddListPrice(Wizard):
    'Wizard Add Term'
    __name__ = 'nodux_product_price_list_by_product_in_purchase.add_price_list'
    start = StateView('nodux_product_price_list_by_product_in_purchase.add_price_list_form',
        'product.template_view_form', [
            Button('Cancel', 'end', 'tryton-cancel'),
            Button('Update', 'update_', 'tryton-ok'),
        ])
    update_ = StateTransition()

    """
    def default_start(self, fields):

        default = {}
        default['listas_precios'] = {}
        pool = Pool()
        Line = pool.get('purchase.line')
        line = Line(Transaction().context['active_id'])
        product = line.product

        for lista in product.listas_precios:
            lista_precio = {
                'template': lista.template.id,
                'lista_precio': lista.lista_precio.id,
                'fijo': lista.fijo,
                'precio_venta': lista.precio_venta,
                'product': lista.product.id,
                'fijo_con_iva': lista.fijo_con_iva,
            }

            default['listas_precios'].setdefault('add', []).append((0, lista_precio))

        return default
        """
