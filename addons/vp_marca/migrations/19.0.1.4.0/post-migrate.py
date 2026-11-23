# -*- coding: utf-8 -*-
# Copyright ASH COLOMBIA SAS. Software propietario.
"""19.0.1.4.0: pantalla de acceso con la cara de CONECTASH y «¿Olvidaste tu
contraseña?» encendido. Lo que hace el gancho de instalacion tiene que ocurrir
tambien al ACTUALIZAR: se llama a la misma funcion, no a una copia."""
from odoo import SUPERUSER_ID, api

from odoo.addons.vp_marca import activar_recuperar_clave


def migrate(cr, version):
    if not version:
        return
    env = api.Environment(cr, SUPERUSER_ID, {})
    activar_recuperar_clave(env)
