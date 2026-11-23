# -*- coding: utf-8 -*-
# Copyright ASH COLOMBIA SAS. Software propietario.
"""El logotipo que trae una compañía recién creada es el de ASH ERP.

EL HUECO QUE CIERRA
===================
`res.company.logo` tiene un valor por defecto en el motor
(`base/models/res_company.py:41-43`): **el logotipo de Odoo**. Una compañía
nueva nace con él, y ese logotipo sale en la pantalla de acceso y en cualquier
documento impreso hasta que alguien suba el suyo. Era la mención más visible
del motor en todo el producto, y la que DEC-020 no había cubierto porque no
está en ninguna plantilla: es un dato.

QUE SE HACE, Y QUE NO
=====================
Se cambia el **valor por defecto**, no el dato de nadie. Una compañía que ya
subió su logotipo conserva el suyo: aquí no se escribe nada sobre ella.

`uses_default_logo` sigue funcionando sin tocarlo, porque el motor lo calcula
comparando contra `_get_logo()` (`res_company.py:175-178`): al cambiar el
defecto, la comparación se hace contra el nuestro sola.

POR QUE EL LOGOTIPO DE ASH Y NO UNO NEUTRO
==========================================
Es el logotipo del **producto**, y aparece hasta que el cliente sube el
**suyo**, que es lo que de verdad debe ir en sus facturas. Poner una imagen
vacía dejaría documentos sin nada; dejar la de Odoo es justo lo que se está
corrigiendo. El motor ya ofrece `uses_default_logo` para que la interfaz
invite a subir el propio, y ese aviso se conserva intacto.
"""
import base64

from odoo import api, fields, models
from odoo.tools import file_open
from odoo.tools.image import image_process

# El logotipo que se ve en la pantalla de acceso y en la barra superior es
# `logo_web`, una copia reducida que el motor calcula a 180 px de ancho
# (`base/models/res_company.py:172`). En una pantalla de alta densidad eso
# se ve borroso, y el Product Owner lo noto: «no quedo tan detallado». Se
# calcula a 540 px (3x) y el navegador lo muestra al tamaño que toque.
# `image_process` solo reduce: un logotipo mas pequeño se queda como esta.
ANCHO_LOGO_WEB = 540


class ResCompany(models.Model):
    _inherit = 'res.company'

    # HAY QUE REDECLARAR EL DEFECTO, Y NO ES REDUNDANTE.
    #
    # El motor declara `logo = fields.Binary(..., default=_get_logo, ...)`
    # (`base/models/res_company.py:62`). Ese `default` guarda la FUNCION del
    # modulo base tal como estaba al definir la clase: sobrescribir
    # `_get_logo` mas abajo no la cambia, porque el campo no la busca por
    # nombre en tiempo de ejecucion.
    #
    # Comprobado, y por eso esta escrito aqui: con solo el metodo
    # sobrescrito, una compañia nueva seguia naciendo con el logotipo de
    # Odoo, y ademas `uses_default_logo` se volvia False —el motor si llama
    # a `_get_logo()` para esa comparacion— de modo que la interfaz dejaba
    # de invitar al cliente a subir el suyo. El cambio parecia hecho y no
    # hacia nada.
    #
    # Con el `lambda` la busqueda es en tiempo de ejecucion y si respeta la
    # herencia. Solo se redeclara `default`; el resto de atributos del campo
    # —`related`, `string`, `readonly`— los conserva Odoo al fusionar la
    # definicion heredada.
    logo = fields.Binary(default=lambda self: self._get_logo())

    def _get_logo(self):
        with file_open('vp_marca/static/src/img/ash_erp_logo.png', 'rb') as archivo:
            return base64.b64encode(archivo.read())

    @api.depends('partner_id.image_1920')
    def _compute_logo_web(self):
        for company in self:
            img = company.partner_id.image_1920
            company.logo_web = img and base64.b64encode(
                image_process(base64.b64decode(img), size=(ANCHO_LOGO_WEB, 0)))
