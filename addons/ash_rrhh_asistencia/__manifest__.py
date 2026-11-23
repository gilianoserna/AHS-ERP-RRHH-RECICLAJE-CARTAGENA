# -*- coding: utf-8 -*-
{
    'name': 'ASH RRHH — Asistencia contra turno',
    'summary': 'Cruza las marcaciones (hr_attendance) con el turno publicado y clasifica las horas',
    'description': """
Reutiliza Asistencias de Odoo Community (marcación por kiosco, PIN, web o
móvil) y añade:

* enlace de cada marcación con el turno publicado del empleado;
* minutos de llegada tarde (con tolerancia parametrizable);
* clasificación de las horas trabajadas: ordinarias, nocturnas,
  dominicales/festivas y extras (diurnas, nocturnas, dominicales), con la
  franja nocturna y los festivos vigentes en la fecha;
* marca «sin turno» para que el supervisor revise lo trabajado fuera de programación.

No calcula dinero: las horas se entregan como novedad a Alegra.
    """,
    'version': '19.0.0.1.0',
    'category': 'Human Resources',
    'author': 'ASH COLOMBIA SAS',
    'depends': ['hr_attendance', 'ash_rrhh_turnos'],
    'data': [
        'security/ash_asistencia_groups.xml',
        'views/hr_attendance_views.xml',
    ],
    'installable': True,
    'license': 'Other proprietary',
}
