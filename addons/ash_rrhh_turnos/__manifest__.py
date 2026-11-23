# -*- coding: utf-8 -*-
{
    'name': 'ASH RRHH — Turnos',
    'summary': 'Plantillas de turno, rotaciones y programación con validaciones laborales',
    'description': """
Reemplaza a Planning (Odoo Enterprise, que no se usa) con un módulo propio:

* plantillas de turno (inicio, fin, descanso; turnos que cruzan medianoche);
* rotaciones (ciclos de N días con turnos y descansos);
* asistente para generar la programación de un grupo de empleados;
* validaciones: sin traslapes, descanso mínimo entre turnos, alerta de tope
  semanal (Ley 2101) — todo leído de los parámetros con vigencia;
* estados borrador / publicado / cancelado: el empleado solo ve lo publicado.
    """,
    'version': '19.0.0.1.0',
    'category': 'Human Resources',
    'author': 'ASH COLOMBIA SAS',
    'depends': ['ash_rrhh_base'],
    'data': [
        'security/ir.model.access.csv',
        'security/ash_turnos_rules.xml',
        'wizard/ash_turno_generar_views.xml',
        'views/ash_turno_views.xml',
    ],
    'installable': True,
    'license': 'Other proprietary',
}
