# -*- coding: utf-8 -*-
"""Clasificación de horas trabajadas según la jornada colombiana.

Python puro, sin Odoo. Este ERP NO liquida nómina (eso lo hace Alegra): solo
cuenta HORAS por tipo, que es lo que Alegra necesita como novedad.

Tipos que produce (minutos):
    ordinaria_diurna, ordinaria_nocturna,
    dominical_diurna, dominical_nocturna,          (domingo o festivo)
    extra_diurna, extra_nocturna,
    extra_dominical_diurna, extra_dominical_nocturna

Reglas parametrizables (vienen de `ash.rrhh.parametro` con fecha de vigencia,
nunca fijas en el código, porque la ley cambia por etapas):
    inicio_nocturno / fin_nocturno: franja nocturna (Ley 2466 de 2025: 19:00-06:00)
    minutos_programados: lo que el turno asignado prometía; lo que exceda es extra.

La resolución es por minuto: simple, exacta y suficiente para turnos humanos.
"""
from dataclasses import dataclass, field
from datetime import datetime, time, timedelta

TIPOS = ('ordinaria_diurna', 'ordinaria_nocturna', 'dominical_diurna', 'dominical_nocturna',
         'extra_diurna', 'extra_nocturna', 'extra_dominical_diurna', 'extra_dominical_nocturna')


@dataclass(frozen=True)
class ReglasJornada:
    inicio_nocturno: time = time(19, 0)
    fin_nocturno: time = time(6, 0)
    festivos: frozenset = field(default_factory=frozenset)

    def es_nocturno(self, momento):
        t = momento.time()
        if self.inicio_nocturno > self.fin_nocturno:  # franja que cruza medianoche
            return t >= self.inicio_nocturno or t < self.fin_nocturno
        return self.inicio_nocturno <= t < self.fin_nocturno

    def es_dominical(self, momento):
        return momento.weekday() == 6 or momento.date() in self.festivos


def clasificar(inicio, fin, reglas, minutos_programados=None, descansos=()):
    """Reparte el intervalo [inicio, fin) en minutos por tipo.

    `descansos`: intervalos (inicio, fin) que no cuentan como trabajo.
    `minutos_programados`: si se da, los minutos trabajados más allá de ese
    total se clasifican como extra (en el orden en que ocurren).
    """
    if fin <= inicio:
        raise ValueError('El fin debe ser posterior al inicio')
    totales = dict.fromkeys(TIPOS, 0)
    trabajados = 0
    momento = inicio.replace(second=0, microsecond=0)
    un_minuto = timedelta(minutes=1)
    while momento < fin:
        if not any(d_ini <= momento < d_fin for d_ini, d_fin in descansos):
            trabajados += 1
            extra = minutos_programados is not None and trabajados > minutos_programados
            nocturno = reglas.es_nocturno(momento)
            dominical = reglas.es_dominical(momento)
            franja = 'nocturna' if nocturno else 'diurna'
            if extra:
                clave = f'extra_dominical_{franja}' if dominical else f'extra_{franja}'
            else:
                clave = f'dominical_{franja}' if dominical else f'ordinaria_{franja}'
            totales[clave] += 1
        momento += un_minuto
    return totales


def a_horas(minutos_por_tipo):
    """Convierte a horas con dos decimales, omitiendo los tipos en cero."""
    return {k: round(v / 60.0, 2) for k, v in minutos_por_tipo.items() if v}


def minutos_semana(intervalos, descansos=()):
    """Total de minutos de una lista de intervalos (para el tope semanal)."""
    total = 0
    for ini, fin in intervalos:
        total += int((fin - ini).total_seconds() // 60)
    for ini, fin in descansos:
        total -= int((fin - ini).total_seconds() // 60)
    return total


def traslapan(a_ini, a_fin, b_ini, b_fin):
    return a_ini < b_fin and b_ini < a_fin


def descanso_entre(fin_anterior, inicio_siguiente):
    """Horas de descanso entre dos turnos consecutivos."""
    return (inicio_siguiente - fin_anterior).total_seconds() / 3600.0


def combinar(fecha, hora_decimal):
    """date + 7.5 -> datetime(fecha 07:30). 24.0 o más pasa al día siguiente."""
    dias, resto = divmod(hora_decimal, 24)
    horas = int(resto)
    minutos = int(round((resto - horas) * 60))
    return datetime.combine(fecha, time(0, 0)) + timedelta(days=dias, hours=horas, minutes=minutos)
