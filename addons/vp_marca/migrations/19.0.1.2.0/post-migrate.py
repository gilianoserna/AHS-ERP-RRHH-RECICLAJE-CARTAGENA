# -*- coding: utf-8 -*-
# Copyright ASH COLOMBIA SAS. Software propietario.
"""19.0.1.2.0: logotipo de pantalla a 540 px en vez de 180, y cara del asistente.

Como en 19.0.1.1.0 (hallazgo A4), lo que haga el gancho de instalacion tiene
que ocurrir tambien al ACTUALIZAR, porque Odoo solo ejecuta
`post_init_hook` al instalar. Se llama a la misma funcion, no a una copia.
"""
from odoo import SUPERUSER_ID, api

from odoo.addons.vp_marca import refrescar_logo_web, vestir_asistente


def migrate(cr, version):
    if not version:
        return
    env = api.Environment(cr, SUPERUSER_ID, {})
    refrescar_logo_web(env)
    vestir_asistente(env)
