# -*- coding: utf-8 -*-
{
    'name': 'ASH RRHH — Novedades para Alegra',
    'summary': 'Cierre de periodo: consolida horas y ausencias como novedades de nómina para Alegra',
    'description': """
Este ERP NO liquida nómina ni transmite nómina electrónica: eso sigue en Alegra.

Por cada periodo (quincena o mes) se consolidan:
* horas extra y recargos desde la asistencia clasificada contra el turno;
* vacaciones, incapacidades y licencias aprobadas;
* novedades manuales.

Flujo: borrador -> calculado -> aprobado (Gestor RRHH) -> enviado.
La salida es un CSV para cargar en Alegra o, con `ash_alegra_conector`, el
envío directo por la API de Alegra.
    """,
    'version': '19.0.0.1.0',
    'category': 'Human Resources',
    'author': 'ASH COLOMBIA SAS',
    'depends': ['ash_rrhh_asistencia', 'ash_rrhh_permisos'],
    'data': [
        'security/ir.model.access.csv',
        'security/ash_novedades_rules.xml',
        'data/ash_novedad_concepto_data.xml',
        'views/ash_novedad_views.xml',
    ],
    'installable': True,
    'license': 'Other proprietary',
}
