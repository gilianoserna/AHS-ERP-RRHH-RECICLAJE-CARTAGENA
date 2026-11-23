# Qué se toma de Odoo y qué se construye

| Necesidad | Odoo | En este proyecto |
|---|---|---|
| Ficha de empleado, departamentos, cargos, organigrama | `hr` (Community) | Se usa, con pestaña «Colombia» |
| Solicitud y aprobación de permisos, vacaciones, asignaciones | `hr_holidays` (Community) | Se usa, con tipos colombianos y soporte obligatorio |
| Marcación (kiosco, PIN, web, móvil) | `hr_attendance` (Community) | Se usa, cruzada contra el turno |
| Programación de turnos | Planning (**Enterprise**) | Propio: `ash_rrhh_turnos` |
| Nómina | Payroll (**Enterprise**) | **No**: Alegra |
| Firma/documentos, evaluaciones, reclutamiento | `hr_recruitment`, `hr_skills` (Community) | Se pueden instalar después sin cambios |

Licencias: Odoo Community LGPL-3, sin modificar; addons propios con licencia
propietaria. No se usa ningún módulo Enterprise ni OPL.
