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
* tipos que exigen soporte (incapacidad, licencias): no se aprueban sin adjunto;
* saldo de vacaciones: causación automática de 15 días hábiles por año (1,25 por
  mes) y asistente para cargar el saldo inicial de cada empleado. Solo las
  vacaciones llevan saldo; incapacidades y licencias se piden sin asignación.
    """,
    'version': '19.0.0.1.1',
    'category': 'Human Resources',
    'author': 'ASH COLOMBIA SAS',
    'depends': ['hr_holidays', 'ash_rrhh_base'],
    'data': [
        'security/ash_permisos_groups.xml',
        'security/ir.model.access.csv',
        'data/hr_leave_type_data.xml',
        'data/hr_leave_accrual_plan_data.xml',
        'views/hr_leave_views.xml',
        'wizard/ash_vacaciones_cargar_views.xml',
    ],
    'installable': True,
    'auto_install': False,
    'license': 'Other proprietary',
}
