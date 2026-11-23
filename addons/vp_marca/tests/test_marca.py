# -*- coding: utf-8 -*-
# Copyright ASH COLOMBIA SAS. Software propietario.
"""La identidad del producto, medida donde de verdad se ve (DEC-020).

Estas pruebas no comprueban que un texto diga «ASH ERP»: comprueban que el
nombre y las imagenes del MOTOR ya no aparecen donde el usuario mira. Por eso
casi todas llevan su contraprueba contra el archivo original de Odoo: sin
ella, una prueba que solo afirme «el logotipo es el nuestro» pasaria igual si
los dos archivos fueran el mismo.

POR QUE SE COMPARA POR FIRMA Y NO POR BYTES
===========================================
`res.company.logo` es `related='partner_id.image_1920'`, y Odoo **reprocesa**
la imagen al guardarla: los bytes almacenados no son los del archivo. La
primera version de estas pruebas comparaba bytes y fallaba por eso, no por el
codigo. Se compara una firma —una miniatura de 16x16 en RGB—, que sobrevive al
reprocesado y sigue distinguiendo dos imagenes distintas.
"""
import base64
import io

from PIL import Image

from odoo.tests import tagged
from odoo.tests.common import HttpCase, TransactionCase
from odoo.tools import file_open

from odoo.addons.vp_marca import LOGO_ASH, LOGO_ODOO, post_init_hook


def leer(ruta):
    with file_open(ruta, 'rb') as archivo:
        return base64.b64encode(archivo.read())


def firma(imagen_b64):
    """Miniatura 16x16 en RGB. Sobrevive al reprocesado de Odoo."""
    imagen = Image.open(io.BytesIO(base64.b64decode(imagen_b64)))
    fondo = Image.new('RGB', imagen.size, (255, 255, 255))
    fondo.paste(imagen, mask=imagen.convert('RGBA').getchannel('A'))
    return fondo.resize((16, 16), Image.LANCZOS).tobytes()


def png(color, tam=(64, 64)):
    """Un PNG VALIDO. Odoo valida la imagen al guardarla, asi que unos bytes
    inventados revientan antes de llegar a lo que se quiere medir."""
    buffer = io.BytesIO()
    Image.new('RGB', tam, color).save(buffer, format='PNG')
    return base64.b64encode(buffer.getvalue())


@tagged('post_install', '-at_install', 'vp_marca')
class TestLogotipoDeCompania(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.ash = leer(LOGO_ASH)
        cls.odoo = leer(LOGO_ODOO)

    def test_los_dos_logotipos_son_distintos(self):
        """Sin esto, todas las demas pruebas de este bloque podrian pasar
        siendo el mismo archivo. Es la que las sostiene."""
        self.assertNotEqual(firma(self.ash), firma(self.odoo))

    def test_una_compania_nueva_no_nace_con_el_logotipo_del_motor(self):
        """`res.company.logo` trae por defecto el logotipo de Odoo
        (`base/models/res_company.py:62`), y sale en la pantalla de acceso y
        en los documentos impresos hasta que alguien suba el suyo. No esta en
        ninguna plantilla: es un dato, y por eso DEC-020 no lo cubria."""
        nueva = self.env['res.company'].create({'name': 'Razón social nueva'})
        self.assertEqual(firma(nueva.logo), firma(self.ash))
        self.assertNotEqual(firma(nueva.logo), firma(self.odoo))

    def test_el_defecto_se_declara_en_el_campo_no_solo_en_el_metodo(self):
        """Regresion de un error propio, y la razon de que esta prueba exista.

        El motor guarda en `default=` la FUNCION `_get_logo` del modulo base:
        sobrescribir el metodo no cambia el defecto del campo. La primera
        version de este modulo hacia justo eso y no hacia nada —la compañia
        seguia naciendo con el logotipo de Odoo— mientras el codigo aparentaba
        estar bien.
        """
        defecto = self.env['res.company']._fields['logo'].default
        self.assertTrue(callable(defecto))
        self.assertEqual(firma(defecto(self.env['res.company'])), firma(self.ash))

    def test_el_aviso_de_que_falta_el_logotipo_del_cliente_sigue_vivo(self):
        """`uses_default_logo` lo calcula el motor comparando contra
        `_get_logo()`, asi que el metodo sobrescrito lo mantiene coherente sin
        tocarlo. Importa: es lo que hace que la interfaz invite al cliente a
        subir el SUYO, que es el que debe ir en sus facturas."""
        nueva = self.env['res.company'].create({'name': 'Razón social B'})
        self.assertTrue(nueva.uses_default_logo)
        nueva.logo = png((12, 34, 56))
        self.assertFalse(nueva.uses_default_logo)


@tagged('post_install', '-at_install', 'vp_marca')
class TestRelevoDelLogotipo(TransactionCase):
    """El gancho de instalacion. Solo releva lo que nadie eligio."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.ash = leer(LOGO_ASH)
        cls.odoo = leer(LOGO_ODOO)

    def test_releva_a_la_compania_que_todavia_traia_el_del_motor(self):
        """Cambiar el valor por defecto solo alcanza a las compañias futuras.
        Las que ya existen nacieron con el del motor guardado y seguirian
        enseñandolo despues de instalar la marca."""
        vieja = self.env['res.company'].create({'name': 'Razón social vieja'})
        vieja.logo = self.odoo
        self.assertEqual(firma(vieja.logo), firma(self.odoo), 'el fixture no preparó el caso')
        post_init_hook(self.env)
        self.assertEqual(firma(vieja.logo), firma(self.ash))

    def test_el_logotipo_propio_del_cliente_no_se_toca(self):
        """La contraprueba que hace aceptable la anterior. Un cliente que
        descubra que una actualizacion le cambio el logotipo de sus facturas
        tiene razon en enfadarse: la unica sustitucion legitima es la de un
        valor que nadie eligio."""
        propio = png((200, 30, 90))
        suya = self.env['res.company'].create({'name': 'Cliente con marca propia'})
        suya.logo = propio
        post_init_hook(self.env)
        self.assertEqual(firma(suya.logo), firma(propio))
        self.assertNotEqual(firma(suya.logo), firma(self.ash))


@tagged('post_install', '-at_install', 'vp_marca')
class TestIconoDeLaPestana(TransactionCase):

    def arch_de_layout(self):
        from lxml import etree
        arch = self.env.ref('web.layout')._get_combined_arch()
        if isinstance(arch, bytes):
            return arch.decode()
        if isinstance(arch, str):
            return arch
        return etree.tostring(arch).decode()

    def test_la_plantilla_ya_no_cae_en_el_icono_del_motor(self):
        """`web.layout` resuelve `x_icon or '/web/static/img/favicon.ico'`:
        cuando la pantalla no fija icono propio —que es siempre, salvo en la
        aplicacion instalada como PWA— sale el del motor. Se queda en la
        pestaña todo el dia, asi que era la mencion mas persistente."""
        texto = self.arch_de_layout()
        self.assertNotIn('/web/static/img/favicon.ico', texto,
                         'la pestaña sigue cayendo en el icono del motor')
        self.assertIn('/vp_marca/static/src/img/ash_erp_favicon.png', texto)

    def test_el_icono_propio_de_una_pantalla_sigue_mandando(self):
        """No se sustituye el mecanismo, solo el respaldo: la PWA fija su
        `x_icon` (`webclient_templates.xml:377`) y ese tiene que seguir
        ganando. Si se hubiera reemplazado el `t-att-href` por una ruta fija,
        la aplicacion instalada perderia su icono."""
        self.assertIn('x_icon or', self.arch_de_layout())

    def test_los_archivos_de_marca_existen_donde_los_declara_el_codigo(self):
        """Una ruta mal escrita aqui no rompe ninguna prueba de logica: deja
        una imagen rota en pantalla, que es peor porque nadie se entera."""
        for ruta in (LOGO_ASH,
                     'vp_marca/static/src/img/ash_erp_favicon.png',
                     'vp_marca/static/description/icon.png'):
            with file_open(ruta, 'rb') as archivo:
                datos = archivo.read()
            self.assertTrue(datos.startswith(b'\x89PNG'), f'{ruta} no es un PNG')
            self.assertGreater(len(datos), 500, f'{ruta} está vacío o truncado')


# El avatar con el que el modulo de correo viste al asistente del sistema
# (`mail/data/res_partner_data.xml:6`).
AVATAR_DEL_MOTOR = 'mail/static/src/img/odoobot.png'


def arch_combinado(env, xmlid):
    from lxml import etree
    arch = env.ref(xmlid)._get_combined_arch()
    if isinstance(arch, bytes):
        return arch.decode()
    if isinstance(arch, str):
        return arch
    return etree.tostring(arch).decode()


@tagged('post_install', '-at_install', 'vp_marca')
class TestLogotipoNitido(TransactionCase):
    """El PO vio el logotipo de la pantalla de acceso «menos detallado» que el
    que entrego: el motor lo reduce a 180 px de ancho."""

    def ancho_logo_web(self, compania):
        return Image.open(io.BytesIO(base64.b64decode(compania.logo_web))).size[0]

    def test_una_compania_nueva_tiene_el_logotipo_de_pantalla_a_540(self):
        from odoo.addons.vp_marca.models.res_company import ANCHO_LOGO_WEB
        compania = self.env['res.company'].create({'name': 'Marca nitida'})
        self.assertEqual(ANCHO_LOGO_WEB, 540)
        self.assertAlmostEqual(self.ancho_logo_web(compania), 540, delta=2)

    def test_contraprueba_el_motor_lo_dejaba_en_180(self):
        """Sin esto, la prueba de arriba pasaria igual si el motor ya lo
        hiciera a 540: se mide lo que hace el metodo del motor."""
        from odoo.addons.base.models.res_company import ResCompany as Base
        compania = self.env['res.company'].create({'name': 'Marca del motor'})
        Base._compute_logo_web(compania)
        # El remuestreo de Odoo redondea: 179 o 180 segun la proporcion.
        self.assertAlmostEqual(self.ancho_logo_web(compania), 180, delta=2)

    def test_un_logotipo_pequeno_no_se_agranda(self):
        compania = self.env['res.company'].create({'name': 'Logo chico', 'logo': png('red', (120, 60))})
        self.assertEqual(self.ancho_logo_web(compania), 120)

    def test_el_gancho_recalcula_tambien_las_companias_existentes(self):
        """Es un campo ALMACENADO: cambiar como se calcula no cambia lo que
        ya estaba guardado. Lo hace el gancho (instalacion) y la migracion
        19.0.1.2.0 (actualizacion), que llama a la misma funcion."""
        from odoo.addons.base.models.res_company import ResCompany as Base
        from odoo.addons.vp_marca import refrescar_logo_web
        compania = self.env['res.company'].create({'name': 'Existente'})
        Base._compute_logo_web(compania)
        self.assertAlmostEqual(self.ancho_logo_web(compania), 180, delta=2)
        refrescar_logo_web(self.env)
        self.assertAlmostEqual(self.ancho_logo_web(compania), 540, delta=2)

    def test_la_migracion_llama_a_la_misma_funcion(self):
        with file_open('vp_marca/migrations/19.0.1.2.0/post-migrate.py', 'r') as f:
            fuente = f.read()
        self.assertIn('refrescar_logo_web(', fuente)


@tagged('post_install', '-at_install', 'vp_marca')
class TestAsistenteYAplicacion(TransactionCase):

    def test_una_base_que_aun_tiene_la_cara_del_motor_la_cambia(self):
        """El caso real: una base existente con «OdooBot» y su logotipo. En
        una actualizacion el archivo de datos NO lo cambia (el identificador
        esta marcado `noupdate` por el modulo de correo); lo cambia
        `vestir_asistente`, que llaman el gancho y la migracion."""
        from odoo.addons.vp_marca import vestir_asistente
        asistente = self.env.ref('base.partner_root').sudo()
        asistente.write({'name': 'OdooBot', 'image_1920': leer(AVATAR_DEL_MOTOR)})
        self.assertEqual(firma(asistente.image_1920), firma(leer(AVATAR_DEL_MOTOR)))
        vestir_asistente(self.env)
        self.assertEqual(asistente.name, 'Asistente ASH')
        self.assertEqual(firma(asistente.image_1920),
                         firma(leer('vp_marca/static/description/icon.png')))
        self.assertNotEqual(firma(asistente.image_1920), firma(leer(AVATAR_DEL_MOTOR)),
                            'contraprueba: las dos caras tienen que ser distintas')

    def test_el_gancho_y_la_migracion_visten_al_asistente(self):
        import inspect
        from odoo.addons import vp_marca
        self.assertIn('vestir_asistente(env)', inspect.getsource(vp_marca.post_init_hook))
        with file_open('vp_marca/migrations/19.0.1.2.0/post-migrate.py', 'r') as f:
            self.assertIn('vestir_asistente(env)', f.read())

    def test_la_app_instalable_se_llama_ash_erp(self):
        """El manifiesto web lee `web.web_app_name` y, si no esta, pone
        «Odoo» (`web/controllers/webmanifest.py:44`)."""
        self.assertEqual(self.env['ir.config_parameter'].sudo().get_param('web.web_app_name'), 'ASH ERP')


@tagged('post_install', '-at_install', 'vp_marca')
class TestPieDeLosCorreos(TransactionCase):

    def test_ninguno_de_los_dos_pies_enlaza_al_motor(self):
        for xmlid in ('mail.mail_notification_layout', 'mail.mail_notification_light'):
            texto = arch_combinado(self.env, xmlid)
            self.assertNotIn('odoo.com', texto, f'{xmlid} sigue enlazando al motor')
            self.assertIn('ASH ERP', texto, xmlid)

    def test_contraprueba_el_original_si_enlazaba(self):
        with file_open('mail/data/mail_templates_email_layouts.xml', 'r') as f:
            self.assertGreaterEqual(f.read().count('https://www.odoo.com?utm_source=db'), 2)


@tagged('post_install', '-at_install', 'vp_marca')
class TestInterfazWeb(TransactionCase):
    """Lo que se carga en el navegador. El comportamiento en pantalla se
    verifico a mano (titulo, menu, dialogos, logotipo, color); aqui se
    asegura que esos archivos LLEGAN al navegador y que los puntos del motor
    que modifican siguen existiendo."""

    def rutas(self, paquete):
        return [ruta for ruta, *_resto in self.env['ir.asset']._get_asset_paths(paquete, {})]

    def test_el_cliente_web_carga_la_marca(self):
        rutas = self.rutas('web.assets_backend')
        for archivo in ('vp_marca/static/src/js/marca.js', 'vp_marca/static/src/xml/marca.xml',
                        'vp_marca/static/src/scss/marca.scss'):
            self.assertTrue(any(r.endswith(archivo) for r in rutas), f'{archivo} no llega al navegador')

    def test_el_color_se_antepone_a_las_variables_del_motor(self):
        """`$o-community-color` es `!default`: gana quien lo defina primero."""
        rutas = self.rutas('web._assets_primary_variables')
        nuestro = next(i for i, r in enumerate(rutas)
                       if r.endswith('vp_marca/static/src/scss/primary_variables.scss'))
        del_motor = next(i for i, r in enumerate(rutas)
                         if r.endswith('web/static/src/scss/primary_variables.scss'))
        self.assertLess(nuestro, del_motor)

    def test_los_puntos_del_motor_que_se_modifican_siguen_ahi(self):
        """Si una actualizacion del motor los mueve, la marca dejaria de
        aplicarse EN SILENCIO. Mejor que falle aqui."""
        esperado = {
            'web/static/src/core/browser/title_service.js': '|| "Odoo"',
            'web/static/src/webclient/user_menu/user_menu_items.js': '.add("odoo_account", odooAccountItem)',
            'web/static/src/core/errors/error_dialogs.js': '_t("Odoo Server Error")',
            'web/static/src/webclient/navbar/navbar.xml': 't-call="web.NavBar.AppsMenu"',
            'web/static/src/scss/primary_variables.scss': '$o-community-color: #71639e !default;',
            'web/controllers/webmanifest.py': "'web.web_app_name', 'Odoo'",
        }
        for ruta, fragmento in esperado.items():
            with file_open(ruta, 'r') as f:
                self.assertIn(fragmento, f.read(), f'{ruta} cambio: revise la marca')
        with file_open('web/static/src/webclient/user_menu/user_menu_items.js', 'r') as f:
            self.assertIn('.add("support", supportItem)', f.read())

    def test_se_quitan_las_claves_del_registro_no_los_ids(self):
        """El menu del usuario se registra por CLAVE. La de la cuenta del
        fabricante es "odoo_account" aunque su `id` sea "account": quitar
        "account" no quitaba nada. Paso en la primera version."""
        import re
        with file_open('vp_marca/static/src/js/marca.js', 'r') as f:
            claves = re.search(r'ENLACES_DEL_MOTOR = \[([^\]]*)\]', f.read()).group(1)
        with file_open('web/static/src/webclient/user_menu/user_menu_items.js', 'r') as f:
            registradas = re.findall(r'\.add\("(\w+)"', f.read())
        for clave in re.findall(r'"(\w+)"', claves):
            self.assertIn(clave, registradas, f'"{clave}" no es una clave del menu del usuario')

    def test_el_color_es_legible_con_texto_blanco(self):
        """4,5:1 es el minimo de accesibilidad (WCAG AA) para texto normal."""
        import re

        def luminancia(hexa):
            canales = [int(hexa[i:i + 2], 16) / 255 for i in (1, 3, 5)]
            lineal = [c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4 for c in canales]
            return 0.2126 * lineal[0] + 0.7152 * lineal[1] + 0.0722 * lineal[2]
        with file_open('vp_marca/static/src/scss/primary_variables.scss', 'r') as f:
            color = re.search(r'\$o-community-color:\s*(#[0-9A-Fa-f]{6})', f.read()).group(1)
        contraste = 1.05 / (luminancia(color) + 0.05)
        self.assertGreaterEqual(contraste, 4.5, f'{color} da {contraste:.2f}:1 con blanco')
        self.assertLess(1.05 / (luminancia('#017DDB') + 0.05), 4.5,
                        'contraprueba: el azul principal no alcanzaba, por eso se usa el profundo')


@tagged('post_install', '-at_install', 'vp_marca')
class TestTitulosDePaginas(TransactionCase):
    """Paginas que el servidor arma con un titulo de respaldo propio y que no
    pasan por `web.layout`: reportes y conversacion publica."""

    def test_ningun_respaldo_de_titulo_dice_odoo(self):
        for xmlid in ('web.report_layout', 'web.report_preview_layout',
                      'mail.discuss_public_channel_template'):
            texto = arch_combinado(self.env, xmlid)
            self.assertNotIn("'Odoo Report'", texto, xmlid)
            self.assertNotIn("title or 'Odoo'", texto, xmlid)
            self.assertIn("'ASH ERP'", texto, xmlid)

    def test_contraprueba_los_originales_si_lo_decian(self):
        with file_open('web/views/report_templates.xml', 'r') as f:
            self.assertEqual(f.read().count("title or 'Odoo Report'"), 2)
        with file_open('mail/views/discuss_public_templates.xml', 'r') as f:
            original = f.read()
        self.assertIn("title or 'Odoo'", original)
        self.assertIn("/web/static/img/favicon.ico", original)

    def test_la_conversacion_publica_usa_el_icono_de_ash_erp(self):
        texto = arch_combinado(self.env, 'mail.discuss_public_channel_template')
        self.assertNotIn('/web/static/img/favicon.ico', texto)
        self.assertIn('/vp_marca/static/src/img/ash_erp_favicon.png', texto)


@tagged('post_install', '-at_install', 'vp_marca')
class TestIconoDeLaAplicacionInstalada(TransactionCase):
    """El ERP se puede instalar como aplicacion, y el icono era el de Odoo.

    Odoo sirve `/web/manifest.webmanifest` para que el navegador ofrezca
    «añadir a la pantalla de inicio». El NOMBRE ya salia bien —este modulo fija
    el parametro que el motor lee—, pero el icono y los dos colores estan
    escritos a mano en el controlador del motor. Quien instalaba el ERP en su
    telefono se encontraba el icono morado de Odoo con el nombre de ASH.
    """

    def manifiesto(self):
        """El diccionario que el motor sirve, con nuestro controlador encima.

        Se llama al metodo y no a la ruta porque en este repositorio no hay
        ninguna prueba HTTP, y meter un patron nuevo solo para esto añadiria
        mas riesgo que valor. Lo que se prueba es lo mismo: lo que devuelve el
        metodo es exactamente lo que la ruta serializa.
        """
        from types import SimpleNamespace
        from unittest.mock import patch

        from odoo.addons.web.controllers import webmanifest as motor
        from odoo.addons.vp_marca.controllers.main import WebManifestAsh

        with patch.object(motor, 'request', SimpleNamespace(env=self.env)):
            return WebManifestAsh()._get_webmanifest()

    def test_el_icono_de_la_app_es_el_de_ash_y_no_el_de_odoo(self):
        iconos = [i['src'] for i in self.manifiesto()['icons']]
        for fuente in iconos:
            self.assertNotIn('odoo-icon', fuente,
                             'la app instalada sigue mostrando el icono de Odoo')
        self.assertEqual(sorted(iconos), [
            '/vp_marca/static/src/img/ash_erp_app_192.png',
            '/vp_marca/static/src/img/ash_erp_app_512.png'])

    def test_el_motor_SI_trae_el_icono_de_odoo(self):
        """Contraprueba: sin esto, la de arriba pasaria igual si el motor nunca
        hubiera puesto un icono propio, y no demostraria que se sustituyo."""
        with file_open('web/controllers/webmanifest.py', 'r') as archivo:
            original = archivo.read()
        self.assertIn('/web/static/img/odoo-icon-%s.png', original)
        self.assertIn("'#714B67'", original)

    def test_los_colores_son_los_de_la_marca_y_no_el_morado_del_motor(self):
        manifiesto = self.manifiesto()
        self.assertNotEqual(manifiesto['theme_color'], '#714B67')
        self.assertEqual(manifiesto['theme_color'], '#017DDB')
        self.assertEqual(manifiesto['background_color'], '#FFFFFF')

    def test_el_azul_es_el_que_entrego_el_product_owner(self):
        """El color no se escribe a ojo: tiene que ser el del archivo de marca."""
        import json
        from pathlib import Path

        # `file_open` solo resuelve dentro del addons path y esto vive fuera, en
        # `docs/`. Se resuelve desde el propio archivo: vale igual en el
        # repositorio y en la instalacion, donde el arbol cuelga de `app/`.
        raiz = Path(__file__).resolve().parents[3]
        archivo = raiz / 'docs' / 'branding' / 'po_assets' / 'ASH_ERP_colores_marca.json'
        self.assertTrue(archivo.exists(), f'no se encontro {archivo}')
        colores = json.loads(archivo.read_text(encoding='utf-8'))
        self.assertEqual(self.manifiesto()['theme_color'],
                         colores['colors']['azul_principal'])

    def test_el_nombre_sigue_saliendo_de_su_parametro(self):
        """No se toca lo que ya funcionaba: el nombre lo fija este modulo por
        parametro y tiene que seguir llegando por el `super()`."""
        self.assertEqual(self.manifiesto()['name'], 'ASH ERP')

    def test_los_dos_iconos_existen_y_tienen_el_tamaño_que_declaran(self):
        """Una ruta mal escrita aqui no rompe ninguna logica: deja el icono roto
        en la pantalla de inicio del telefono, y nadie se entera."""
        for lado in (192, 512):
            ruta = f'vp_marca/static/src/img/ash_erp_app_{lado}.png'
            with file_open(ruta, 'rb') as archivo:
                datos = archivo.read()
            self.assertTrue(datos.startswith(b'\x89PNG'), f'{ruta} no es un PNG')
            imagen = Image.open(io.BytesIO(datos))
            self.assertEqual(imagen.size, (lado, lado), f'{ruta} no mide {lado}x{lado}')


@tagged('post_install', '-at_install', 'vp_marca')
class TestPantallaDeAcceso(HttpCase):
    """La pantalla de acceso con la cara de CONECTASH (19.0.1.4.0). Se mide
    la pagina servida de verdad, no la plantilla: lo que importa es que el
    formulario del motor siga dentro del marco nuevo."""

    def test_el_marco_nuevo_envuelve_el_formulario_del_motor(self):
        respuesta = self.url_open('/web/login')
        self.assertEqual(respuesta.status_code, 200)
        html = respuesta.text
        self.assertIn('vp_acceso', html)
        self.assertIn('vp_acceso_red', html)
        self.assertIn('Iniciar sesión', html)
        # El formulario sigue siendo el del motor: mismos campos y destino.
        self.assertIn('oe_login_form', html)
        self.assertIn('name="login"', html)
        self.assertIn('name="password"', html)
        self.assertIn('name="csrf_token"', html)
        self.assertNotIn('odoo.com', html)

    def test_sin_selector_de_usuarios_y_con_el_formulario_visible(self):
        html = self.url_open('/web/login').text
        self.assertNotIn('web.user_switch', html)
        self.assertNotIn('oe_login_form d-none', html)

    def test_el_sitio_web_no_tapa_el_marco(self):
        """Regresion de produccion (2026-11-11): con `website` instalado, su
        `website.login_layout` (prioridad 20) cambiaba el marco por el del
        sitio web y la pantalla nueva no se veia. Se mide el marco combinado
        con todas las herencias que haya en la base."""
        from lxml import etree
        arch = etree.tostring(self.env.ref('web.login_layout')._get_combined_arch(), encoding='unicode')
        self.assertIn('vp_acceso_pant', arch)
        self.assertNotIn('website.layout', arch)

    def test_los_estilos_van_en_el_paquete_publico(self):
        rutas = [ruta for ruta, *_resto in self.env['ir.asset']._get_asset_paths('web.assets_frontend', {})]
        for archivo in ('vp_marca/static/src/scss/acceso.scss', 'vp_marca/static/src/js/acceso.js'):
            self.assertTrue(any(r.endswith(archivo) for r in rutas), f'{archivo} no llega al navegador')

    def test_recuperar_contrasena_queda_encendido(self):
        from odoo.addons.vp_marca import activar_recuperar_clave
        parametros = self.env['ir.config_parameter'].sudo()
        parametros.set_param('auth_signup.reset_password', 'False')
        activar_recuperar_clave(self.env)
        self.assertEqual(parametros.get_param('auth_signup.reset_password'), 'True')
        html = self.url_open('/web/login').text
        self.assertIn('/web/reset_password', html)
        self.assertIn('¿Olvidaste tu contraseña?', html)

    def test_sin_registro_abierto_dice_a_quien_pedir_el_usuario(self):
        self.env['ir.config_parameter'].sudo().set_param('auth_signup.invitation_scope', 'b2b')
        # Con `website` manda el campo de cada sitio, y `website_sale` lo trae
        # en «registro libre» (b2c): sin esto, en una base con tienda la
        # pantalla ofreceria registrarse.
        if 'website' in self.env:
            self.env['website'].sudo().search([]).write({'auth_signup_uninvited': 'b2b'})
        html = self.url_open('/web/login').text
        self.assertIn('Pídeselo al administrador de tu empresa', html)
        self.assertNotIn('/web/signup', html)

    def test_recuperar_contrasena_usa_el_marco_nuevo(self):
        self.env['ir.config_parameter'].sudo().set_param('auth_signup.reset_password', 'True')
        html = self.url_open('/web/reset_password').text
        self.assertIn('vp_acceso', html)
        self.assertIn('Recuperar contraseña', html)


@tagged('post_install', '-at_install', 'vp_marca')
class TestRemitenteDeAvisosDeSeguridad(TransactionCase):
    """«Nueva conexión a tu cuenta» y demas avisos de seguridad salen del
    remitente de notificaciones, no del correo de la compañia (ventas@)."""

    def test_el_aviso_sale_del_remitente_por_defecto_del_dominio(self):
        compania = self.env.company
        dominio = self.env['mail.alias.domain'].create({'name': 'ejemplo-ash.test', 'default_from': 'notificaciones'})
        compania.write({'alias_domain_id': dominio.id, 'email': 'ventas@ejemplo-ash.test'})
        usuario = self.env['res.users'].create({
            'name': 'Prueba aviso', 'login': 'prueba.aviso@ejemplo-ash.test',
            'email': 'prueba.aviso@ejemplo-ash.test', 'company_id': compania.id,
            'company_ids': [(6, 0, compania.ids)]})
        # auto_delete apagado: en pruebas el envio se simula y el correo se borraria.
        correos = usuario._notify_security_setting_update('Asunto', 'Contenido', mail_values={'auto_delete': False})
        self.assertIn('notificaciones@ejemplo-ash.test', correos.email_from)
        self.assertNotIn('ventas@', correos.email_from)

    def test_un_remitente_explicito_se_respeta(self):
        usuario = self.env['res.users'].create({
            'name': 'Prueba aviso 2', 'login': 'prueba.aviso2@ejemplo-ash.test',
            'email': 'prueba.aviso2@ejemplo-ash.test'})
        correos = usuario._notify_security_setting_update(
            'Asunto', 'Contenido', mail_values={'email_from': 'otro@ejemplo-ash.test', 'auto_delete': False})
        self.assertEqual(correos.email_from, 'otro@ejemplo-ash.test')

    def test_restablecer_contrasena_sale_de_notificaciones_con_firma(self):
        """El correo de restablecer contraseña lo arma el motor con el correo
        de la compañia; con la marca de contexto pasa a notificaciones@ y
        lleva la firma configurada."""
        compania = self.env.company
        dominio = self.env['mail.alias.domain'].create({'name': 'ejemplo-ash2.test', 'default_from': 'notificaciones'})
        compania.write({'alias_domain_id': dominio.id, 'email': 'ventas@ejemplo-ash2.test'})
        self.env['ir.config_parameter'].sudo().set_param('vp_marca.firma_correo_cuenta', 'https://ejemplo/firma.jpg')
        correo = self.env['mail.mail'].with_context(vp_correo_cuenta=True).create({
            'email_from': compania.email_formatted, 'body_html': '<p>Restablecer</p>',
            'email_to': 'alguien@ejemplo-ash2.test', 'auto_delete': False})
        self.assertIn('notificaciones@ejemplo-ash2.test', correo.email_from)
        self.assertIn('https://ejemplo/firma.jpg', str(correo.body_html))
        # Sin la marca de contexto, nada cambia.
        otro = self.env['mail.mail'].create({
            'email_from': compania.email_formatted, 'body_html': '<p>Otro</p>',
            'email_to': 'alguien@ejemplo-ash2.test', 'auto_delete': False})
        self.assertIn('ventas@', otro.email_from)
