# -*- coding: utf-8 -*-
# Copyright ASH COLOMBIA SAS. Software propietario.
"""Filtrar lo Enterprise en las listas QUE VE LA PERSONA, no en la base.

Primera version: se cambiaba el dominio de la accion de Aplicaciones. No
servia: `website` redefine esa misma accion (para esconder los temas) y, al
cargarse despues, pisaba el cambio; y devolverla a «vacio» al desinstalar
habria borrado tambien el filtro de `website`.

Ahora se filtran las lecturas de la INTERFAZ —`web_search_read` (listas y
kanban) y `web_read_group` (vistas agrupadas)—, que son las que usa el
navegador. Las busquedas internas de Odoo (instalar, actualizar la lista de
aplicaciones, resolver dependencias) no pasan por aqui y siguen viendo todo:
ocultar no es borrar. No depende del orden de carga ni deja nada que
restaurar al desinstalar.
"""
from odoo.fields import Domain


def con_community(domain, condicion):
    """El dominio de la interfaz, restringido a lo que es de Community."""
    return Domain(domain or []) & Domain(condicion)
