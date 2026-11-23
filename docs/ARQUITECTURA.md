# Arquitectura

## Decisiones

1. **Odoo 19 Community como motor**, igual que ASH ERP (mismo stack, mismo equipo,
   mismas convenciones). Se reutiliza lo que Community ya resuelve bien:
   empleados (`hr`), solicitudes y aprobaciones de ausencias (`hr_holidays`) y
   marcación de asistencia (`hr_attendance`, con kiosco y PIN).
2. **Lo que en Odoo es Enterprise se construye propio**: la programación de
   turnos (Planning) es `ash_rrhh_turnos`; la nómina (Payroll) **no se
   construye**: es Alegra.
3. **Alegra es la fuente de verdad del maestro de empleados y de la nómina.**
   El ERP lee empleados de Alegra y le devuelve novedades. Nunca liquida
   valores en pesos.
4. **Lógica crítica en Python puro** (`addons/*/lib/`): el motor de jornada,
   los festivos, el cliente de Alegra y el exportador no importan Odoo, así que
   se prueban en milisegundos y se pueden reutilizar fuera del ERP.
5. **Parámetros legales con vigencia** (`ash.rrhh.parametro`): la reducción de
   jornada (Ley 2101) y la franja nocturna (Ley 2466) cambian por fechas. Un
   periodo viejo se recalcula con las reglas que regían entonces.

## Flujo de un periodo

```
Alegra ──(cron diario o botón)──► empleados en el ERP
Supervisor: rotación ─► generar turnos (borrador) ─► publicar
Empleado:   marca entrada/salida (kiosco/web/móvil) · solicita permisos
Sistema:    marcación ─► turno publicado ─► tardanza + horas por tipo
Gestor A:   periodo ─► Calcular (asistencia + permisos aprobados + manuales)
Gestor B:   Aprobar (doble control: quien calcula no aprueba)
            ─► Enviar a Alegra (API, por línea, reintentable) o Descargar CSV
Alegra:     liquida y transmite la nómina electrónica
```

## Seguridad

| Grupo | Puede |
|---|---|
| Empleado | ver sus turnos publicados, marcar, solicitar permisos |
| Supervisor | programar turnos, ver asistencia, aprobar permisos de su equipo (implica los grupos nativos de Asistencias y Ausencias que necesita) |
| Gestor RRHH | parámetros, conceptos de Alegra, calcular/aprobar/enviar novedades, conexión con Alegra |
| Administrador | además, ver y cambiar el token de Alegra |

Reglas de registro: el empleado solo ve sus turnos publicados; periodos y
líneas de novedades por compañía. El token de Alegra tiene `groups=base.group_system`
y se redacta de cualquier error que llegue a la bitácora.

## Multiempresa

Cada compañía tiene su propia conexión con Alegra, sus conceptos y sus
periodos. Los festivos y parámetros sin compañía aplican a todas; uno con
compañía la sobrescribe.
