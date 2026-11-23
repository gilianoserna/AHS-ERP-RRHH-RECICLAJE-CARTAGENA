import unittest
from datetime import date, datetime, time

from tests import _rutas  # noqa: F401
import jornada

REGLAS = jornada.ReglasJornada(inicio_nocturno=time(19, 0), fin_nocturno=time(6, 0),
                               festivos=frozenset({date(2026, 12, 8)}))


class TestJornada(unittest.TestCase):
    def test_turno_diurno_entre_semana(self):
        r = jornada.clasificar(datetime(2026, 11, 23, 8), datetime(2026, 11, 23, 16), REGLAS)
        self.assertEqual(jornada.a_horas(r), {'ordinaria_diurna': 8.0})

    def test_turno_que_cruza_la_franja_nocturna(self):
        r = jornada.clasificar(datetime(2026, 11, 23, 14), datetime(2026, 11, 23, 22), REGLAS)
        self.assertEqual(jornada.a_horas(r), {'ordinaria_diurna': 5.0, 'ordinaria_nocturna': 3.0})

    def test_domingo_y_paso_a_lunes(self):
        # Domingo 22:00 a lunes 06:00: 2 h dominicales nocturnas, 6 h nocturnas ordinarias.
        r = jornada.clasificar(datetime(2026, 11, 22, 22), datetime(2026, 11, 23, 6), REGLAS)
        self.assertEqual(jornada.a_horas(r), {'dominical_nocturna': 2.0, 'ordinaria_nocturna': 6.0})

    def test_festivo(self):
        r = jornada.clasificar(datetime(2026, 12, 8, 6), datetime(2026, 12, 8, 14), REGLAS)
        self.assertEqual(jornada.a_horas(r), {'dominical_diurna': 8.0})

    def test_extras_sobre_lo_programado(self):
        r = jornada.clasificar(datetime(2026, 11, 23, 8), datetime(2026, 11, 23, 20), REGLAS,
                               minutos_programados=8 * 60)
        self.assertEqual(jornada.a_horas(r), {'ordinaria_diurna': 8.0, 'extra_diurna': 3.0,
                                              'extra_nocturna': 1.0})

    def test_descanso_no_cuenta(self):
        descanso = [(datetime(2026, 11, 23, 12), datetime(2026, 11, 23, 13))]
        r = jornada.clasificar(datetime(2026, 11, 23, 8), datetime(2026, 11, 23, 17), REGLAS,
                               descansos=descanso)
        self.assertEqual(jornada.a_horas(r), {'ordinaria_diurna': 8.0})

    def test_fin_antes_de_inicio(self):
        with self.assertRaises(ValueError):
            jornada.clasificar(datetime(2026, 11, 23, 8), datetime(2026, 11, 23, 8), REGLAS)

    def test_combinar_y_descanso(self):
        self.assertEqual(jornada.combinar(date(2026, 11, 23), 22.5), datetime(2026, 11, 23, 22, 30))
        self.assertEqual(jornada.combinar(date(2026, 11, 23), 30), datetime(2026, 11, 24, 6))
        self.assertEqual(jornada.descanso_entre(datetime(2026, 11, 23, 22), datetime(2026, 11, 24, 6)), 8.0)


if __name__ == '__main__':
    unittest.main()
