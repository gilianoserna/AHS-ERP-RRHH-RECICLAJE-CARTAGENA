# -*- coding: utf-8 -*-
"""Traducción entre el JSON de Alegra y los datos del ERP. Python puro.

Los nombres de campo del empleado en la API de nómina de Alegra se leen por
«rutas» (`'identification.number'`, `'contract.startDate'`...) definidas en
`MAPA_EMPLEADO_POR_DEFECTO`; si la API usa otros nombres se ajusta el mapa,
no el código. La huella (`huella`) permite saber si un registro cambió sin
comparar campo por campo: si es igual, no se escribe nada (idempotencia).
"""
import hashlib
import json
from datetime import date, datetime

MAPA_EMPLEADO_POR_DEFECTO = {
    'id_alegra': 'id',
    'tipo_documento': 'identificationType',
    'numero_documento': 'identification',
    'nombres': 'name',
    'primer_apellido': 'lastName',
    'segundo_apellido': 'secondLastName',
    'correo': 'email',
    'telefono': 'phone',
    'cargo': 'position',
    'centro_costo': 'costCenter.name',
    'fecha_ingreso': 'contract.startDate',
    'fecha_retiro': 'contract.endDate',
    'estado': 'status',
}

ESTADOS_ACTIVOS = {'ACTIVE', 'ACTIVO', 'A', '1', 'TRUE'}

TIPOS_DOCUMENTO = {'CC': 'CC', '13': 'CC', 'CE': 'CE', '22': 'CE', 'TI': 'TI', '12': 'TI',
                   'PP': 'PA', 'PA': 'PA', '41': 'PA', 'PEP': 'PEP', '47': 'PEP',
                   'PPT': 'PPT', 'NIT': 'NIT', '31': 'NIT'}


class ErrorMapeo(ValueError):
    pass


def leer(datos, ruta):
    """Lee 'a.b.c' de dicts anidados; None si falta algún tramo."""
    actual = datos
    for parte in ruta.split('.'):
        if not isinstance(actual, dict):
            return None
        actual = actual.get(parte)
    if isinstance(actual, dict):  # p. ej. identification = {'type':..,'number':..}
        actual = actual.get('number') or actual.get('name') or actual.get('id')
    return actual


def _texto(valor):
    return '' if valor is None else str(valor).strip()


def _fecha(valor):
    texto = _texto(valor)
    if not texto:
        return None
    for formato in ('%Y-%m-%d', '%Y-%m-%dT%H:%M:%S', '%d/%m/%Y'):
        try:
            return datetime.strptime(texto[:19], formato).date()
        except ValueError:
            continue
    raise ErrorMapeo(f'Fecha no reconocida: {texto!r}')


def empleado(registro, mapa=None):
    """Empleado de Alegra -> diccionario normalizado del ERP."""
    mapa = mapa or MAPA_EMPLEADO_POR_DEFECTO
    v = {campo: leer(registro, ruta) for campo, ruta in mapa.items()}
    documento = _texto(v.get('numero_documento'))
    if not documento:
        raise ErrorMapeo('Empleado de Alegra sin número de documento')
    nombre = ' '.join(p for p in (_texto(v.get('nombres')), _texto(v.get('primer_apellido')),
                                  _texto(v.get('segundo_apellido'))) if p)
    if not nombre:
        raise ErrorMapeo(f'Empleado {documento} sin nombre')
    tipo_crudo = _texto(v.get('tipo_documento')) or _texto(leer(registro, 'identification.type'))
    retiro = _fecha(v.get('fecha_retiro'))
    estado = _texto(v.get('estado')).upper()
    activo = (estado in ESTADOS_ACTIVOS) if estado else retiro is None
    return {
        'id_alegra': _texto(v.get('id_alegra')) or documento,
        'tipo_documento': TIPOS_DOCUMENTO.get(tipo_crudo.upper(), 'CC'),
        'numero_documento': documento,
        'nombre': nombre,
        'correo': _texto(v.get('correo')).lower() or None,
        'telefono': _texto(v.get('telefono')) or None,
        'cargo': _texto(v.get('cargo')) or None,
        'centro_costo': _texto(v.get('centro_costo')) or None,
        'fecha_ingreso': _fecha(v.get('fecha_ingreso')),
        'fecha_retiro': retiro,
        'activo': activo,
    }


def novedad_a_alegra(linea, id_empleado_alegra, codigos):
    """Línea de novedad del ERP -> cuerpo JSON para Alegra.

    `codigos`: concepto interno -> código/ID del concepto en Alegra.
    Se envía solo lo necesario; los valores en pesos los calcula Alegra.
    """
    concepto = linea['concepto']
    if concepto not in codigos:
        raise ErrorMapeo(f'El concepto {concepto!r} no tiene código de Alegra configurado')
    cuerpo = {
        'employee': {'id': id_empleado_alegra},
        'concept': codigos[concepto],
        'quantity': round(float(linea['cantidad']), 2),
        'startDate': str(linea.get('fecha_inicio') or linea['periodo_desde']),
        'endDate': str(linea.get('fecha_fin') or linea['periodo_hasta']),
    }
    if linea.get('observacion'):
        cuerpo['observations'] = linea['observacion']
    return cuerpo


def huella(datos):
    """SHA-256 estable de un diccionario normalizado."""
    def por_defecto(o):
        if isinstance(o, (date, datetime)):
            return o.isoformat()
        raise TypeError(type(o))
    crudo = json.dumps(datos, sort_keys=True, default=por_defecto, ensure_ascii=False)
    return hashlib.sha256(crudo.encode('utf-8')).hexdigest()


def plan_sincronizacion(normalizados, huellas_actuales):
    """Decide qué crear, actualizar u omitir.

    `huellas_actuales`: {id_alegra: huella guardada en el ERP}. Los `ausentes`
    (están en el ERP pero ya no en Alegra) se reportan, no se archivan solos:
    retirar a alguien es decisión de una persona.
    """
    plan = {'crear': [], 'actualizar': [], 'sin_cambios': [], 'ausentes': []}
    vistos = set()
    for datos in normalizados:
        clave = datos['id_alegra']
        vistos.add(clave)
        h = huella(datos)
        if clave not in huellas_actuales:
            plan['crear'].append((datos, h))
        elif huellas_actuales[clave] != h:
            plan['actualizar'].append((datos, h))
        else:
            plan['sin_cambios'].append(clave)
    plan['ausentes'] = sorted(set(huellas_actuales) - vistos)
    return plan
