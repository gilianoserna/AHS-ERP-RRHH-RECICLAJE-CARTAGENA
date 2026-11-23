# -*- coding: utf-8 -*-
"""Pone en sys.path las carpetas lib/ de los addons: son Python puro y se
prueban sin Odoo."""
import os
import sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for addon in sorted(os.listdir(os.path.join(RAIZ, 'addons'))):
    lib = os.path.join(RAIZ, 'addons', addon, 'lib')
    if os.path.isdir(lib) and lib not in sys.path:
        sys.path.insert(0, lib)
