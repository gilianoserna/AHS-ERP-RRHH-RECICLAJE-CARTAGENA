# -*- coding: utf-8 -*-
# Copyright ASH COLOMBIA SAS. Software propietario. Ver LICENSE en la raiz del repositorio.
"""El aviso de datos de muestra depende del upstream. Se vigila lo que depende.

**El problema.** Odoo ya sabe cuando una vista enseña registros inventados: el
modelo lo marca en `useSampleModel`. Lo que no hace es decirlo. Nuestro modulo
pinta el aviso en los cuatro renderizadores —lista, kanban, grafica y tabla
dinamica—, con cuatro herencias de plantilla y sin tocar el upstream.

**Y de ahi el riesgo que estas pruebas cubren.** Si una version futura de Odoo
renombra una plantilla, cambia el ancla del `xpath` o mueve un archivo a otro
paquete, nuestro aviso **dejaria de aparecer sin que falle nada**: los datos
inventados volverian a verse como datos reales, en silencio. Eso es exactamente
el defecto que este modulo existe para evitar, cometido una capa mas abajo.

Por eso se mira el codigo del upstream instalado, no el nuestro.

---

**LO QUE ESTAS PRUEBAS NO PUEDEN DEMOSTRAR, y hay que decirlo porque ya pasó.**
Son pruebas de **estructura**: leen archivos y comprueban que los nombres y las
señales siguen ahi. La primera version del aviso heredaba `web.ActionHelper`,
**estas pruebas pasaban todas** y el aviso **no se pintaba en la pantalla**,
porque `ActionHelper` solo se monta si la accion trae `help`. Lo encontro
`test_aviso_render.py`, que abre un navegador de verdad.

Estructura y render son dos cosas distintas. Hacen falta las dos, y ninguna
sustituye a la otra.
"""
import os

from odoo.modules.module import get_module_path
from odoo.tests import common, tagged

# Los cuatro renderizadores donde se pinta el aviso, con la plantilla que se
# hereda y el ancla del `xpath`. Si mañana son otros, esta tabla hay que
# cambiarla a mano — y eso es lo que se quiere: que alguien mire.
ANCLAJES = (
    ('static/src/views/list/list_renderer.xml', 'web.ListRenderer',
     "t-if=\"showNoContentHelper\""),
    ('static/src/views/kanban/kanban_renderer.xml', 'web.KanbanRenderer',
     "t-if=\"showNoContentHelper\""),
    # Ojo: los ficheros y los componentes se llaman `...Controller`, pero las
    # PLANTILLAS se llaman `web.GraphView` y `web.PivotView`. Heredar el nombre
    # del componente no falla al instalar: falla en la consola del navegador la
    # primera vez que alguien abre una grafica.
    ('static/src/views/graph/graph_controller.xml', 'web.GraphView',
     "t-component=\"props.Renderer\""),
    ('static/src/views/pivot/pivot_controller.xml', 'web.PivotView',
     "t-component=\"props.Renderer\""),
)


@tagged('post_install', '-at_install')
class TestAvisoDatosDeMuestra(common.TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.web = get_module_path('web')
        cls.propio = get_module_path('vp_interfaz_community')

    def _leer(self, base, relativo):
        ruta = os.path.join(base, relativo)
        self.assertTrue(os.path.isfile(ruta), f'no existe {relativo} en {base}')
        with open(ruta, encoding='utf-8') as f:
            return f.read()

    def _nuestras_plantillas(self):
        return (self._leer(self.propio, 'static/src/muestra/aviso_muestra.xml')
                + self._leer(self.propio, 'static/src/muestra/aviso_muestra_lazy.xml'))

    # ── La señal del upstream sigue existiendo ──────────────────────────

    def test_los_cuatro_renderizadores_siguen_mirando_useSampleModel(self):
        """`useSampleModel` es la pregunta de verdad: «esto que se ve, ¿es
        inventado?». Si un renderizador deja de consultarla, sus datos de muestra
        quedan sin marcar."""
        mudos = []
        for relativo, _plantilla, _ancla in ANCLAJES:
            if 'useSampleModel' not in self._leer(self.web, relativo):
                mudos.append(relativo)
        self.assertFalse(
            mudos, 'estas vistas dejaron de consultar useSampleModel: ' + ', '.join(mudos))

    def test_las_plantillas_que_heredamos_siguen_llamandose_igual(self):
        perdidas = []
        for relativo, plantilla, _ancla in ANCLAJES:
            if f't-name="{plantilla}"' not in self._leer(self.web, relativo):
                perdidas.append(plantilla)
        self.assertFalse(
            perdidas,
            'Odoo renombro estas plantillas y nuestra herencia dejaria de aplicarse: '
            + ', '.join(perdidas))

    def test_los_anclajes_del_xpath_siguen_estando(self):
        """**La prueba que mas vale de este archivo.** Un `xpath` cuyo ancla
        desaparece no deja el aviso mal puesto: hace fallar la carga del paquete
        con «Element not found», y eso tumba la interfaz entera. Que se entere
        aqui y no un usuario."""
        rotos = []
        for relativo, _plantilla, ancla in ANCLAJES:
            if ancla not in self._leer(self.web, relativo):
                rotos.append(f'{relativo} ya no contiene {ancla}')
        self.assertFalse(rotos, 'anclajes perdidos: ' + '; '.join(rotos))

    def test_grafica_y_tabla_dinamica_siguen_en_el_paquete_PEREZOSO(self):
        """Por que hay dos archivos nuestros y no uno.

        `web` quita `views/graph/**` y `views/pivot/**` de `assets_backend` y los
        pone en `assets_backend_lazy`. Heredar esas plantillas desde el paquete
        normal falla con «Missing (extension) parent templates» y **tumba toda la
        interfaz**. Si el upstream los devuelve al paquete normal, esto avisa.
        """
        manifiesto = self._leer(self.web, '__manifest__.py')
        self.assertIn("('remove', 'web/static/src/views/graph/**')", manifiesto)
        self.assertIn("('remove', 'web/static/src/views/pivot/**')", manifiesto)

    def test_odoo_SIGUE_sin_pintar_el_aviso_el_mismo(self):
        """Si algun dia lo pinta, hay que quitar el nuestro o saldran dos.

        No es un fallo del upstream: es un aviso de que estas herencias dejaron de
        hacer falta. El recorrido de navegador tambien lo cazaria —cuenta los
        avisos y exige exactamente uno— pero esto lo dice antes y mas claro.
        """
        plantilla = self._leer(self.web, 'static/src/views/action_helper.xml')
        self.assertNotIn('RibbonWidget', plantilla,
                         'Odoo ya pinta la cinta: revise si nuestro aviso sigue haciendo '
                         'falta o si ahora se duplica.')

    # ── Lo nuestro ──────────────────────────────────────────────────────

    def test_heredamos_los_cuatro_renderizadores(self):
        nuestras = self._nuestras_plantillas()
        for _relativo, plantilla, _ancla in ANCLAJES:
            self.assertIn(f't-inherit="{plantilla}"', nuestras,
                          f'no se hereda {plantilla}: esas vistas quedan sin aviso')

    def test_el_aviso_NO_depende_de_que_la_accion_traiga_texto_de_ayuda(self):
        """El fallo exacto de la primera version.

        Heredaba `web.ActionHelper`, que solo se monta si la accion define `help`.
        En las vistas sin ese texto —la mayoria— no se montaba nada y el aviso no
        aparecia. La condicion tiene que ser `useSampleModel` y nada mas.
        """
        nuestras = self._nuestras_plantillas()
        # Se busca la HERENCIA, no el nombre: los comentarios de las plantillas
        # explican por que ActionHelper no sirve, y esa explicacion tiene que
        # poder nombrarlo.
        self.assertNotIn('t-inherit="web.ActionHelper"', nuestras,
                         'volvio la herencia de ActionHelper: el aviso solo saldria en las '
                         'vistas cuya accion trae texto de ayuda')
        self.assertNotIn('props.showRibbon', nuestras,
                         'showRibbon solo existe dentro de ActionHelper, que casi nunca se '
                         'monta')
        self.assertIn('useSampleModel', nuestras)

    def test_el_texto_del_aviso_vive_en_un_solo_sitio(self):
        """Cuatro copias del mismo texto se desincronizan. Una se mantiene."""
        nuestras = self._nuestras_plantillas()
        self.assertEqual(nuestras.count('DATOS DE MUESTRA — NO SON DATOS REALES'), 1)
        self.assertEqual(nuestras.count('t-call="vp_interfaz_community.AvisoMuestra"'), 4,
                         'los cuatro renderizadores tienen que llamar a la misma plantilla')

    def test_el_aviso_se_carga_en_los_dos_paquetes(self):
        """Una plantilla que no entra en ningun paquete no se pinta nunca."""
        manifiesto = self._leer(self.propio, '__manifest__.py')
        self.assertIn('web.assets_backend', manifiesto)
        self.assertIn('aviso_muestra.xml', manifiesto)
        self.assertIn('aviso_muestra.scss', manifiesto)
        self.assertIn('web.assets_backend_lazy', manifiesto)
        self.assertIn('aviso_muestra_lazy.xml', manifiesto)
