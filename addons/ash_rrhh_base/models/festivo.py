# -*- coding: utf-8 -*-
from datetime import date

from odoo import api, fields, models

from ..lib import festivos_co


class AshRrhhFestivo(models.Model):
    _name = 'ash.rrhh.festivo'
    _description = 'Día festivo'
    _order = 'fecha'

    fecha = fields.Date(required=True, index=True)
    name = fields.Char('Festivo', required=True)
    company_id = fields.Many2one('res.company', string='Compañía',
                                 help='Vacío = festivo nacional para todas las compañías.')
    manual = fields.Boolean(help='Agregado a mano (día cívico, decreto local…).')

    _ash_festivo_unico = models.Constraint('UNIQUE(fecha, company_id)', 'Ese festivo ya existe.')

    @api.model
    def generar_anio(self, anio):
        existentes = set(self.search([('company_id', '=', False),
                                      ('fecha', '>=', date(anio, 1, 1)),
                                      ('fecha', '<=', date(anio, 12, 31))]).mapped('fecha'))
        nuevos = [{'fecha': f, 'name': n} for f, n in festivos_co.festivos(anio).items()
                  if f not in existentes]
        return self.create(nuevos)

    @api.model
    def _cron_generar(self):
        hoy = fields.Date.context_today(self)
        for anio in (hoy.year, hoy.year + 1):
            self.generar_anio(anio)

    @api.model
    def conjunto(self, desde, hasta, company=None):
        """frozenset de fechas festivas entre dos fechas (para el motor de jornada)."""
        company = company or self.env.company
        return frozenset(self.sudo().search([
            ('fecha', '>=', desde), ('fecha', '<=', hasta),
            '|', ('company_id', '=', False), ('company_id', '=', company.id)]).mapped('fecha'))
