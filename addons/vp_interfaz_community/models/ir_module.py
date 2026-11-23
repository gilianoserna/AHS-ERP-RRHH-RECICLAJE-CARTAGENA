# -*- coding: utf-8 -*-
# Copyright ASH COLOMBIA SAS. Software propietario.
"""Aplicaciones: los modulos de Odoo Enterprise (`to_buy`) no se ofrecen."""
from odoo import api, models

from .solo_community import con_community

COMMUNITY = [('to_buy', '=', False)]


class IrModuleModule(models.Model):
    _inherit = 'ir.module.module'

    @api.model
    def web_search_read(self, domain, specification, offset=0, limit=None, order=None, count_limit=None):
        return super().web_search_read(con_community(domain, COMMUNITY), specification, offset=offset,
                                       limit=limit, order=order, count_limit=count_limit)

    @api.model
    def web_read_group(self, domain, groupby, aggregates=(), limit=None, offset=0, order=None, **kwargs):
        return super().web_read_group(con_community(domain, COMMUNITY), groupby, aggregates, limit,
                                      offset, order, **kwargs)

    @api.model
    def search_panel_select_range(self, field_name, **kwargs):
        """Los contadores del panel de categorias cuentan lo que la lista
        muestra, no los modulos Enterprise que ya no aparecen."""
        if field_name == 'category_id':
            kwargs['search_domain'] = con_community(kwargs.get('search_domain'), COMMUNITY)
        return super().search_panel_select_range(field_name, **kwargs)
