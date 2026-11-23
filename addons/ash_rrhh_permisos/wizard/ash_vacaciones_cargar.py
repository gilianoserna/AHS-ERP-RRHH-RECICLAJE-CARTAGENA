# -*- coding: utf-8 -*-
from odoo import _, api, fields, models
from odoo.exceptions import UserError


class AshVacacionesCargar(models.TransientModel):
    _name = 'ash.vacaciones.cargar'
    _description = 'Arranque del control de vacaciones'

    fecha_corte = fields.Date('Fecha de corte', required=True, default=fields.Date.context_today,
                              help='Desde esta fecha el ERP causa 1,25 días por mes. El saldo inicial '
                                   'son los días pendientes a esta fecha.')
    linea_ids = fields.One2many('ash.vacaciones.cargar.linea', 'asistente_id', string='Empleados')

    def action_agregar_sin_causacion(self):
        """Trae los empleados activos que aún no tienen causación de vacaciones."""
        self.ensure_one()
        plan = self.env.ref('ash_rrhh_permisos.plan_vacaciones_co')
        con_plan = self.env['hr.leave.allocation'].search(
            [('accrual_plan_id', '=', plan.id), ('state', '=', 'validate')]).employee_id
        ya = self.linea_ids.employee_id
        faltan = self.env['hr.employee'].search([('id', 'not in', (con_plan | ya).ids),
                                                 ('company_id', 'in', self.env.companies.ids)])
        self.write({'linea_ids': [(0, 0, {'employee_id': e.id}) for e in faltan]})
        return {'type': 'ir.actions.act_window', 'res_model': self._name, 'res_id': self.id,
                'view_mode': 'form', 'target': 'new'}

    def action_cargar(self):
        self.ensure_one()
        if not self.linea_ids:
            raise UserError(_('Agregue al menos un empleado.'))
        plan = self.env.ref('ash_rrhh_permisos.plan_vacaciones_co')
        tipo = plan.time_off_type_id
        Asignacion = self.env['hr.leave.allocation']
        creadas = Asignacion
        for linea in self.linea_ids:
            if linea.saldo_inicial > 0:
                creadas |= Asignacion.create({
                    'name': _('Saldo inicial de vacaciones al %s', self.fecha_corte),
                    'employee_id': linea.employee_id.id, 'holiday_status_id': tipo.id,
                    'allocation_type': 'regular', 'number_of_days': linea.saldo_inicial,
                    'date_from': self.fecha_corte})
            creadas |= Asignacion.create({
                'name': _('Causación de vacaciones desde %s', self.fecha_corte),
                'employee_id': linea.employee_id.id, 'holiday_status_id': tipo.id,
                'allocation_type': 'accrual', 'accrual_plan_id': plan.id,
                'number_of_days': 0, 'date_from': self.fecha_corte})
        creadas.filtered(lambda a: a.state != 'validate').action_approve()
        return {'type': 'ir.actions.act_window', 'name': _('Asignaciones de vacaciones'),
                'res_model': 'hr.leave.allocation', 'view_mode': 'list,form',
                'domain': [('id', 'in', creadas.ids)]}


class AshVacacionesCargarLinea(models.TransientModel):
    _name = 'ash.vacaciones.cargar.linea'
    _description = 'Empleado a cargar en el control de vacaciones'

    asistente_id = fields.Many2one('ash.vacaciones.cargar', required=True, ondelete='cascade')
    employee_id = fields.Many2one('hr.employee', string='Empleado', required=True)
    saldo_inicial = fields.Float('Días pendientes', digits=(16, 2),
                                 help='Días hábiles de vacaciones pendientes a la fecha de corte.')

    @api.constrains('saldo_inicial')
    def _check_saldo(self):
        if any(l.saldo_inicial < 0 for l in self):
            raise UserError(_('El saldo inicial no puede ser negativo.'))
