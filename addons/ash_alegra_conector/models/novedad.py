# -*- coding: utf-8 -*-
from odoo import _, models
from odoo.exceptions import UserError


class AshNovedadPeriodo(models.Model):
    _inherit = 'ash.novedad.periodo'

    def action_enviar_alegra(self):
        self.ensure_one()
        if self.estado not in ('aprobado', 'enviado'):
            raise UserError(_('Solo se envía a Alegra un periodo aprobado.'))
        conexion = self.env['ash.alegra.conexion'].search([('company_id', '=', self.company_id.id)], limit=1)
        if not conexion:
            raise UserError(_('No hay conexión con Alegra para %s.', self.company_id.name))
        enviados, fallidos = conexion.enviar_periodo(self)
        if not fallidos:
            self.estado = 'enviado'
        self.message_post(body=_('Envío a Alegra (%(modo)s): %(ok)s líneas enviadas, %(err)s con error.',
                                 modo=conexion.modo, ok=enviados, err=fallidos))
        return {'type': 'ir.actions.client', 'tag': 'display_notification', 'params': {
            'type': 'warning' if fallidos else 'success', 'sticky': bool(fallidos),
            'message': _('%(ok)s enviadas, %(err)s con error (vea la columna Error).', ok=enviados, err=fallidos)}}
