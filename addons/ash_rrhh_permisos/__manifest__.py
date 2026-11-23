# -*- coding: utf-8 -*-
{
    'name': 'ASH RRHH — Permisos, licencias e incapacidades',
    'summary': 'Tipos de ausencia colombianos sobre Ausencias (hr_holidays) de Odoo Community',
    'description': """
Reutiliza el flujo de solicitudes y aprobaciones de Odoo (hr_holidays, LGPL) y
le añade lo colombiano:

* tipos de ausencia: vacaciones, incapacidad general y laboral, licencias de
  maternidad, paternidad, luto, calamidad doméstica, remunerada, no remunerada,
  permiso sindical, citas médicas y ausencia injustificada;
* cada tipo indica el concepto con el que viaja a Alegra como novedad;
* tipos que exigen soporte (incapacidad, licencias): no se aprueban sin adjunto.
    """,
    'version': '19.0.0.1.0',
    'category': 'Human Resources',
    'author': 'ASH COLOMBIA SAS',
    'depends': ['hr_holidays', 'ash_rrhh_base'],
    'data': [
        'security/ash_permisos_groups.xml',
        'data/hr_leave_type_data.xml',
        'views/hr_leave_views.xml',
    ],
    'installable': True,
    'auto_install': False,
    'license': 'Other proprietary',
}
