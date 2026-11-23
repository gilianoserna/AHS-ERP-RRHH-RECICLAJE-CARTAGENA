import unittest

from tests import _rutas  # noqa: F401
import exportador_alegra as ex


class TestExportador(unittest.TestCase):
    def test_filas_y_csv(self):
        novedades = [
            {'identificacion': '1047000001', 'empleado': 'PRUEBA Empleado Uno',
             'periodo_desde': '2026-11-01', 'periodo_hasta': '2026-11-15',
             'concepto': 'extra_diurna', 'cantidad': 3},
            {'identificacion': '1047000001', 'empleado': 'PRUEBA Empleado Uno',
             'periodo_desde': '2026-11-01', 'periodo_hasta': '2026-11-15',
             'concepto': 'ordinaria_diurna', 'cantidad': 80},
            {'identificacion': '1047000001', 'empleado': 'PRUEBA Empleado Uno',
             'periodo_desde': '2026-11-01', 'periodo_hasta': '2026-11-15',
             'concepto': 'extra_nocturna', 'cantidad': 0},
        ]
        filas, sin_codigo = ex.filas(novedades)
        self.assertEqual([f['codigo_concepto'] for f in filas], ['HED'])
        self.assertEqual(sin_codigo, ['ordinaria_diurna'])
        texto = ex.a_csv(filas)
        self.assertTrue(texto.startswith('﻿identificacion;empleado'))
        self.assertIn('HED;Hora extra diurna;3.00;horas', texto)


if __name__ == '__main__':
    unittest.main()
