# -*- coding: utf-8 -*-
# Copyright ASH COLOMBIA SAS. Software propietario. Ver LICENSE en la raiz del repositorio.
{
    'name': 'ASH ERP — Identidad de producto',
    'summary': 'La interfaz que ve el usuario se presenta como ASH ERP',
    'description': """
Identidad visual del producto (DEC-020).

Lo que ve una persona usando el ERP dice **ASH ERP**: el titulo de la
pestaña, la pantalla de acceso, el pie de "hecho con", la pantalla de sin
conexion, el asistente del sistema (nombre y cara), el menu del usuario, los
dialogos de error, el pie de los correos, el nombre de la app instalable, el
logotipo en la barra superior y el color principal de la interfaz.

Que NO hace, y es deliberado:

* no toca el core: todo son herencias de plantilla (`inherit_id`, xpath),
  igual que el resto de addons propios;
* no borra avisos de licencia ni de copyright del motor. La LGPL-3 los
  exige en el codigo fuente y ahi se quedan. Tampoco los toca la
  documentacion tecnica, el SBOM ni la trazabilidad del upstream: nombrar
  el motor donde corresponde legal y tecnicamente es obligacion, no
  descuido;
* no promete ocultar el origen a quien mire por dentro. Las rutas, la API
  y el modo desarrollador siguen siendo los del motor. Esto cambia la
  cara del producto, no su procedencia.
    """,
    'version': '19.0.1.4.0',
    'category': 'Administration',
    'author': 'ASH COLOMBIA SAS',
    'website': '',
    'depends': ['web', 'mail', 'auth_signup'],
    'data': [
        'views/vp_marca_templates.xml',
        'data/vp_marca_data.xml',
    ],
    'assets': {
        # Antepuesto: `$o-community-color` es `!default` en el motor y gana
        # quien lo defina primero (ver el propio archivo).
        'web._assets_primary_variables': [
            ('prepend', 'vp_marca/static/src/scss/primary_variables.scss'),
        ],
        'web.assets_backend': [
            'vp_marca/static/src/js/marca.js',
            'vp_marca/static/src/xml/marca.xml',
            'vp_marca/static/src/scss/marca.scss',
        ],
        # La pantalla de acceso se sirve con el paquete del sitio publico.
        'web.assets_frontend': [
            'vp_marca/static/src/scss/acceso.scss',
            'vp_marca/static/src/js/acceso.js',
        ],
    },
    'post_init_hook': 'post_init_hook',
    'installable': True,
    'application': False,
    'license': 'Other proprietary',
}
