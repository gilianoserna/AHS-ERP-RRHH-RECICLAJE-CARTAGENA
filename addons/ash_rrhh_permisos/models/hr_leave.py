# -*- coding: utf-8 -*-
from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

# Conceptos de ausencia que viajan a Alegra (ver ash_rrhh_novedades).
CONCEPTOS_AUSENCIA = [
    ('vacaciones', 'Vacaciones disfrutadas'),
    ('incapacidad_general', 'Incapacidad enfermedad general'),
    ('incapacidad_laboral', 'Incapacidad accidente/enfermedad laboral'),
    ('licencia_maternidad', 'Licencia de maternidad'),
    ('licencia_paternidad', 'Licencia de paternidad'),
    ('licencia_remunerada', 'Licencia remunerada (luto, calamidad, otras)'),
    ('licencia_no_remunerada', 'Licencia no remunerada'),
    ('ausencia_injustificada', 'Ausencia injustificada'),
    ('sin_novedad', 'No genera novedad de nómina'),
]


class HrLeaveType(models.Model):
    _inherit = 'hr.leave.type'

    ash_concepto_alegra = fields.Selection(CONCEPTOS_AUSENCIA, string='Concepto para Alegra',
                                           default='sin_novedad', required=True)
    ash_requiere_soporte = fields.Boolean('Exige soporte adjunto',
                                          help='No se puede aprobar sin un documento adjunto '
                                               '(incapacidad, registro civil, etc.).')


class HrLeave(models.Model):
    _inherit = 'hr.leave'

    ash_concepto_alegra = fields.Selection(related='holiday_status_id.ash_concepto_alegra', store=True)
    ash_numero_soporte = fields.Char('N.º de incapacidad / soporte')

    @api.constrains('state')
    def _ash_check_soporte(self):
        for permiso in self:
            if permiso.state not in ('validate1', 'validate'):
                continue
            if not permiso.holiday_status_id.ash_requiere_soporte:
                continue
            adjuntos = self.env['ir.attachment'].sudo().search_count([
                ('res_model', '=', 'hr.leave'), ('res_id', '=', permiso.id)])
            if not adjuntos:
                raise ValidationError(_(
                    'El tipo «%s» exige un soporte adjunto antes de aprobarse.',
                    permiso.holiday_status_id.name))
