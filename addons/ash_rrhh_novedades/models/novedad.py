# -*- coding: utf-8 -*-
import base64
from collections import defaultdict
from datetime import datetime, time

from odoo import _, api, fields, models
from odoo.exceptions import UserError

from odoo.addons.ash_rrhh_asistencia.models.hr_attendance import CAMPOS_HORAS
from ..lib import exportador_alegra

CONCEPTOS = [
    ('extra_diurna', 'Hora extra diurna'),
    ('extra_nocturna', 'Hora extra nocturna'),
    ('extra_dominical_diurna', 'Hora extra dominical/festiva diurna'),
    ('extra_dominical_nocturna', 'Hora extra dominical/festiva nocturna'),
    ('ordinaria_nocturna', 'Recargo nocturno'),
    ('dominical_diurna', 'Recargo dominical/festivo diurno'),
    ('dominical_nocturna', 'Recargo dominical/festivo nocturno'),
    ('vacaciones', 'Vacaciones disfrutadas'),
    ('incapacidad_general', 'Incapacidad enfermedad general'),
    ('incapacidad_laboral', 'Incapacidad accidente/enfermedad laboral'),
    ('licencia_maternidad', 'Licencia de maternidad'),
    ('licencia_paternidad', 'Licencia de paternidad'),
    ('licencia_remunerada', 'Licencia remunerada'),
    ('licencia_no_remunerada', 'Licencia no remunerada'),
    ('ausencia_injustificada', 'Ausencia injustificada'),
]
# Las horas ordinarias diurnas no son novedad: ya van en el salario básico.
CONCEPTOS_DE_HORAS = [c for c, _n in CONCEPTOS if c in CAMPOS_HORAS]


class AshNovedadConcepto(models.Model):
    _name = 'ash.novedad.concepto'
    _description = 'Concepto de novedad y su código en Alegra'
    _order = 'clave'

    clave = fields.Selection(CONCEPTOS, required=True)
    codigo_alegra = fields.Char('Código / ID en Alegra', required=True,
                                help='Código o ID del concepto tal como existe en la nómina de Alegra.')
    unidad = fields.Selection([('horas', 'Horas'), ('dias', 'Días')], required=True)
    company_id = fields.Many2one('res.company', default=lambda s: s.env.company)

    _ash_concepto_unico = models.Constraint('UNIQUE(clave, company_id)',
                                            'El concepto ya tiene código en esta compañía.')

    def mapa_exportador(self):
        etiquetas = dict(CONCEPTOS)
        return {c.clave: (c.codigo_alegra, etiquetas[c.clave], c.unidad) for c in self}


class AshNovedadPeriodo(models.Model):
    _name = 'ash.novedad.periodo'
    _description = 'Periodo de novedades de nómina'
    _inherit = ['mail.thread']
    _order = 'fecha_desde desc'

    name = fields.Char(required=True, tracking=True)
    company_id = fields.Many2one('res.company', required=True, default=lambda s: s.env.company)
    fecha_desde = fields.Date(required=True)
    fecha_hasta = fields.Date(required=True)
    estado = fields.Selection([('borrador', 'Borrador'), ('calculado', 'Calculado'),
                               ('aprobado', 'Aprobado'), ('enviado', 'Enviado a Alegra')],
                              default='borrador', required=True, tracking=True)
    linea_ids = fields.One2many('ash.novedad.linea', 'periodo_id', string='Novedades')
    aprobado_por = fields.Many2one('res.users', readonly=True, tracking=True)
    calculado_por = fields.Many2one('res.users', readonly=True)
    total_lineas = fields.Integer(compute='_compute_total')
    asistencias_sin_turno = fields.Integer(compute='_compute_total',
                                           help='Marcaciones sin turno: revisar antes de aprobar.')

    def _rango_utc(self):
        return (datetime.combine(self.fecha_desde, time.min),
                datetime.combine(self.fecha_hasta, time.max))

    def _compute_total(self):
        for p in self:
            p.total_lineas = len(p.linea_ids)
            desde, hasta = p._rango_utc() if p.fecha_desde and p.fecha_hasta else (False, False)
            p.asistencias_sin_turno = desde and self.env['hr.attendance'].search_count([
                ('employee_id.company_id', '=', p.company_id.id), ('ash_sin_turno', '=', True),
                ('check_in', '>=', desde), ('check_in', '<=', hasta)]) or 0

    def action_calcular(self):
        for p in self:
            if p.estado not in ('borrador', 'calculado'):
                raise UserError(_('Solo se recalcula un periodo en borrador o calculado.'))
            p.linea_ids.filtered(lambda l: l.origen != 'manual').unlink()
            valores = p._lineas_asistencia() + p._lineas_permisos()
            self.env['ash.novedad.linea'].create(valores)
            p.write({'estado': 'calculado', 'calculado_por': self.env.uid})

    def _lineas_asistencia(self):
        desde, hasta = self._rango_utc()
        # sudo acotado a la compañía del periodo: el Gestor consolida a todos,
        # aunque las reglas de Asistencias solo le muestren a su equipo.
        asistencias = self.env['hr.attendance'].sudo().search([
            ('employee_id.company_id', '=', self.company_id.id), ('check_out', '!=', False),
            ('check_in', '>=', desde), ('check_in', '<=', hasta)])
        acumulado = defaultdict(float)
        for att in asistencias:
            for concepto in CONCEPTOS_DE_HORAS:
                acumulado[(att.employee_id.id, concepto)] += att[CAMPOS_HORAS[concepto]]
        return [{'periodo_id': self.id, 'employee_id': emp, 'concepto': concepto,
                 'cantidad': round(horas, 2), 'origen': 'asistencia'}
                for (emp, concepto), horas in acumulado.items() if horas]

    def _lineas_permisos(self):
        permisos = self.env['hr.leave'].sudo().search([
            ('employee_id.company_id', '=', self.company_id.id), ('state', '=', 'validate'),
            ('ash_concepto_alegra', 'not in', (False, 'sin_novedad')),
            ('request_date_from', '<=', self.fecha_hasta), ('request_date_to', '>=', self.fecha_desde)])
        lineas = []
        for permiso in permisos:
            ini = max(permiso.request_date_from, self.fecha_desde)
            fin = min(permiso.request_date_to, self.fecha_hasta)
            total = (permiso.request_date_to - permiso.request_date_from).days + 1
            dias = permiso.number_of_days * ((fin - ini).days + 1) / total if total else 0
            lineas.append({'periodo_id': self.id, 'employee_id': permiso.employee_id.id,
                           'concepto': permiso.ash_concepto_alegra, 'cantidad': round(dias, 2),
                           'fecha_inicio': ini, 'fecha_fin': fin, 'origen': 'permiso',
                           'leave_id': permiso.id, 'observacion': permiso.ash_numero_soporte or False})
        return lineas

    def action_aprobar(self):
        if not self.env.user.has_group('ash_rrhh_base.group_ash_rrhh_gestor'):
            raise UserError(_('Solo un Gestor RRHH aprueba novedades.'))
        for p in self:
            if p.estado != 'calculado':
                raise UserError(_('Calcule el periodo antes de aprobarlo.'))
            if p.calculado_por == self.env.user and not self.env.user._is_superuser():
                raise UserError(_('Quien calcula el periodo no puede aprobarlo (doble control).'))
            p.write({'estado': 'aprobado', 'aprobado_por': self.env.uid})

    def action_volver_borrador(self):
        self.filtered(lambda p: p.estado in ('calculado', 'aprobado')).write(
            {'estado': 'borrador', 'aprobado_por': False})

    def _filas_exportar(self):
        self.ensure_one()
        conceptos = self.env['ash.novedad.concepto'].search([('company_id', 'in', (self.company_id.id, False))])
        novedades = [{
            'identificacion': l.employee_id.sudo().ash_numero_documento or '',
            'empleado': l.employee_id.name, 'periodo_desde': self.fecha_desde,
            'periodo_hasta': self.fecha_hasta, 'concepto': l.concepto, 'cantidad': l.cantidad,
            'fecha_inicio': l.fecha_inicio, 'fecha_fin': l.fecha_fin, 'observacion': l.observacion,
        } for l in self.linea_ids]
        return exportador_alegra.filas(novedades, conceptos.mapa_exportador())

    def action_exportar_csv(self):
        self.ensure_one()
        if self.estado not in ('aprobado', 'enviado'):
            raise UserError(_('Solo se exporta un periodo aprobado.'))
        filas, sin_codigo = self._filas_exportar()
        if sin_codigo:
            raise UserError(_('Faltan códigos de Alegra para: %s', ', '.join(sin_codigo)))
        contenido = exportador_alegra.a_csv(filas)
        adjunto = self.env['ir.attachment'].create({
            'name': f'novedades_alegra_{self.fecha_desde}_{self.fecha_hasta}.csv',
            'datas': base64.b64encode(contenido.encode('utf-8')),
            'res_model': self._name, 'res_id': self.id, 'mimetype': 'text/csv'})
        return {'type': 'ir.actions.act_url', 'url': f'/web/content/{adjunto.id}?download=true',
                'target': 'self'}


class AshNovedadLinea(models.Model):
    _name = 'ash.novedad.linea'
    _description = 'Novedad de nómina'
    _order = 'employee_id, concepto'

    periodo_id = fields.Many2one('ash.novedad.periodo', required=True, ondelete='cascade', index=True)
    company_id = fields.Many2one(related='periodo_id.company_id', store=True)
    employee_id = fields.Many2one('hr.employee', string='Empleado', required=True)
    concepto = fields.Selection(CONCEPTOS, required=True)
    cantidad = fields.Float(digits=(16, 2), required=True)
    unidad = fields.Selection([('horas', 'Horas'), ('dias', 'Días')], compute='_compute_unidad', store=True)
    fecha_inicio = fields.Date()
    fecha_fin = fields.Date()
    origen = fields.Selection([('asistencia', 'Asistencia'), ('permiso', 'Permiso'),
                               ('manual', 'Manual')], default='manual', required=True)
    leave_id = fields.Many2one('hr.leave', string='Permiso')
    observacion = fields.Char()
    estado_envio = fields.Selection([('pendiente', 'Pendiente'), ('enviado', 'Enviado'),
                                     ('error', 'Error')], default='pendiente', copy=False)
    id_alegra = fields.Char('ID en Alegra', copy=False)
    error_envio = fields.Text(copy=False)

    @api.depends('concepto')
    def _compute_unidad(self):
        for l in self:
            l.unidad = 'horas' if l.concepto in CONCEPTOS_DE_HORAS else 'dias'

    @api.model_create_multi
    def create(self, vals_list):
        lineas = super().create(vals_list)
        if any(l.periodo_id.estado in ('aprobado', 'enviado') for l in lineas):
            raise UserError(_('El periodo ya está aprobado: vuelva a borrador para cambiarlo.'))
        return lineas
