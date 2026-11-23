# ORACLE — Gestión de empleados (ASH RRHH)

ERP **solo de gestión de empleados** para ASH COLOMBIA SAS, construido con la
misma base técnica que ASH ERP: **Odoo 19 Community (LGPL-3), sin modificar**,
más addons propios.

> La **nómina electrónica sigue en Alegra**. Este ERP no liquida nómina ni
> transmite a la DIAN: controla permisos, turnos y asistencia, y le entrega a
> Alegra las **novedades** del periodo (horas extra, recargos, ausencias).

```
 Alegra (nómina electrónica, DIAN)
   ▲ novedades aprobadas            │ empleados (maestro)
   │ (API o CSV)                     ▼
 ┌──────────────────── ORACLE / ASH RRHH (Odoo 19 Community) ───────────────────┐
 │ ash_alegra_conector   API de Alegra: trae empleados, envía novedades, bitácora │
 │ ash_rrhh_novedades    cierre de periodo → novedades → aprobación → envío       │
 │ ash_rrhh_asistencia   marcaciones (hr_attendance) contra turno, horas por tipo │
 │ ash_rrhh_turnos       plantillas, rotaciones, programación, validaciones       │
 │ ash_rrhh_permisos     vacaciones, incapacidades, licencias (hr_holidays)       │
 │ ash_rrhh_base         datos CO del empleado, grupos, festivos, parámetros ley  │
 └──────────────────────────────────────────────────────────────────────────────┘
```

## Módulos

| Addon | Qué hace | Se apoya en (Odoo Community) |
|---|---|---|
| `ash_rrhh_base` | Documento, EPS/AFP/ARL/caja/cesantías, ID de Alegra; grupos Empleado / Supervisor / Gestor RRHH; festivos de Colombia (Ley Emiliani); parámetros laborales con fecha de vigencia | `hr` |
| `ash_rrhh_permisos` | 12 tipos de ausencia colombianos, concepto de Alegra por tipo, soporte obligatorio para incapacidades y licencias | `hr_holidays` |
| `ash_rrhh_turnos` | Plantillas (incluye turnos nocturnos), rotaciones, asistente de programación, publicación, sin traslapes, descanso mínimo, alerta de tope semanal | propio (Planning es Enterprise) |
| `ash_rrhh_asistencia` | Cruza cada marcación con el turno publicado: tardanza, horas ordinarias / nocturnas / dominicales-festivas / extras | `hr_attendance` |
| `ash_rrhh_novedades` | Periodo → calcular → aprobar (doble control) → CSV para Alegra | — |
| `ash_alegra_conector` | API de Alegra: empleados (idempotente) y envío de novedades por línea; modo Ensayo sin red; bitácora | — |

Detalle: [`docs/ARQUITECTURA.md`](docs/ARQUITECTURA.md) ·
[`docs/INTEGRACION_ALEGRA.md`](docs/INTEGRACION_ALEGRA.md) ·
[`docs/REGLAS_LABORALES.md`](docs/REGLAS_LABORALES.md) ·
[`docs/ODOO_REUTILIZADO.md`](docs/ODOO_REUTILIZADO.md)

## Probar en local

```bash
docker compose up -d
# Abrir http://localhost:8069, crear la base e instalar «ASH RRHH — Conector API de Alegra»
# (arrastra los demás módulos).
```

Pruebas sin Odoo (lógica pura: jornada, festivos, Alegra, exportador):

```bash
python -m unittest discover -s . -p 'test_*.py' -t .
```

Pruebas dentro de Odoo 19 (las corre la CI en cada PR):

```bash
odoo-bin -d prueba --addons-path=<odoo>/addons,addons -i ash_alegra_conector \
  --test-enable --test-tags=ash_rrhh --stop-after-init
```

## Reglas

- **0 parches al core de Odoo** y **nada de Enterprise**.
- **Sin datos reales ni credenciales en el repositorio.** El token de Alegra se
  escribe en la pantalla de conexión (solo administradores lo ven).
- **Las reglas laborales son datos con vigencia**, no constantes en el código.
- El conector arranca en **modo Ensayo**: nada sale hacia Alegra hasta que una
  persona lo pase a Real.
