# -*- coding: utf-8 -*-
"""Cliente de la API REST de Alegra, independiente de Odoo.

Alegra sigue siendo el sistema de NÓMINA ELECTRÓNICA (liquida y transmite a la
DIAN). Este ERP solo:
  * LEE de Alegra los empleados (Alegra es la fuente de verdad del maestro), y
  * ENVÍA a Alegra las novedades del periodo (horas extra, recargos,
    ausencias, incapacidades, vacaciones) para que Alegra liquide.

Lo confirmado de la API pública de Alegra (https://developer.alegra.com):
  * URL base `https://api.alegra.com/api/v1`;
  * autenticación básica `correo:token` (el token se genera en Alegra >
    Configuración > Integraciones / API);
  * paginación con `start` y `limit` (máximo 30 por página);
  * límite de peticiones por minuto: responde 429 (a veces 400 con code 429).

Las RUTAS de nómina (empleados y novedades) se configuran en
`RUTAS_POR_DEFECTO` y en la pantalla de conexión, porque hay que confirmarlas
contra la documentación de nómina de la cuenta de la empresa antes de
producción (ver docs/INTEGRACION_ALEGRA.md). Si la cuenta no expone novedades
por API, el ERP usa el archivo CSV de `ash_rrhh_novedades` como respaldo.

Seguridad: nunca se registran credenciales; `redactar()` las oculta de los
mensajes de error que van a la bitácora.
"""
import base64
import json
import time
import urllib.error
import urllib.parse
import urllib.request

URL_BASE = 'https://api.alegra.com/api/v1'
LIMITE_PAGINA = 30

# Confirmar con la documentación de nómina de Alegra de la cuenta.
RUTAS_POR_DEFECTO = {
    'empleados': 'payroll/employees',
    'novedades': 'payroll/novelties',
    'prueba_conexion': 'company',
}


class ErrorAlegra(Exception):
    """Fallo de comunicación o respuesta inválida de Alegra."""

    def __init__(self, mensaje, codigo=None):
        super().__init__(mensaje)
        self.codigo = codigo


def redactar(texto, secretos):
    for s in secretos:
        if s:
            texto = texto.replace(s, '***')
    return texto


class TransporteAlegra:
    """Interfaz común: `pedir(metodo, ruta, params, cuerpo) -> JSON`."""

    def pedir(self, metodo, ruta, params=None, cuerpo=None):
        raise NotImplementedError


class TransporteHttp(TransporteAlegra):
    def __init__(self, correo, token, url_base=URL_BASE, timeout=60, reintentos=4,
                 espera_base=20, abridor=None, dormir=time.sleep):
        self._secretos = [correo, token]
        par = f'{correo}:{token}'.encode('utf-8')
        self._auth = 'Basic ' + base64.b64encode(par).decode('ascii')
        self._secretos.append(self._auth)
        self.url_base = url_base.rstrip('/')
        self.timeout, self.reintentos, self.espera_base = timeout, reintentos, espera_base
        self._abrir = abridor or urllib.request.urlopen
        self._dormir = dormir

    def pedir(self, metodo, ruta, params=None, cuerpo=None):
        url = f'{self.url_base}/{ruta.lstrip("/")}'
        if params:
            url += '?' + urllib.parse.urlencode(params)
        datos = json.dumps(cuerpo).encode('utf-8') if cuerpo is not None else None
        encabezados = {'Authorization': self._auth, 'Accept': 'application/json'}
        if datos is not None:
            encabezados['Content-Type'] = 'application/json'
        for intento in range(self.reintentos + 1):
            peticion = urllib.request.Request(url, data=datos, headers=encabezados, method=metodo)
            try:
                with self._abrir(peticion, timeout=self.timeout) as r:
                    texto = r.read().decode('utf-8')
                    return json.loads(texto) if texto else None
            except urllib.error.HTTPError as e:
                cuerpo_error = e.read().decode('utf-8', 'replace')[:500]
                limite = e.code == 429 or '"code":429' in cuerpo_error.replace(' ', '')
                if limite and intento < self.reintentos:
                    self._dormir(self.espera_base * (intento + 1))
                    continue
                if e.code == 401:
                    raise ErrorAlegra('Alegra respondió 401: revise el correo y el token de la API.', 401) from None
                raise ErrorAlegra(redactar(f'Alegra respondió {e.code} en /{ruta}: {cuerpo_error}',
                                           self._secretos), e.code) from None
            except (urllib.error.URLError, OSError) as e:
                if intento < self.reintentos:
                    self._dormir(self.espera_base)
                    continue
                raise ErrorAlegra(redactar(f'Sin conexión con Alegra: {e}', self._secretos)) from None
        raise ErrorAlegra('Alegra no respondió tras varios intentos')


class TransporteFalso(TransporteAlegra):
    """Para pruebas y modo «ensayo»: responde con datos dados y guarda lo enviado."""

    def __init__(self, datos_por_ruta=None):
        self.datos = datos_por_ruta or {}
        self.enviados = []

    def pedir(self, metodo, ruta, params=None, cuerpo=None):
        if metodo == 'GET':
            filas = self.datos.get(ruta, [])
            if isinstance(filas, list) and params and 'start' in params:
                ini = int(params['start'])
                return filas[ini: ini + int(params.get('limit', LIMITE_PAGINA))]
            return filas
        self.enviados.append((metodo, ruta, cuerpo))
        return {'id': len(self.enviados), **(cuerpo or {})}


class ClienteAlegra:
    def __init__(self, transporte, rutas=None):
        self.t = transporte
        self.rutas = dict(RUTAS_POR_DEFECTO, **(rutas or {}))

    def probar_conexion(self):
        return self.t.pedir('GET', self.rutas['prueba_conexion'])

    def listar(self, ruta, params=None, max_paginas=2000):
        """Recorre todas las páginas de un listado (start/limit)."""
        filas, start = [], 0
        for _ in range(max_paginas):
            p = dict(params or {}, start=start, limit=LIMITE_PAGINA)
            lote = self.t.pedir('GET', ruta, p)
            if isinstance(lote, dict):
                lote = lote.get('data') or lote.get('items') or []
            filas.extend(lote)
            if len(lote) < LIMITE_PAGINA:
                break
            start += LIMITE_PAGINA
        return filas

    def empleados(self):
        return self.listar(self.rutas['empleados'])

    def enviar_novedad(self, novedad):
        """Crea una novedad en Alegra. `novedad` ya viene en el formato de la API."""
        return self.t.pedir('POST', self.rutas['novedades'], cuerpo=novedad)
