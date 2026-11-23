# -*- coding: utf-8 -*-
{
    'name': 'ASH RRHH — Conector API de Alegra',
    'summary': 'Trae empleados desde la nómina de Alegra y le envía las novedades aprobadas',
    'description': """
Alegra es la nómina electrónica (liquida y transmite a la DIAN). Este conector:

* LEE empleados de Alegra (fuente de verdad del maestro) y los crea o
  actualiza en el ERP, de forma idempotente (huella por registro);
* ENVÍA a Alegra las novedades de un periodo aprobado, línea por línea, con
  su estado y error por línea para reintentar solo lo fallido;
* modo «Ensayo» (sin red, nada sale del ERP) y modo «Real»;
* bitácora de cada ejecución; credenciales visibles solo para administradores.
    """,
    'version': '19.0.0.1.0',
    'category': 'Human Resources',
    'author': 'ASH COLOMBIA SAS',
    'depends': ['ash_rrhh_novedades'],
    'data': [
        'security/ir.model.access.csv',
        'data/ash_alegra_cron.xml',
        'views/ash_alegra_views.xml',
    ],
    'installable': True,
    'license': 'Other proprietary',
}
