# -*- coding: utf-8 -*-
from datetime import time, timedelta

from odoo import api, fields, models

from odoo.addons.ash_rrhh_turnos.lib import jornada
from odoo.addons.ash_rrhh_turnos.models.turno import ZONA_POR_DEFECTO, a_local

CAMPOS_HORAS = {tipo: f'ash_h_{tipo}' for tipo in jornada.TIPOS}


def _hora(decimal):
    horas = int(decimal) % 24
    return time(horas, int(round((decimal - int(decimal)) * 60)) % 60)


class HrAttendance(models.Model):
    _inherit = 'hr.attendance'

    ash_asignacion_id = fields.Many2one('ash.turno.asignacion', string='Turno', compute='_compute_ash',
                                        store=True, index=True)
    ash_sin_turno = fields.Boolean('Sin turno', compute='_compute_ash', store=True)
    ash_minutos_tarde = fields.Integer('Minutos tarde', compute='_compute_ash', store=True)
    ash_h_ordinaria_diurna = fields.Float('Ordinaria diurna', compute='_compute_ash', store=True)
    ash_h_ordinaria_nocturna = fields.Float('Ordinaria nocturna', compute='_compute_ash', store=True)
    ash_h_dominical_diurna = fields.Float('Dominical/festiva diurna', compute='_compute_ash', store=True)
    ash_h_dominical_nocturna = fields.Float('Dominical/festiva nocturna', compute='_compute_ash', store=True)
    ash_h_extra_diurna = fields.Float('Extra diurna', compute='_compute_ash', store=True)
    ash_h_extra_nocturna = fields.Float('Extra nocturna', compute='_compute_ash', store=True)
    ash_h_extra_dominical_diurna = fields.Float('Extra dominical diurna', compute='_compute_ash', store=True)
    ash_h_extra_dominical_nocturna = fields.Float('Extra dominical nocturna', compute='_compute_ash', store=True)

    def _ash_reglas(self, fecha_local, company):
        Parametro = self.env['ash.rrhh.parametro']
        inicio = Parametro.valor_en('inicio_nocturno', fecha_local, company, defecto=19.0)
        fin = Parametro.valor_en('fin_nocturno', fecha_local, company, defecto=6.0)
        festivos = self.env['ash.rrhh.festivo'].conjunto(fecha_local - timedelta(days=1),
                                                         fecha_local + timedelta(days=2), company)
        return jornada.ReglasJornada(inicio_nocturno=_hora(inicio), fin_nocturno=_hora(fin),
                                     festivos=festivos)

    @api.depends('check_in', 'check_out', 'employee_id')
    def _compute_ash(self):
        Asignacion = self.env['ash.turno.asignacion']
        Parametro = self.env['ash.rrhh.parametro']
        for att in self:
            valores = dict.fromkeys(CAMPOS_HORAS.values(), 0.0)
            valores.update(ash_asignacion_id=False, ash_sin_turno=False, ash_minutos_tarde=0)
            if att.check_in and att.employee_id:
                turno = Asignacion.turno_en(att.employee_id, att.check_in)
                valores['ash_asignacion_id'] = turno.id
                valores['ash_sin_turno'] = not turno
                if turno:
                    tolerancia = Parametro.valor_en('tolerancia_tardanza_min', turno.fecha,
                                                    att.employee_id.company_id, defecto=0)
                    tarde = int((att.check_in - turno.inicio).total_seconds() // 60)
                    valores['ash_minutos_tarde'] = tarde if tarde > tolerancia else 0
                if att.check_out and att.check_out > att.check_in:
                    zona = att.employee_id.tz or ZONA_POR_DEFECTO
                    ini, fin = a_local(att.check_in, zona), a_local(att.check_out, zona)
                    reglas = att._ash_reglas(ini.date(), att.employee_id.company_id)
                    programados = turno.minutos_programados if turno else None
                    minutos = jornada.clasificar(ini, fin, reglas, minutos_programados=programados)
                    for tipo, campo in CAMPOS_HORAS.items():
                        valores[campo] = round(minutos[tipo] / 60.0, 2)
            att.update(valores)
