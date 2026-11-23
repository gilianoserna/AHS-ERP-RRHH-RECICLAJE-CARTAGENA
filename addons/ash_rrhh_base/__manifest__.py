# -*- coding: utf-8 -*-
{
    'name': 'ASH RRHH — Base Colombia',
    'summary': 'Datos colombianos del empleado, grupos, festivos y parámetros laborales con vigencia',
    'description': """
Base del ERP de gestión de empleados (sin nómina: la nómina electrónica sigue en Alegra).

* Grupos: Empleado (autoservicio), Supervisor (turnos y permisos de su equipo) y Gestor RRHH.
* Empleado: tipo y número de documento, EPS, AFP, ARL, caja y fondo de cesantías,
  identificador del empleado en Alegra.
* Festivos de Colombia generados por año (Ley Emiliani) y editables.
* Parámetros laborales con fecha de vigencia (franja nocturna, tope semanal…):
  la ley cambia por etapas, así que nunca se fijan en el código.
    """,
    'version': '19.0.0.1.0',
    'category': 'Human Resources',
    'author': 'ASH COLOMBIA SAS',
    'depends': ['hr', 'vp_marca', 'vp_interfaz_community'],
    'data': [
        'security/ash_rrhh_groups.xml',
        'security/ir.model.access.csv',
        'data/ash_rrhh_parametros.xml',
        'data/ash_rrhh_cron.xml',
        'views/hr_employee_views.xml',
        'views/ash_rrhh_config_views.xml',
    ],
    'installable': True,
    'application': True,
    'license': 'Other proprietary',
}
