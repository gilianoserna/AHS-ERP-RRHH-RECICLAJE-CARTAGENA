# -*- coding: utf-8 -*-
from datetime import datetime, time, timedelta
from zoneinfo import ZoneInfo

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

from ..lib import jornada

ZONA_POR_DEFECTO = 'America/Bogota'


def a_utc(fecha_local, zona):
    """datetime local ingenuo -> datetime UTC ingenuo (como lo guarda Odoo)."""
    return fecha_local.replace(tzinfo=ZoneInfo(zona)).astimezone(ZoneInfo('UTC')).replace(tzinfo=None)


def a_local(fecha_utc, zona):
    return fecha_utc.replace(tzinfo=ZoneInfo('UTC')).astimezone(ZoneInfo(zona)).replace(tzinfo=None)


class AshTurnoPlantilla(models.Model):
    _name = 'ash.turno.plantilla'
    _description = 'Plantilla de turno'
    _order = 'hora_inicio, name'

    name = fields.Char('Turno', required=True)
    codigo = fields.Char(required=True, size=8, help='Abreviatura que se ve en la grilla (M, T, N…).')
    hora_inicio = fields.Float(required=True, help='Hora local. 22.5 = 10:30 p. m.')
    hora_fin = fields.Float(required=True, help='Si es menor que el inicio, el turno termina al día siguiente.')
    descanso_minutos = fields.Integer('Descanso (min)', default=0,
                                      help='Pausa no remunerada dentro del turno (almuerzo).')
    duracion_horas = fields.Float(compute='_compute_duracion', store=True)
    color = fields.Integer()
    active = fields.Boolean(default=True)
    company_id = fields.Many2one('res.company', default=lambda s: s.env.company)

    @api.depends('hora_inicio', 'hora_fin', 'descanso_minutos')
    def _compute_duracion(self):
        for p in self:
            fin = p.hora_fin if p.hora_fin > p.hora_inicio else p.hora_fin + 24
            p.duracion_horas = max(fin - p.hora_inicio - p.descanso_minutos / 60.0, 0)

    @api.constrains('hora_inicio', 'hora_fin')
    def _check_horas(self):
        for p in self:
            if not (0 <= p.hora_inicio < 24 and 0 <= p.hora_fin <= 24) or p.hora_inicio == p.hora_fin:
                raise ValidationError(_('Horas de turno inválidas en «%s».', p.name))

    def intervalo_local(self, fecha):
        self.ensure_one()
        inicio = jornada.combinar(fecha, self.hora_inicio)
        fin_dec = self.hora_fin if self.hora_fin > self.hora_inicio else self.hora_fin + 24
        return inicio, jornada.combinar(fecha, fin_dec)


class AshTurnoRotacion(models.Model):
    _name = 'ash.turno.rotacion'
    _description = 'Rotación de turnos'

    name = fields.Char(required=True)
    linea_ids = fields.One2many('ash.turno.rotacion.linea', 'rotacion_id', string='Días del ciclo')
    dias_ciclo = fields.Integer(compute='_compute_dias_ciclo')
    company_id = fields.Many2one('res.company', default=lambda s: s.env.company)

    @api.depends('linea_ids')
    def _compute_dias_ciclo(self):
        for r in self:
            r.dias_ciclo = len(r.linea_ids)

    def plantilla_del_dia(self, indice):
        """Plantilla para el día `indice` (desde 0) del ciclo; vacío = descanso."""
        self.ensure_one()
        lineas = self.linea_ids.sorted('secuencia')
        if not lineas:
            return self.env['ash.turno.plantilla']
        return lineas[indice % len(lineas)].plantilla_id


class AshTurnoRotacionLinea(models.Model):
    _name = 'ash.turno.rotacion.linea'
    _description = 'Día de una rotación'
    _order = 'secuencia, id'

    rotacion_id = fields.Many2one('ash.turno.rotacion', required=True, ondelete='cascade')
    secuencia = fields.Integer(default=10)
    plantilla_id = fields.Many2one('ash.turno.plantilla', string='Turno',
                                   help='Vacío = día de descanso.')


class AshTurnoAsignacion(models.Model):
    _name = 'ash.turno.asignacion'
    _description = 'Turno asignado'
    _inherit = ['mail.thread']
    _order = 'inicio desc'

    employee_id = fields.Many2one('hr.employee', string='Empleado', required=True, index=True,
                                  tracking=True)
    company_id = fields.Many2one(related='employee_id.company_id', store=True)
    department_id = fields.Many2one(related='employee_id.department_id', store=True)
    fecha = fields.Date(required=True, index=True, tracking=True)
    plantilla_id = fields.Many2one('ash.turno.plantilla', string='Turno', required=True, tracking=True)
    inicio = fields.Datetime(compute='_compute_intervalo', store=True, index=True)
    fin = fields.Datetime(compute='_compute_intervalo', store=True)
    minutos_programados = fields.Integer(compute='_compute_intervalo', store=True)
    estado = fields.Selection([('borrador', 'Borrador'), ('publicado', 'Publicado'),
                               ('cancelado', 'Cancelado')], default='borrador', required=True,
                              tracking=True)
    excede_tope_semanal = fields.Boolean(compute='_compute_excede_tope',
                                         help='La semana (lunes a domingo) supera la jornada máxima.')
    notas = fields.Text()
    color = fields.Integer(related='plantilla_id.color')

    def _zona(self):
        return self.employee_id.tz or self.env.user.tz or ZONA_POR_DEFECTO

    @api.depends('fecha', 'plantilla_id.hora_inicio', 'plantilla_id.hora_fin',
                 'plantilla_id.descanso_minutos', 'employee_id.tz')
    def _compute_intervalo(self):
        for a in self:
            if not (a.fecha and a.plantilla_id):
                a.inicio = a.fin = False
                a.minutos_programados = 0
                continue
            ini, fin = a.plantilla_id.intervalo_local(a.fecha)
            zona = a._zona()
            a.inicio, a.fin = a_utc(ini, zona), a_utc(fin, zona)
            a.minutos_programados = int(a.plantilla_id.duracion_horas * 60)

    def _semana(self):
        lunes = self.fecha - timedelta(days=self.fecha.weekday())
        return lunes, lunes + timedelta(days=6)

    def _compute_excede_tope(self):
        Parametro = self.env['ash.rrhh.parametro']
        for a in self:
            if not a.fecha or not a.employee_id:
                a.excede_tope_semanal = False
                continue
            lunes, domingo = a._semana()
            tope = Parametro.valor_en('jornada_max_semanal', a.fecha, a.company_id, defecto=42)
            semana = self.search([('employee_id', '=', a.employee_id.id), ('estado', '!=', 'cancelado'),
                                  ('fecha', '>=', lunes), ('fecha', '<=', domingo)])
            a.excede_tope_semanal = sum(semana.mapped('minutos_programados')) > tope * 60

    @api.constrains('inicio', 'fin', 'employee_id', 'estado')
    def _check_traslape_y_descanso(self):
        Parametro = self.env['ash.rrhh.parametro']
        for a in self.filtered(lambda r: r.estado != 'cancelado' and r.inicio):
            minimo = Parametro.valor_en('descanso_minimo_horas', a.fecha, a.company_id, defecto=0)
            margen = timedelta(hours=minimo)
            vecinos = self.search([('id', '!=', a.id), ('employee_id', '=', a.employee_id.id),
                                   ('estado', '!=', 'cancelado'),
                                   ('inicio', '<', a.fin + margen), ('fin', '>', a.inicio - margen)])
            for v in vecinos:
                if jornada.traslapan(a.inicio, a.fin, v.inicio, v.fin):
                    raise ValidationError(_('%(emp)s ya tiene el turno %(t)s que se cruza el %(f)s.',
                                            emp=a.employee_id.name, t=v.plantilla_id.name, f=v.fecha))
                raise ValidationError(_('%(emp)s no tendría el descanso mínimo de %(h)s h entre '
                                        'turnos (%(f1)s y %(f2)s).', emp=a.employee_id.name, h=minimo,
                                        f1=v.fecha, f2=a.fecha))

    def action_publicar(self):
        self.filtered(lambda a: a.estado == 'borrador').write({'estado': 'publicado'})

    def action_cancelar(self):
        self.write({'estado': 'cancelado'})

    def action_borrador(self):
        self.filtered(lambda a: a.estado == 'cancelado').write({'estado': 'borrador'})

    @api.model
    def turno_en(self, employee, momento_utc, holgura_horas=3):
        """Turno publicado que contiene `momento_utc` (o empieza cerca de él)."""
        holgura = timedelta(hours=holgura_horas)
        return self.search([('employee_id', '=', employee.id), ('estado', '=', 'publicado'),
                            ('inicio', '<=', momento_utc + holgura), ('fin', '>=', momento_utc)],
                           order='inicio', limit=1)
