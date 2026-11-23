# -*- coding: utf-8 -*-
# Copyright ASH COLOMBIA SAS. Software propietario. Ver LICENSE en la raiz del repositorio.
{
    'name': 'ASH ERP — Interfaz sin ofertas Enterprise',
    'summary': 'La interfaz no promete lo que no hay: oculta lo Enterprise y marca los datos de muestra',
    'description': """
ASH ERP corre sobre Odoo Community. La interfaz de Community ofrece funciones
de la edicion de pago (Enterprise) que aqui no existen y no se pueden
activar: casillas con la etiqueta «Enterprise» en los Ajustes y aplicaciones
con el boton «Upgrade» en el menu Aplicaciones. Para quien usa el ERP son
promesas vacias.

Este modulo las OCULTA. Decision del Product Owner (2026-09-28): «oculta solo
lo enterprise». Las funciones gratuitas de Community que no esten activadas
siguen visibles, porque son capacidades reales.

* Ajustes: toda opcion marcada como de pago (widget `upgrade_boolean`) se
  marca invisible al armar la vista, en todas las pantallas de Ajustes de
  todos los modulos instalados, incluidos los que se instalen despues. Solo
  se ocultan: siguen en la vista para que las condiciones que las nombran
  sigan siendo validas.
* Aplicaciones: la lista no muestra los modulos Enterprise (`to_buy`). Se
  filtran las lecturas de la interfaz, no la base: instalar y actualizar
  siguen viendo todo, y no hay nada que restaurar al desinstalar.

Sin tocar el codigo de Odoo: herencia y datos. Los proveedores de pago
Enterprise los oculta el puente `vp_interfaz_community_pago`, que se instala
solo donde este `payment`.
    """,
    'version': '19.0.1.1.1',
    'category': 'Administration',
    'author': 'ASH COLOMBIA SAS',
    'website': '',
    'depends': ['base_setup', 'web'],
    'data': [],
    'assets': {
        'web.assets_backend': [
            'vp_interfaz_community/static/src/muestra/aviso_muestra.xml',
            'vp_interfaz_community/static/src/muestra/aviso_muestra.scss',
        ],
        # Grafica y tabla dinamica viven en el bundle PEREZOSO del upstream
        # (`web/static/src/views/graph/**` y `pivot/**` estan quitados de
        # `assets_backend` y puestos aqui). Heredar sus plantillas desde
        # `assets_backend` falla con «Missing (extension) parent templates», y lo
        # dice en voz alta en la consola del navegador: lo vio la prueba de
        # navegador, no una lectura del manifiesto.
        'web.assets_backend_lazy': [
            'vp_interfaz_community/static/src/muestra/aviso_muestra_lazy.xml',
        ],
        # Recorridos de navegador. Comprueban que el aviso LLEGA AL DOM, que es
        # justo lo que las pruebas estructurales no pueden demostrar.
        'web.assets_tests': [
            'vp_interfaz_community/static/tests/tours/aviso_muestra.js',
        ],
    },
    'auto_install': True,
    'installable': True,
    'application': False,
    'license': 'Other proprietary',
}
