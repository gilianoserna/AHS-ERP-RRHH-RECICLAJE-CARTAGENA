# -*- coding: utf-8 -*-
from odoo import fields, models

TIPOS_DOCUMENTO = [('CC', 'Cédula de ciudadanía'), ('CE', 'Cédula de extranjería'),
                   ('TI', 'Tarjeta de identidad'), ('PA', 'Pasaporte'),
                   ('PEP', 'Permiso especial de permanencia'),
                   ('PPT', 'Permiso por protección temporal'), ('NIT', 'NIT')]


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    ash_tipo_documento = fields.Selection(TIPOS_DOCUMENTO, string='Tipo de documento',
                                          default='CC', groups='hr.group_hr_user')
    ash_numero_documento = fields.Char('Número de documento', index=True, groups='hr.group_hr_user')
    ash_eps = fields.Char('EPS', groups='hr.group_hr_user')
    ash_afp = fields.Char('Fondo de pensiones', groups='hr.group_hr_user')
    ash_arl = fields.Char('ARL', groups='hr.group_hr_user')
    ash_caja_compensacion = fields.Char('Caja de compensación', groups='hr.group_hr_user')
    ash_fondo_cesantias = fields.Char('Fondo de cesantías', groups='hr.group_hr_user')
    ash_centro_costo = fields.Char('Centro de costo', groups='hr.group_hr_user',
                                   help='Tal como viene de Alegra. Solo informativo: aquí no hay contabilidad.')
    ash_fecha_ingreso = fields.Date('Fecha de ingreso', groups='hr.group_hr_user')
    ash_fecha_retiro = fields.Date('Fecha de retiro', groups='hr.group_hr_user')
    ash_id_alegra = fields.Char('ID en Alegra', index=True, copy=False, groups='hr.group_hr_user',
                                help='Identificador del empleado en la nómina de Alegra.')
    ash_huella_alegra = fields.Char(copy=False, groups='base.group_system',
                                    help='Huella de la última versión leída de Alegra (evita escrituras sin cambios).')
    ash_sincronizado_el = fields.Datetime('Última sincronización', copy=False, readonly=True,
                                          groups='hr.group_hr_user')

    _ash_documento_unico = models.Constraint(
        'UNIQUE(company_id, ash_tipo_documento, ash_numero_documento)',
        'Ya existe un empleado con ese documento en la compañía.')
    _ash_id_alegra_unico = models.Constraint(
        'UNIQUE(company_id, ash_id_alegra)',
        'Ya existe un empleado enlazado a ese ID de Alegra en la compañía.')
