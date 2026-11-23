# -*- coding: utf-8 -*-
from datetime import timedelta

from odoo import _, fields, models
from odoo.exceptions import UserError


class AshTurnoGenerar(models.TransientModel):
    _name = 'ash.turno.generar'
    _description = 'Generar programación de turnos'

    employee_ids = fields.Many2many('hr.employee', string='Empleados', required=True)
    rotacion_id = fields.Many2one('ash.turno.rotacion', string='Rotación', required=True)
    fecha_desde = fields.Date(required=True)
    fecha_hasta = fields.Date(required=True)
    desfase_por_empleado = fields.Integer(
        'Desfase por empleado (días)', default=0,
        help='Corre el ciclo N días por cada empleado para que no descansen todos el mismo día.')
    reemplazar_borradores = fields.Boolean(default=True,
                                           help='Borra los turnos en borrador del rango antes de generar.')

    def action_generar(self):
        self.ensure_one()
        if self.fecha_hasta < self.fecha_desde:
            raise UserError(_('La fecha final es anterior a la inicial.'))
        if (self.fecha_hasta - self.fecha_desde).days > 93:
            raise UserError(_('Genere como máximo tres meses a la vez.'))
        Asignacion = self.env['ash.turno.asignacion']
        if self.reemplazar_borradores:
            Asignacion.search([('employee_id', 'in', self.employee_ids.ids), ('estado', '=', 'borrador'),
                               ('fecha', '>=', self.fecha_desde), ('fecha', '<=', self.fecha_hasta)]).unlink()
        valores = []
        for n, empleado in enumerate(self.employee_ids):
            dia = self.fecha_desde
            while dia <= self.fecha_hasta:
                indice = (dia - self.fecha_desde).days + n * self.desfase_por_empleado
                plantilla = self.rotacion_id.plantilla_del_dia(indice)
                if plantilla:
                    valores.append({'employee_id': empleado.id, 'fecha': dia, 'plantilla_id': plantilla.id})
                dia += timedelta(days=1)
        creadas = Asignacion.create(valores)
        return {
            'type': 'ir.actions.act_window', 'name': _('Turnos generados'),
            'res_model': 'ash.turno.asignacion', 'view_mode': 'list,calendar,form',
            'domain': [('id', 'in', creadas.ids)],
        }
