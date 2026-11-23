# -*- coding: utf-8 -*-
"""Flujo completo en modo ensayo: Alegra -> empleados -> turno -> asistencia ->
novedades -> aprobación -> envío. Nada sale a la red."""
from datetime import date, datetime

from odoo.exceptions import UserError
from odoo.tests import TransactionCase, new_test_user, tagged

EMPLEADOS_ALEGRA = [
    {'id': '501', 'identification': {'type': 'CC', 'number': '1047000501'}, 'name': 'PRUEBA',
     'lastName': 'Alegra', 'email': 'prueba.alegra@ejemplo.test', 'position': 'Operario',
     'contract': {'startDate': '2025-01-15'}, 'status': 'active'},
    {'id': '502', 'identification': {'number': ''}, 'name': 'SIN DOCUMENTO'},
]


@tagged('post_install', '-at_install', 'ash_rrhh')
class TestFlujoAlegra(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.conexion = cls.env['ash.alegra.conexion'].create({'name': 'Prueba', 'modo': 'ensayo'})
        cls.calcula = new_test_user(cls.env, 'prueba.calcula', groups='ash_rrhh_base.group_ash_rrhh_gestor')
        cls.aprueba = new_test_user(cls.env, 'prueba.aprueba', groups='ash_rrhh_base.group_ash_rrhh_gestor')

    def test_flujo(self):
        bitacora = self.conexion._sincronizar_empleados(EMPLEADOS_ALEGRA)
        self.assertEqual((bitacora.creados, bitacora.resultado), (1, 'error'))
        emp = self.env['hr.employee'].search([('ash_id_alegra', '=', '501')])
        self.assertEqual(emp.name, 'PRUEBA Alegra')
        self.assertEqual(emp.job_title, 'Operario')
        self.assertEqual(emp.ash_fecha_ingreso, date(2025, 1, 15))
        self.assertFalse(emp.ash_fecha_retiro)
        # Segunda pasada sin cambios: no escribe nada.
        segunda = self.conexion._sincronizar_empleados(EMPLEADOS_ALEGRA[:1])
        self.assertEqual((segunda.creados, segunda.actualizados, segunda.sin_cambios), (0, 0, 1))

        emp.tz = 'America/Bogota'
        plantilla = self.env['ash.turno.plantilla'].create(
            {'name': 'Tarde', 'codigo': 'T', 'hora_inicio': 14, 'hora_fin': 22})
        turno = self.env['ash.turno.asignacion'].create(
            {'employee_id': emp.id, 'fecha': date(2026, 11, 3), 'plantilla_id': plantilla.id})
        turno.action_publicar()
        # Martes 3 nov: entra 14:10 y sale 23:00 hora Bogotá (19:10-04:00 UTC).
        att = self.env['hr.attendance'].create({'employee_id': emp.id,
                                                'check_in': datetime(2026, 11, 3, 19, 10),
                                                'check_out': datetime(2026, 11, 4, 4, 0)})
        self.assertEqual(att.ash_asignacion_id, turno)
        self.assertEqual(att.ash_minutos_tarde, 10)
        self.assertAlmostEqual(att.ash_h_ordinaria_diurna, 4.83, places=2)
        # Llegó 10 min tarde: las 8 h programadas se cumplen a las 22:10; lo demás es extra.
        self.assertAlmostEqual(att.ash_h_ordinaria_nocturna, 3.17, places=2)
        self.assertAlmostEqual(att.ash_h_extra_nocturna, 0.83, places=2)

        periodo = self.env['ash.novedad.periodo'].with_user(self.calcula).create({
            'name': '1Q nov 2026', 'fecha_desde': date(2026, 11, 1), 'fecha_hasta': date(2026, 11, 15)})
        periodo.action_calcular()
        conceptos = {l.concepto: l.cantidad for l in periodo.linea_ids}
        self.assertEqual(conceptos, {'ordinaria_nocturna': 3.17, 'extra_nocturna': 0.83})
        with self.assertRaises(UserError):
            periodo.action_aprobar()  # doble control: quien calcula no aprueba
        periodo.with_user(self.aprueba).action_aprobar()
        self.assertEqual(periodo.estado, 'aprobado')

        periodo = periodo.with_user(self.aprueba)
        filas, sin_codigo = periodo._filas_exportar()
        self.assertEqual(sorted(f['codigo_concepto'] for f in filas), ['HEN', 'RN'])
        self.assertFalse(sin_codigo)
        periodo.action_enviar_alegra()
        self.assertEqual(periodo.estado, 'enviado')
        self.assertEqual(set(periodo.linea_ids.mapped('estado_envio')), {'enviado'})
