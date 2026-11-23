# -*- coding: utf-8 -*-
from odoo import api, fields, models

CLAVES = [
    ('inicio_nocturno', 'Inicio de la jornada nocturna (hora, p. ej. 19.0)'),
    ('fin_nocturno', 'Fin de la jornada nocturna (hora, p. ej. 6.0)'),
    ('jornada_max_semanal', 'Jornada máxima semanal (horas)'),
    ('max_extra_diaria', 'Máximo de horas extra por día'),
    ('max_extra_semanal', 'Máximo de horas extra por semana'),
    ('descanso_minimo_horas', 'Descanso mínimo entre turnos (horas, política interna)'),
    ('tolerancia_tardanza_min', 'Tolerancia de llegada tarde (minutos, política interna)'),
]


class AshRrhhParametro(models.Model):
    _name = 'ash.rrhh.parametro'
    _description = 'Parámetro laboral con vigencia'
    _order = 'clave, vigente_desde desc'

    clave = fields.Selection(CLAVES, required=True)
    valor = fields.Float(required=True, digits=(16, 2))
    vigente_desde = fields.Date(required=True)
    company_id = fields.Many2one('res.company', string='Compañía',
                                 help='Vacío = aplica a todas las compañías.')
    fuente = fields.Char(help='Norma o decisión que lo respalda.')

    _ash_parametro_unico = models.Constraint(
        'UNIQUE(clave, vigente_desde, company_id)',
        'Ya hay un valor para ese parámetro con esa fecha de vigencia.')

    @api.model
    def valor_en(self, clave, fecha, company=None, defecto=None):
        """Valor vigente en `fecha`: el de la compañía si existe, si no el general."""
        company = company or self.env.company
        for dominio_compania in ([('company_id', '=', company.id)], [('company_id', '=', False)]):
            registro = self.sudo().search([('clave', '=', clave), ('vigente_desde', '<=', fecha)]
                                          + dominio_compania, order='vigente_desde desc', limit=1)
            if registro:
                return registro.valor
        return defecto
