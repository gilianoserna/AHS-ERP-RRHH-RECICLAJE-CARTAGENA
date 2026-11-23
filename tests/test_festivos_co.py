import unittest
from datetime import date

from tests import _rutas  # noqa: F401
import festivos_co


class TestFestivos(unittest.TestCase):
    def test_pascua(self):
        self.assertEqual(festivos_co.domingo_de_pascua(2025), date(2025, 4, 20))
        self.assertEqual(festivos_co.domingo_de_pascua(2026), date(2026, 4, 5))

    def test_2026(self):
        f = festivos_co.festivos(2026)
        self.assertEqual(len(f), 18)
        esperados = [date(2026, 1, 1), date(2026, 1, 12), date(2026, 3, 23), date(2026, 4, 2),
                     date(2026, 4, 3), date(2026, 5, 1), date(2026, 5, 18), date(2026, 6, 8),
                     date(2026, 6, 15), date(2026, 6, 29), date(2026, 7, 20), date(2026, 8, 7),
                     date(2026, 8, 17), date(2026, 10, 12), date(2026, 11, 2), date(2026, 11, 16),
                     date(2026, 12, 8), date(2026, 12, 25)]
        self.assertEqual(sorted(f), esperados)

    def test_trasladables_caen_en_lunes(self):
        for anio in range(2024, 2031):
            for fecha, nombre in festivos_co.festivos(anio).items():
                if nombre in [n for _, _, n in festivos_co.TRASLADABLES]:
                    self.assertEqual(fecha.weekday(), 0, (anio, nombre))


if __name__ == '__main__':
    unittest.main()
