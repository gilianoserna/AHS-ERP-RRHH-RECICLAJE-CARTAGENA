# -*- coding: utf-8 -*-
# Copyright ASH COLOMBIA SAS. Software propietario.
"""El relevo del logotipo también tiene que ocurrir al ACTUALIZAR (hallazgo A4).

`vp_marca 19.0.1.0.0` no tocaba el logotipo de las compañías. La versión
`19.0.1.1.0` lo releva con un `post_init_hook`... y ahí estaba el agujero:
Odoo ejecuta ese gancho **solo al instalar**. En `odoo/modules/loading.py` la
llamada está dentro de `if update_operation == 'install'`; la rama de
`upgrade` no lo invoca.

Consecuencia: una base que ya tuviera `vp_marca` instalado seguía enseñando el
logotipo de Odoo en la pantalla de acceso y en sus documentos impresos después
de actualizar. Justo lo que el cambio venía a corregir, sin corregirse.

La prueba que lo cubría llamaba a `post_init_hook(self.env)` directamente, así
que pasaba sin demostrar que el gancho llegara a ejecutarse en una
actualización real. El defecto lo encontró la auditoría, no la suite.

**Se reutiliza el mismo gancho**, no una copia: si la regla de a quién se
releva cambia, tiene que cambiar en un solo sitio. Y la regla sigue siendo
estrecha: solo la compañía cuyo logotipo es, byte a byte, el que trae el
motor.
"""
import logging

from odoo import SUPERUSER_ID, api

from odoo.addons.vp_marca import post_init_hook

_log = logging.getLogger(__name__)


def migrate(cr, version):
    if not version:
        return
    _log.info('vp_marca: relevo del logotipo en actualizacion (A4)')
    post_init_hook(api.Environment(cr, SUPERUSER_ID, {}))
