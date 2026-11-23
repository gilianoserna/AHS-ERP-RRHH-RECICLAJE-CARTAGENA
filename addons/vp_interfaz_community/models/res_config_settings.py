# -*- coding: utf-8 -*-
# Copyright ASH COLOMBIA SAS. Software propietario.
"""Los Ajustes sin las opciones de Odoo Enterprise.

Odoo Community marca cada opcion de la edicion de pago con el widget
`upgrade_boolean`: es el que pinta la etiqueta «Enterprise» y, al marcarla,
abre la ventana de «actualice a Enterprise». Aqui se busca ese widget en la
vista YA COMBINADA —con todas las herencias de todos los modulos
instalados— y se oculta lo que lo contiene. Una regla, no una lista: un
modulo que se instale mañana con otra opcion Enterprise tambien queda
oculto.

Se OCULTA, no se borra. Otras partes de la vista pueden nombrar ese campo en
sus condiciones (`invisible="not module_x"`), y quitarlo del arbol las
dejaria apuntando a un campo que no esta.
"""
from odoo import api, models

WIDGET_ENTERPRISE = 'upgrade_boolean'


def ocultar_enterprise(arch):
    """Marca invisible cada opcion Enterprise de una vista de Ajustes.

    * Si el campo Enterprise es el campo principal de su `<setting>` —el
      primero que aparece—, se oculta la opcion entera: etiqueta, ayuda y
      contenido.
    * Si esta anidado en una opcion que no es Enterprise, se ocultan solo el
      campo y su etiqueta.
    * Un bloque que se queda sin ninguna opcion visible se oculta tambien:
      no se deja un titulo sobre un bloque vacio.

    Devuelve cuantas opciones se ocultaron (para las pruebas)."""
    ocultas = 0
    for campo in arch.iter('field'):
        if campo.get('widget') != WIDGET_ENTERPRISE:
            continue
        opcion = next((a for a in campo.iterancestors() if a.tag == 'setting'), None)
        principal = opcion is not None and next(opcion.iter('field'), None) is campo
        if principal:
            opcion.set('invisible', '1')
        else:
            campo.set('invisible', '1')
            contenedor = campo.getparent()
            for etiqueta in contenedor.iter('label'):
                if etiqueta.get('for') == campo.get('name'):
                    etiqueta.set('invisible', '1')
        ocultas += 1
    for bloque in arch.iter('block'):
        opciones = [o for o in bloque.iter('setting')]
        if opciones and all(o.get('invisible') == '1' for o in opciones):
            bloque.set('invisible', '1')
    return ocultas


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    @api.model
    def _get_view(self, view_id=None, view_type='form', **options):
        arch, view = super()._get_view(view_id, view_type, **options)
        if view_type == 'form':
            ocultar_enterprise(arch)
        return arch, view
