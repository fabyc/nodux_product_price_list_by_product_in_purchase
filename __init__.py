#This file is part of Tryton.  The COPYRIGHT file at the top level of
#this repository contains the full copyright notices and license terms.#This file is part of Tryton.  The COPYRIGHT file at the top level of
#this repository contains the full copyright notices and license terms.
from trytond.pool import Pool
from .purchase import *

def register():
    Pool.register(
        PurchaseLine,
        AddListPrice,
        module='nodux_product_price_list_by_product_in_purchase', type_='model')
    Pool.register(
        WizardAddListPrice,
        module='nodux_product_price_list_by_product_in_purchase', type_='wizard')
