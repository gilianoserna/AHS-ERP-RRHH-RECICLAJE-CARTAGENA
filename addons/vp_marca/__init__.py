# -*- coding: utf-8 -*-
# Copyright ASH COLOMBIA SAS. Software propietario.
import base64
import logging

from odoo.tools import file_open

from . import controllers
from . import models

_log = logging.getLogger(__name__)

LOGO_ODOO = 'base/static/img/res_company_logo.png'
LOGO_ASH = 'vp_marca/static/src/img/ash_erp_logo.png'


def _leer(ruta):
    with file_open(ruta, 'rb') as archivo:
        return base64.b64encode(archivo.read())


def post_init_hook(env):
    """Releva el logotipo de Odoo en las compañías que NUNCA eligieron uno.

    Cambiar el valor por defecto (`models/res_company.py`) solo alcanza a las
    compañías que se creen a partir de ahora. Las que ya existen nacieron con
    el logotipo del motor guardado, así que seguirían enseñándolo en la
    pantalla de acceso y en sus documentos después de instalar la marca.

    La sustitución es DELIBERADAMENTE estrecha: solo se toca la compañía cuyo
    logotipo es, byte a byte, el que trae el motor por defecto. Quien haya
    subido el suyo —aunque sea parecido— no se toca. Un cliente que descubra
    que una actualización le cambió el logotipo de sus facturas tiene razón
    en enfadarse, así que la única sustitución aceptable es la de un valor
    que nadie eligió.
    """
    odoo_logo, ash_logo = _leer(LOGO_ODOO), _leer(LOGO_ASH)
    companias = env['res.company'].sudo().search([])
    relevadas = companias.filtered(lambda c: c.logo == odoo_logo)
    if relevadas:
        relevadas.write({'logo': ash_logo})
        _log.info('vp_marca: logotipo del motor relevado en %s compañia(s): %s',
                  len(relevadas), ', '.join(relevadas.mapped('name')))
    else:
        _log.info('vp_marca: ninguna compañia traia el logotipo del motor')
    refrescar_logo_web(env)
    vestir_asistente(env)
    activar_recuperar_clave(env)


def activar_recuperar_clave(env):
    """Enciende «¿Olvidaste tu contraseña?» en la pantalla de acceso.

    Odoo lo trae apagado (`auth_signup.reset_password`), y sin el la unica
    salida de quien olvida la clave es escribirle al administrador. El enlace
    manda un correo con un enlace de un solo uso; la verificacion en dos pasos
    se sigue pidiendo despues. Necesita el correo saliente configurado.

    No toca el registro abierto (`auth_signup.invitation_scope`): esa es
    decision de cada empresa, en Ajustes → Permisos."""
    env['ir.config_parameter'].sudo().set_param('auth_signup.reset_password', 'True')
    _log.info('vp_marca: recuperar contraseña activado en la pantalla de acceso')


AVATAR_ASH = 'vp_marca/static/description/icon.png'


def vestir_asistente(env):
    """Nombre y cara del asistente del sistema: «Asistente ASH» con el
    simbolo de ASH ERP, en vez de «OdooBot» con el logotipo del motor.

    POR QUE UNA FUNCION Y NO SOLO EL ARCHIVO DE DATOS. El identificador
    `base.partner_root` queda marcado `noupdate` por el modulo de correo
    (`mail/data/res_partner_data.xml` lo declara en `<data noupdate="1">`).
    En una ACTUALIZACION, Odoo se salta ese registro diga lo que diga nuestro
    archivo: el nombre llego porque se cargo al INSTALAR, pero una cara
    añadida despues nunca habria llegado a las bases existentes. Lo detecto
    la prueba. Esta funcion la llaman el gancho de instalacion y la
    migracion 19.0.1.2.0."""
    asistente = env.ref('base.partner_root').sudo()
    asistente.write({'name': 'Asistente ASH', 'image_1920': _leer(AVATAR_ASH)})
    _log.info('vp_marca: asistente del sistema con nombre y cara de ASH ERP')


def refrescar_logo_web(env):
    """`logo_web` es un campo almacenado: cambiar como se calcula no cambia
    lo que ya esta guardado. Se recalcula en TODAS las compañias —tambien las
    que tienen su propio logotipo, que tambien merece verse nitido—. No
    cambia ningun logotipo: solo su copia para pantalla."""
    companias = env['res.company'].sudo().search([])
    companias._compute_logo_web()
    _log.info('vp_marca: logotipo de pantalla recalculado en %s compañia(s)', len(companias))
