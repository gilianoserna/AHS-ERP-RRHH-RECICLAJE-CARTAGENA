# -*- coding: utf-8 -*-
# Copyright ASH COLOMBIA SAS. Software propietario.
"""Direccion propia para entrar al ERP: `/ash` ademas de la del motor.

ALCANCE REAL, para no prometer de mas. Esto **anade** una direccion; no
renombra la del motor, que sigue existiendo y a la que el cliente web
vuelve por su cuenta. El enrutador JavaScript comprueba el camino contra
`/odoo` en `web/static/src/core/browser/router.js:325-331`, y hay una
veintena de sitios mas del cliente que construyen enlaces con ese prefijo
(menus, many2one, buscador, PWA, service worker).

Cambiar eso de verdad seria parchear el JavaScript del motor en 19
puntos: contra la regla de cero parches al core, y roto en la siguiente
actualizacion. No se hace.

Lo que si resuelve: la direccion que uno escribe, la que va en un acceso
directo, en un manual o en un correo, puede ser la nuestra.
"""
from odoo.addons.web.controllers.home import Home
from odoo.addons.web.controllers.webmanifest import WebManifest
from odoo.http import route

# El azul principal de la marca, tal como lo entrego el Product Owner en
# `docs/branding/po_assets/ASH_ERP_colores_marca.json`. No se escribe a ojo.
AZUL_MARCA = '#017DDB'
# El fondo del arranque va en BLANCO y no en azul a proposito: el simbolo tiene
# fondo transparente y azul sobre azul se pierde. El color de marca se usa donde
# si se ve —la barra de estado del telefono—. Si se prefiere al reves, son estas
# dos lineas.
FONDO_ARRANQUE = '#FFFFFF'
TAMANOS_ICONO = (192, 512)


class HomeAsh(Home):

    # `readonly=False` es lo mismo que declara el motor para esta pantalla
    # (`_web_client_readonly` devuelve False, web/controllers/home.py:42-43).
    # Se escribe el valor en vez de leerlo por dentro: menos magia, y nada
    # que se rompa si mañana mueven ese ayudante de sitio.
    @route(['/ash', '/ash/<path:subpath>'], type='http', auth='none',
           readonly=False)
    def vp_cliente_web(self, s_action=None, **kw):
        """Misma pantalla que el cliente web, por nuestra direccion."""
        return self.web_client(s_action=s_action, **kw)


class WebManifestAsh(WebManifest):
    """El icono y los colores de la app instalada son los de ASH ERP.

    **Que estaba pasando.** Odoo sirve un `manifest.webmanifest` para que el ERP
    se pueda instalar como aplicacion en el telefono o en el escritorio. El
    NOMBRE ya salia bien —«ASH ERP», porque el motor lo lee de un parametro que
    este modulo ya fijaba—, pero el icono y los dos colores estan **escritos a
    mano** en `web/controllers/webmanifest.py:50-58`: el icono morado de Odoo y
    el morado `#714B67`.

    Resultado: quien instalaba el ERP en su telefono se encontraba el icono de
    Odoo con el nombre de ASH. Aqui se sustituyen las tres cosas.

    Se sobreescribe el metodo que arma el diccionario y no la ruta, que es lo
    que lo hace sobrevivir a una actualizacion del motor: si Odoo agrega mañana
    un campo al manifiesto, llega solo por el `super()`.
    """

    def _get_webmanifest(self):
        manifiesto = super()._get_webmanifest()
        manifiesto['icons'] = [{
            'src': f'/vp_marca/static/src/img/ash_erp_app_{lado}.png',
            'sizes': f'{lado}x{lado}',
            'type': 'image/png',
        } for lado in TAMANOS_ICONO]
        manifiesto['background_color'] = FONDO_ARRANQUE
        manifiesto['theme_color'] = AZUL_MARCA
        return manifiesto
