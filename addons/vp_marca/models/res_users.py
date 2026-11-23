# -*- coding: utf-8 -*-
# Copyright ASH COLOMBIA SAS. Software propietario.
from odoo import api, models
from odoo.tools import formataddr

# URL de la imagen de firma que se anexa a los correos de la cuenta (avisos
# de seguridad y restablecer contraseña). Vacio: sin firma.
PARAM_FIRMA = 'vp_marca.firma_correo_cuenta'


def _remitente_cuenta(compania):
    """«ASH COLOMBIA S.A.S <notificaciones@...>»: el remitente por defecto del
    dominio de alias de la compañia. None si no tiene dominio de alias."""
    desde = compania.default_from_email
    return formataddr((compania.name, desde)) if desde else None


def _con_firma(env, cuerpo):
    url = env['ir.config_parameter'].sudo().get_param(PARAM_FIRMA)
    if not url or 'vp-firma' in str(cuerpo or ''):
        return cuerpo
    return '%s<div class="vp-firma" style="margin-top:24px"><img src="%s" alt="Firma" width="480" ' \
           'style="width:480px;max-width:100%%;height:auto;display:block;border:0"/></div>' % (cuerpo or '', url)


class ResUsers(models.Model):
    _inherit = 'res.users'

    def _notify_security_setting_update(self, subject, content, mail_values=None, **kwargs):
        """Los avisos de seguridad de la cuenta (dispositivo nuevo, clave o
        correo cambiados) salen del remitente de notificaciones, no del
        correo de la compañia.

        El motor fija `email_from` al correo de la compañia
        (`mail/models/res_users.py`, `_notify_security_setting_update`), y en
        ASH ese es ventas@: el PO recibio «Nueva conexión a tu cuenta» desde
        ventas (2026-11-11). Se usa el «remitente por defecto» del dominio de
        alias de la compañia (Ajustes → Dominio de alias), que en produccion
        es notificaciones@. Sin dominio de alias, queda lo del motor."""
        self = self.with_context(vp_correo_cuenta=True)
        if mail_values and mail_values.get('email_from'):
            correos = super(ResUsers, self)._notify_security_setting_update(subject, content, mail_values=mail_values, **kwargs)
        else:
            correos = self.env['mail.mail']
            for user in self:
                valores = dict(mail_values or {})
                desde = _remitente_cuenta(user.company_id)
                if desde:
                    valores['email_from'] = desde
                correos |= super(ResUsers, user)._notify_security_setting_update(
                    subject, content, mail_values=valores, **kwargs)
        return correos

    def _action_reset_password(self, signup_type="reset"):
        """El correo de restablecer contraseña no es una plantilla en Odoo 19:
        el motor lo arma y fija `email_from` al correo de la compañia
        (`auth_signup/models/res_users.py`). Se marca el contexto para que
        `mail.mail.create` lo pase al remitente de notificaciones."""
        return super(ResUsers, self.with_context(vp_correo_cuenta=True))._action_reset_password(signup_type=signup_type)


class MailMail(models.Model):
    _inherit = 'mail.mail'

    @api.model_create_multi
    def create(self, vals_list):
        if self.env.context.get('vp_correo_cuenta'):
            companias = self.env['res.company'].sudo().search([])
            por_correo = {c.email_formatted: c for c in companias if c.email_formatted}
            for vals in vals_list:
                compania = por_correo.get(vals.get('email_from'))
                desde = compania and _remitente_cuenta(compania)
                if desde:
                    vals['email_from'] = desde
                    if vals.get('body_html'):
                        vals['body_html'] = _con_firma(self.env, vals['body_html'])
        return super().create(vals_list)
