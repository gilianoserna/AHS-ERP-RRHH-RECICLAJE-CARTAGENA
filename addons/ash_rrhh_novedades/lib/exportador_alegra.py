# -*- coding: utf-8 -*-
"""Exportación de novedades del periodo para cargarlas en la nómina de Alegra.

Python puro. Este ERP no liquida ni transmite nómina electrónica: Alegra sigue
siendo el sistema de nómina y el que reporta a la DIAN. Aquí solo se entrega
el insumo (horas extra, recargos, ausencias, incapacidades, vacaciones) en un
archivo que una persona revisa y carga en Alegra.

El formato es una plantilla CSV con columnas configurables: si Alegra cambia
su plantilla de importación, se ajusta `COLUMNAS` sin tocar la lógica. Una
segunda fase puede enviar las novedades por la API de Alegra
(ver docs/FRONTERA_ALEGRA.md).
"""
import csv
import io

COLUMNAS = ('identificacion', 'empleado', 'periodo_desde', 'periodo_hasta', 'codigo_concepto',
            'concepto', 'cantidad', 'unidad', 'fecha_inicio', 'fecha_fin', 'observacion')

# Concepto interno -> (código en Alegra, descripción, unidad). Los códigos se
# ajustan a los conceptos que la empresa tenga creados en Alegra.
CONCEPTOS_POR_DEFECTO = {
    'extra_diurna': ('HED', 'Hora extra diurna', 'horas'),
    'extra_nocturna': ('HEN', 'Hora extra nocturna', 'horas'),
    'extra_dominical_diurna': ('HEDDF', 'Hora extra diurna dominical/festiva', 'horas'),
    'extra_dominical_nocturna': ('HENDF', 'Hora extra nocturna dominical/festiva', 'horas'),
    'ordinaria_nocturna': ('RN', 'Recargo nocturno', 'horas'),
    'dominical_diurna': ('RDDF', 'Recargo dominical/festivo diurno', 'horas'),
    'dominical_nocturna': ('RNDF', 'Recargo nocturno dominical/festivo', 'horas'),
    'vacaciones': ('VAC', 'Vacaciones disfrutadas', 'dias'),
    'incapacidad_general': ('IGE', 'Incapacidad enfermedad general', 'dias'),
    'incapacidad_laboral': ('IRL', 'Incapacidad accidente/enfermedad laboral', 'dias'),
    'licencia_maternidad': ('LMA', 'Licencia de maternidad', 'dias'),
    'licencia_paternidad': ('LPA', 'Licencia de paternidad', 'dias'),
    'licencia_remunerada': ('LR', 'Licencia remunerada', 'dias'),
    'licencia_no_remunerada': ('LNR', 'Licencia no remunerada', 'dias'),
    'ausencia_injustificada': ('AUS', 'Ausencia injustificada', 'dias'),
}


def filas(novedades, conceptos=None):
    """`novedades`: iterable de dicts con identificacion, empleado, periodo_desde,
    periodo_hasta, concepto, cantidad y opcionales fecha_inicio, fecha_fin,
    observacion. Omite cantidades en cero y conceptos sin código."""
    conceptos = conceptos or CONCEPTOS_POR_DEFECTO
    salida, sin_codigo = [], set()
    for n in novedades:
        if not n.get('cantidad'):
            continue
        definicion = conceptos.get(n['concepto'])
        if not definicion:
            sin_codigo.add(n['concepto'])
            continue
        codigo, descripcion, unidad = definicion
        salida.append({
            'identificacion': n['identificacion'], 'empleado': n['empleado'],
            'periodo_desde': str(n['periodo_desde']), 'periodo_hasta': str(n['periodo_hasta']),
            'codigo_concepto': codigo, 'concepto': descripcion,
            'cantidad': f"{float(n['cantidad']):.2f}", 'unidad': unidad,
            'fecha_inicio': str(n.get('fecha_inicio') or ''), 'fecha_fin': str(n.get('fecha_fin') or ''),
            'observacion': n.get('observacion') or '',
        })
    salida.sort(key=lambda f: (f['identificacion'], f['codigo_concepto'], f['fecha_inicio']))
    return salida, sorted(sin_codigo)


def a_csv(filas_exportar, separador=';'):
    """CSV con BOM UTF-8 para que Excel lo abra con tildes correctas."""
    buffer = io.StringIO()
    escritor = csv.DictWriter(buffer, fieldnames=COLUMNAS, delimiter=separador, lineterminator='\r\n')
    escritor.writeheader()
    escritor.writerows(filas_exportar)
    return '﻿' + buffer.getvalue()
