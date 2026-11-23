# -*- coding: utf-8 -*-
"""Los tipos de ausencia se cargaron con noupdate y con la asignación previa
que Odoo pone por defecto: una incapacidad o una licencia no se podía pedir
sin saldo. Solo las vacaciones llevan saldo."""
from odoo import SUPERUSER_ID, api

SIN_SALDO = ['leave_incapacidad_general', 'leave_incapacidad_laboral', 'leave_maternidad',
             'leave_paternidad', 'leave_luto', 'leave_calamidad', 'leave_remunerada',
             'leave_no_remunerada', 'leave_sindical', 'leave_cita_medica', 'leave_injustificada']


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    for xmlid in SIN_SALDO:
        tipo = env.ref(f'ash_rrhh_permisos.{xmlid}', raise_if_not_found=False)
        if tipo:
            tipo.requires_allocation = False
