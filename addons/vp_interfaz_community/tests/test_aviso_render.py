# -*- coding: utf-8 -*-
# Copyright ASH COLOMBIA SAS. Software propietario. Ver LICENSE en la raiz del repositorio.
"""El aviso de datos de muestra se VE, en un navegador de verdad.

**Por que no bastaban las pruebas que ya habia.** `test_aviso_muestra.py` vigila
el contrato con el upstream: que siga declarando `showRibbon`, que las cuatro
vistas sigan pasandolo, que la plantilla no cambie de nombre, que Odoo siga sin
pintarla el. Todo eso es necesario y **nada de eso demuestra que el usuario vea
el aviso**. Un `xpath` que dejara de encajar, un asset que no entrara en el
bundle o un `t-if` mal escrito pasarian las siete y dejarian la pantalla igual
que antes.

Lo señalo la segunda auditoria externa y tenia razon: probar la estructura no es
probar el render.

**Como se provoca el caso.** `useSampleModel` se activa cuando la vista declara
`sample="1"` **y** la busqueda no devuelve ni un registro. La vista se crea aqui,
en la prueba, con un dominio `[('id', '=', 0)]` que garantiza cero registros sea
cual sea el estado de la base. No se añade a ningun archivo de datos a proposito:
`sample="1"` esta prohibido en los modulos propios y lo vigila un lint — esta
vista existe solo durante la transaccion de la prueba.

**Y la otra cara.** El segundo recorrido usa la misma vista con un dominio que si
devuelve registros. Un aviso que saliera siempre no avisaria de nada, y esa es la
mitad de la propiedad que una sola prueba no cubre.
"""
import odoo.tests
from odoo.tests import tagged


ARCO = '''<list sample="1">
    <field name="name"/>
</list>'''


@tagged('post_install', '-at_install')
class TestAvisoRender(odoo.tests.HttpCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.vista = cls.env['ir.ui.view'].create({
            'name': 'vp_interfaz_community: lista con datos de muestra (prueba)',
            'model': 'res.partner.category',
            'type': 'list',
            'arch': ARCO,
        })
        # Dos acciones sobre la MISMA vista: lo unico que cambia es si hay
        # registros. Si cambiara algo mas, la comparacion no probaria nada.
        cls.accion_vacia = cls.env['ir.actions.act_window'].create({
            'name': 'Prueba sin registros',
            'res_model': 'res.partner.category',
            'view_mode': 'list',
            'views': [(cls.vista.id, 'list')],
            'domain': "[('id', '=', 0)]",
        })
        cls.etiqueta = cls.env['res.partner.category'].create(
            {'name': 'Etiqueta real de prueba'})
        # La grafica necesita su propia vista: `sample="1"` en un `<graph>`, y un
        # campo por el que agrupar. Se usa `res.partner.category` otra vez para
        # que lo unico distinto entre los casos sea el tipo de vista.
        cls.vista_grafica = cls.env['ir.ui.view'].create({
            'name': 'vp_interfaz_community: grafica con datos de muestra (prueba)',
            'model': 'res.partner.category',
            'type': 'graph',
            'arch': '<graph sample="1"><field name="name"/></graph>',
        })
        cls.accion_grafica = cls.env['ir.actions.act_window'].create({
            'name': 'Prueba grafica sin registros',
            'res_model': 'res.partner.category',
            'view_mode': 'graph',
            'views': [(cls.vista_grafica.id, 'graph')],
            'domain': "[('id', '=', 0)]",
        })
        cls.accion_con_datos = cls.env['ir.actions.act_window'].create({
            'name': 'Prueba con registros',
            'res_model': 'res.partner.category',
            'view_mode': 'list',
            'views': [(cls.vista.id, 'list')],
            'domain': f"[('id', '=', {cls.etiqueta.id})]",
        })

    def test_el_aviso_se_pinta_cuando_los_registros_son_inventados(self):
        """La prueba que faltaba: el aviso en el DOM, visible y una sola vez."""
        self.start_tour(f'/odoo/action-{self.accion_vacia.id}',
                        'vp_aviso_muestra_si', login='admin')

    def test_y_NO_se_pinta_cuando_los_registros_son_reales(self):
        """Misma vista, mismos assets, datos de verdad: nada de aviso."""
        self.start_tour(f'/odoo/action-{self.accion_con_datos.id}',
                        'vp_aviso_muestra_no', login='admin')

    def test_tambien_se_pinta_en_una_grafica_que_es_OTRO_paquete(self):
        """La prueba que evito publicar un fallo que solo aparece en produccion.

        Grafica y tabla dinamica viven en `web.assets_backend_lazy`, que no se
        carga hasta que alguien abre una de esas vistas. La primera version de la
        herencia nombraba `web.GraphController`, y la plantilla se llama
        `web.GraphView`: en una lista no se nota **nada**, y el dia que alguien
        abriera una grafica se habria encontrado la vista rota. Lo unico que lo
        delataba era una linea en la consola del navegador.
        """
        self.start_tour(f'/odoo/action-{self.accion_grafica.id}',
                        'vp_aviso_muestra_grafica', login='admin')

    def test_tambien_se_ve_en_la_pantalla_de_un_celular(self):
        """El caso original lo encontro el Product Owner **desde el celular**, y
        ahi fue donde las tarjetas de cifras inventadas se veian nitidas. Un
        aviso que se saliera de la pantalla o quedara tapado en 375 px de ancho
        no serviria para el unico sitio donde ya falló una vez.
        """
        self.browser_size = '375x812'
        self.touch_enabled = True
        self.start_tour(f'/odoo/action-{self.accion_vacia.id}',
                        'vp_aviso_muestra_si', login='admin')
