# -*- coding: utf-8 -*-
"""Festivos de Colombia (Ley 51 de 1983, «Ley Emiliani»).

Python puro, sin Odoo: se prueba con unittest en CI.

Tres clases de festivo:
* fijos: caen en su fecha;
* trasladables: si no caen en lunes, pasan al lunes siguiente;
* dependientes de la Pascua: Jueves y Viernes Santo en su fecha; Ascensión,
  Corpus Christi y Sagrado Corazón se trasladan al lunes.

El modelo `ash.rrhh.festivo` permite agregar o quitar fechas a mano (por
ejemplo, un día cívico decretado), de modo que esta función es el punto de
partida, no la última palabra.
"""
from datetime import date, timedelta

FIJOS = [(1, 1, 'Año Nuevo'), (5, 1, 'Día del Trabajo'), (7, 20, 'Independencia'),
         (8, 7, 'Batalla de Boyacá'), (12, 8, 'Inmaculada Concepción'), (12, 25, 'Navidad')]

TRASLADABLES = [(1, 6, 'Reyes Magos'), (3, 19, 'San José'), (6, 29, 'San Pedro y San Pablo'),
                (8, 15, 'Asunción de la Virgen'), (10, 12, 'Día de la Raza'),
                (11, 1, 'Todos los Santos'), (11, 11, 'Independencia de Cartagena')]

# (días desde el domingo de Pascua, nombre, ¿se traslada al lunes?)
PASCUALES = [(-3, 'Jueves Santo', False), (-2, 'Viernes Santo', False),
             (39, 'Ascensión del Señor', True), (60, 'Corpus Christi', True),
             (68, 'Sagrado Corazón', True)]


def domingo_de_pascua(anio):
    """Algoritmo anónimo gregoriano (Meeus/Jones/Butcher)."""
    a = anio % 19
    b, c = divmod(anio, 100)
    d, e = divmod(b, 4)
    f = (b + 8) // 25
    g = (b - f + 1) // 3
    h = (19 * a + b - d - g + 15) % 30
    i, k = divmod(c, 4)
    l = (32 + 2 * e + 2 * i - h - k) % 7
    m = (a + 11 * h + 22 * l) // 451
    mes, dia = divmod(h + l - 7 * m + 114, 31)
    return date(anio, mes, dia + 1)


def al_lunes(fecha):
    """El mismo día si ya es lunes; si no, el lunes siguiente."""
    return fecha + timedelta(days=(7 - fecha.weekday()) % 7)


def festivos(anio):
    """Diccionario {fecha: nombre} con los 18 festivos del año."""
    resultado = {}
    for mes, dia, nombre in FIJOS:
        resultado[date(anio, mes, dia)] = nombre
    for mes, dia, nombre in TRASLADABLES:
        resultado[al_lunes(date(anio, mes, dia))] = nombre
    pascua = domingo_de_pascua(anio)
    for dias, nombre, traslada in PASCUALES:
        fecha = pascua + timedelta(days=dias)
        resultado[al_lunes(fecha) if traslada else fecha] = nombre
    return resultado
