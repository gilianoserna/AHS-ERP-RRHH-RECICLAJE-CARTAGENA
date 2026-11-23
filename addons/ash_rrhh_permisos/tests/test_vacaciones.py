# -*- coding: utf-8 -*-
from datetime import date

from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install', 'ash_rrhh')
class TestVacaciones(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.emp = cls.env['hr.employee'].create({'name': 'PRUEBA Vacaciones'})
        cls.vacaciones = cls.env.ref('ash_rrhh_permisos.leave_vacaciones')

    def test_solo_vacaciones_lleva_saldo(self):
        tipos = self.env['hr.leave.type'].search([('ash_concepto_alegra', '!=', False)])
        con_saldo = tipos.filtered('requires_allocation')
        self.assertIn(self.vacaciones, con_saldo)
        self.assertFalse(self.env.ref('ash_rrhh_permisos.leave_incapacidad_general').requires_allocation)

    def test_arranque_crea_saldo_y_causacion(self):
        asistente = self.env['ash.vacaciones.cargar'].create({
            'fecha_corte': date(2026, 11, 1),
            'linea_ids': [(0, 0, {'employee_id': self.emp.id, 'saldo_inicial': 7.5})]})
        accion = asistente.action_cargar()
        asignaciones = self.env['hr.leave.allocation'].search(accion['domain'])
        self.assertEqual(len(asignaciones), 2)
        self.assertEqual(set(asignaciones.mapped('state')), {'validate'})
        regular = asignaciones.filtered(lambda a: a.allocation_type == 'regular')
        self.assertEqual(regular.number_of_days, 7.5)
        causacion = asignaciones.filtered(lambda a: a.allocation_type == 'accrual')
        self.assertEqual(causacion.accrual_plan_id, self.env.ref('ash_rrhh_permisos.plan_vacaciones_co'))
        # El asistente ya no ofrece a quien tiene causación.
        otro = self.env['ash.vacaciones.cargar'].create({'fecha_corte': date(2026, 11, 1)})
        otro.action_agregar_sin_causacion()
        self.assertNotIn(self.emp, otro.linea_ids.employee_id)
