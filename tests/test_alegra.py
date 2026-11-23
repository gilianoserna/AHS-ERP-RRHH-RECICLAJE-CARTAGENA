import io
import json
import unittest
import urllib.error
from datetime import date

from tests import _rutas  # noqa: F401
import alegra_client
import mapeo

EMPLEADO = {'id': '7', 'identification': {'type': 'CC', 'number': '1047000001'},
            'name': 'PRUEBA', 'lastName': 'Empleado', 'secondLastName': 'Uno',
            'email': 'Prueba@Ejemplo.test', 'position': 'Auxiliar de bodega',
            'costCenter': {'id': 3, 'name': 'Bodega'},
            'contract': {'startDate': '2024-02-01', 'endDate': None}, 'status': 'active'}


class Respuesta(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


class TestMapeo(unittest.TestCase):
    def test_empleado(self):
        e = mapeo.empleado(EMPLEADO)
        self.assertEqual(e['nombre'], 'PRUEBA Empleado Uno')
        self.assertEqual(e['numero_documento'], '1047000001')
        self.assertEqual(e['tipo_documento'], 'CC')
        self.assertEqual(e['correo'], 'prueba@ejemplo.test')
        self.assertEqual(e['centro_costo'], 'Bodega')
        self.assertEqual(e['fecha_ingreso'], date(2024, 2, 1))
        self.assertTrue(e['activo'])

    def test_retirado(self):
        registro = dict(EMPLEADO, status=None, contract={'startDate': '2024-02-01', 'endDate': '2026-10-31'})
        self.assertFalse(mapeo.empleado(registro)['activo'])

    def test_sin_documento(self):
        with self.assertRaises(mapeo.ErrorMapeo):
            mapeo.empleado(dict(EMPLEADO, identification={'number': ' '}))

    def test_plan_idempotente(self):
        e = mapeo.empleado(EMPLEADO)
        h = mapeo.plan_sincronizacion([e], {})['crear'][0][1]
        plan = mapeo.plan_sincronizacion([e], {'7': h, '99': 'x'})
        self.assertEqual((plan['sin_cambios'], plan['ausentes']), (['7'], ['99']))
        plan = mapeo.plan_sincronizacion([dict(e, cargo='Supervisor')], {'7': h})
        self.assertEqual(len(plan['actualizar']), 1)

    def test_novedad(self):
        linea = {'concepto': 'extra_diurna', 'cantidad': 3, 'periodo_desde': '2026-11-01',
                 'periodo_hasta': '2026-11-15'}
        cuerpo = mapeo.novedad_a_alegra(linea, '7', {'extra_diurna': 'HED'})
        self.assertEqual(cuerpo['employee'], {'id': '7'})
        self.assertEqual(cuerpo['quantity'], 3.0)
        with self.assertRaises(mapeo.ErrorMapeo):
            mapeo.novedad_a_alegra(linea, '7', {})


class TestCliente(unittest.TestCase):
    def test_paginacion(self):
        t = alegra_client.TransporteFalso({'payroll/employees': [{'id': n} for n in range(65)]})
        self.assertEqual(len(alegra_client.ClienteAlegra(t).empleados()), 65)

    def test_http_auth_reintento_y_redaccion(self):
        vistas, llamadas = [], {'n': 0}

        def abridor(peticion, timeout):
            vistas.append(peticion)
            llamadas['n'] += 1
            if llamadas['n'] == 1:
                raise urllib.error.HTTPError(peticion.full_url, 429, 'Too Many', {}, io.BytesIO(b'{}'))
            return Respuesta(json.dumps([EMPLEADO]).encode())

        t = alegra_client.TransporteHttp('c@ejemplo.test', 'TOKEN-SECRETO', abridor=abridor,
                                         dormir=lambda s: None)
        self.assertEqual(t.pedir('GET', 'payroll/employees', {'start': 0}), [EMPLEADO])
        self.assertTrue(vistas[-1].get_header('Authorization').startswith('Basic '))
        self.assertEqual(llamadas['n'], 2)

        def falla(peticion, timeout):
            raise urllib.error.HTTPError(peticion.full_url, 500, 'X', {},
                                         io.BytesIO(b'error con TOKEN-SECRETO'))

        t = alegra_client.TransporteHttp('c@ejemplo.test', 'TOKEN-SECRETO', abridor=falla,
                                         dormir=lambda s: None)
        with self.assertRaises(alegra_client.ErrorAlegra) as ctx:
            t.pedir('GET', 'company')
        self.assertNotIn('TOKEN-SECRETO', str(ctx.exception))
        self.assertEqual(ctx.exception.codigo, 500)


if __name__ == '__main__':
    unittest.main()
