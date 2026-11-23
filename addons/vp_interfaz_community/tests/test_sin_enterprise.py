# -*- coding: utf-8 -*-
# Copyright ASH COLOMBIA SAS. Software propietario.
"""Ninguna oferta de Odoo Enterprise a la vista; las funciones de Community, si.

Decision del Product Owner (2026-09-28): «oculta solo lo enterprise».
"""
import copy

from lxml import etree

from odoo.tests import TransactionCase, tagged

from odoo.addons.vp_interfaz_community.models.res_config_settings import (
    WIDGET_ENTERPRISE, ocultar_enterprise)


def _oculto(nodo):
    """Invisible el nodo o algun contenedor: asi lo ve la persona."""
    return any(n.get('invisible') in ('1', 'True', 'true') for n in [nodo] + list(nodo.iterancestors()))


@tagged('post_install', '-at_install', 'vp_interfaz_community')
class TestAjustesSinEnterprise(TransactionCase):

    def test_ninguna_opcion_enterprise_queda_visible(self):
        """La vista COMBINADA —todos los modulos instalados— tal como la
        recibe el navegador."""
        arch = etree.fromstring(self.env['res.config.settings'].get_view(view_type='form')['arch'])
        enterprise = [c for c in arch.iter('field') if c.get('widget') == WIDGET_ENTERPRISE]
        self.assertTrue(enterprise, 'sin opciones Enterprise en la vista la prueba no mediría nada')
        visibles = [c.get('name') for c in enterprise if not _oculto(c)]
        self.assertFalse(visibles, f'opciones Enterprise visibles: {visibles}')

    def test_solo_cambia_lo_enterprise(self):
        """Contraprueba: se compara la vista de Odoo sin filtrar con la
        filtrada. Toda opcion que paso a invisible tiene como campo principal
        uno Enterprise, y las demas siguen exactamente como Odoo las trae."""
        vista = self.env['ir.ui.view'].sudo().browse(
            self.env['ir.ui.view'].default_view('res.config.settings', 'form'))
        original = vista._get_combined_arch()
        filtrada = copy.deepcopy(original)
        self.assertTrue(ocultar_enterprise(filtrada))
        # Por posicion, no por id: Odoo repite ids (hr: tres
        # «presence_reporting_setting»). La copia conserva la estructura.
        pares = list(zip(original.iter('setting'), filtrada.iter('setting')))
        self.assertEqual(len(pares), len(list(original.iter('setting'))))
        cambiadas, intactas = [], 0
        for antes, opcion in pares:
            if opcion.get('invisible') != antes.get('invisible'):
                cambiadas.append(opcion)
            elif not antes.get('invisible'):
                intactas += 1
        self.assertTrue(cambiadas)
        for opcion in cambiadas:
            self.assertEqual(next(opcion.iter('field')).get('widget'), WIDGET_ENTERPRISE, opcion.get('id'))
        self.assertGreater(intactas, 20, 'las opciones de Community siguen visibles')

    def test_se_oculta_sin_borrar(self):
        """Las condiciones que nombran un campo Enterprise siguen teniendo su
        campo en la vista (antes de que Odoo quite lo que el usuario no ve por
        grupos)."""
        arch, _vista = self.env['res.config.settings']._get_view(view_type='form')
        campo = next(c for c in arch.iter('field') if c.get('name') == 'module_account_inter_company_rules')
        self.assertTrue(_oculto(campo))

    def test_la_regla_sobre_un_arbol_de_ejemplo(self):
        arch = etree.fromstring('''
            <form><app name="x">
              <block title="Todo de pago">
                <setting id="a"><field name="module_a" widget="upgrade_boolean"/></setting>
                <setting id="b"><field name="module_b" widget="upgrade_boolean"/></setting>
              </block>
              <block title="Mixto">
                <setting id="c"><field name="module_c" widget="upgrade_boolean"/><div>ayuda</div></setting>
                <setting id="d"><field name="module_d"/>
                  <div><field name="module_e" widget="upgrade_boolean"/><label for="module_e"/></div>
                </setting>
              </block>
            </app></form>''')
        self.assertEqual(ocultar_enterprise(arch), 4)
        por_id = {s.get('id'): s for s in arch.iter('setting')}
        bloques = list(arch.iter('block'))
        self.assertEqual(bloques[0].get('invisible'), '1', 'un bloque solo de pago se oculta entero')
        self.assertIsNone(bloques[1].get('invisible'), 'un bloque con algo gratuito queda')
        self.assertEqual(por_id['c'].get('invisible'), '1')
        self.assertIsNone(por_id['d'].get('invisible'), 'la opción gratuita queda')
        anidado = next(c for c in arch.iter('field') if c.get('name') == 'module_e')
        etiqueta = next(arch.iter('label'))
        self.assertEqual((anidado.get('invisible'), etiqueta.get('invisible')), ('1', '1'))


@tagged('post_install', '-at_install', 'vp_interfaz_community')
class TestAplicacionesSinEnterprise(TransactionCase):

    def test_la_lista_de_aplicaciones_no_muestra_modulos_enterprise(self):
        Modulo = self.env['ir.module.module']
        self.assertTrue(Modulo.search_count([('to_buy', '=', True)]),
                        'sin módulos Enterprise en la base la prueba no mediría nada')
        lista = Modulo.web_search_read([], {'name': {}, 'to_buy': {}})
        self.assertTrue(lista['records'], 'las aplicaciones de Community se siguen viendo')
        self.assertFalse([r['name'] for r in lista['records'] if r['to_buy']])
        con_filtro_de_la_accion = Modulo.web_search_read([('application', '=', True)], {'to_buy': {}})
        self.assertFalse([r for r in con_filtro_de_la_accion['records'] if r['to_buy']])

    def test_agrupado_tampoco(self):
        Modulo = self.env['ir.module.module']
        grupos = Modulo.web_read_group([], ['to_buy'], ['__count'])['groups']
        self.assertEqual({g['to_buy'] for g in grupos}, {False})

    def test_los_contadores_del_panel_cuentan_lo_que_se_ve(self):
        Modulo = self.env['ir.module.module']
        panel = Modulo.search_panel_select_range('category_id', enable_counters=True, search_domain=[])
        con_enterprise = 0
        for categoria in panel['values']:
            dentro = [('category_id', 'child_of', categoria['id'])]
            visibles = Modulo.web_search_read(dentro, {'id': {}})['length']
            self.assertEqual(categoria['__count'], visibles, categoria['display_name'])
            con_enterprise += bool(Modulo.search_count(dentro + [('to_buy', '=', True)]))
        self.assertTrue(con_enterprise, 'ninguna categoria tenia modulos Enterprise: la prueba no mediria nada')

    def test_se_oculta_en_la_interfaz_no_en_la_base(self):
        """Instalar y actualizar la lista de aplicaciones siguen viendo todo."""
        self.assertTrue(self.env['ir.module.module'].search([('to_buy', '=', True)]))
