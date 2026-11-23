# -*- coding: utf-8 -*-
from datetime import date, datetime

from odoo.exceptions import ValidationError
from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install', 'ash_rrhh')
class TestTurnos(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.emp = cls.env['hr.employee'].create({'name': 'PRUEBA Turnos', 'tz': 'America/Bogota'})
        Plantilla = cls.env['ash.turno.plantilla']
        cls.manana = Plantilla.create({'name': 'Mañana', 'codigo': 'M', 'hora_inicio': 6, 'hora_fin': 14})
        cls.noche = Plantilla.create({'name': 'Noche', 'codigo': 'N', 'hora_inicio': 22, 'hora_fin': 6})

    def test_festivos_y_parametros(self):
        self.env['ash.rrhh.festivo'].generar_anio(2026)
        festivos = self.env['ash.rrhh.festivo'].conjunto(date(2026, 1, 1), date(2026, 12, 31))
        self.assertIn(date(2026, 11, 16), festivos)
        Parametro = self.env['ash.rrhh.parametro']
        self.assertEqual(Parametro.valor_en('inicio_nocturno', date(2025, 6, 1)), 21.0)
        self.assertEqual(Parametro.valor_en('inicio_nocturno', date(2026, 1, 10)), 19.0)
        self.assertEqual(Parametro.valor_en('jornada_max_semanal', date(2026, 11, 22)), 42)

    def test_intervalo_en_utc_y_turno_nocturno(self):
        a = self.env['ash.turno.asignacion'].create({
            'employee_id': self.emp.id, 'fecha': date(2026, 11, 23), 'plantilla_id': self.noche.id})
        # Bogotá es UTC-5: 22:00 local = 03:00 UTC del día siguiente.
        self.assertEqual(a.inicio, datetime(2026, 11, 24, 3, 0))
        self.assertEqual(a.fin, datetime(2026, 11, 24, 11, 0))
        self.assertEqual(a.minutos_programados, 480)

    def test_traslape_y_descanso_minimo(self):
        Asignacion = self.env['ash.turno.asignacion']
        Asignacion.create({'employee_id': self.emp.id, 'fecha': date(2026, 11, 23), 'plantilla_id': self.noche.id})
        with self.assertRaises(ValidationError):
            # Mañana del 24 empieza a las 06:00, justo cuando termina la noche: sin descanso.
            Asignacion.create({'employee_id': self.emp.id, 'fecha': date(2026, 11, 24),
                               'plantilla_id': self.manana.id})

    def test_generar_desde_rotacion(self):
        rotacion = self.env['ash.turno.rotacion'].create({'name': '2x1', 'linea_ids': [
            (0, 0, {'secuencia': 1, 'plantilla_id': self.manana.id}),
            (0, 0, {'secuencia': 2, 'plantilla_id': self.manana.id}),
            (0, 0, {'secuencia': 3, 'plantilla_id': False})]})
        asistente = self.env['ash.turno.generar'].create({
            'employee_ids': [(6, 0, self.emp.ids)], 'rotacion_id': rotacion.id,
            'fecha_desde': date(2026, 11, 23), 'fecha_hasta': date(2026, 11, 28)})
        accion = asistente.action_generar()
        creadas = self.env['ash.turno.asignacion'].search(accion['domain'])
        self.assertEqual(len(creadas), 4)
        self.assertEqual(set(creadas.mapped('estado')), {'borrador'})
