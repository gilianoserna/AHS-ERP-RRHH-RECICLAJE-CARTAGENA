# Reglas laborales parametrizadas

Valores iniciales en `addons/ash_rrhh_base/data/ash_rrhh_parametros.xml`.
**Validar con el asesor laboral antes de producción.** Un cambio de ley se
registra como una fila nueva con su fecha de vigencia.

| Parámetro | Valor | Desde | Fuente |
|---|---|---|---|
| Inicio jornada nocturna | 21:00 | — | CST art. 160 |
| Inicio jornada nocturna | 19:00 | 2025-12-25 | Ley 2466 de 2025 |
| Fin jornada nocturna | 06:00 | — | CST art. 160 |
| Jornada máxima semanal | 44 h | 2025-07-15 | Ley 2101 de 2021 |
| Jornada máxima semanal | 42 h | 2026-07-15 | Ley 2101 de 2021 |
| Máx. horas extra día / semana | 2 / 12 | — | CST art. 22, Ley 50 de 1990 |
| Descanso mínimo entre turnos | 10 h | — | Política interna |
| Tolerancia de tardanza | 5 min | — | Política interna |

## Cómo se clasifican las horas

Por minuto, en la hora local del empleado:

- **Nocturna** si cae en la franja nocturna vigente; si no, diurna.
- **Dominical/festiva** si cae en domingo o en un festivo (`ash.rrhh.festivo`).
- **Extra** cuando lo trabajado supera los minutos programados del turno
  (en el orden en que ocurre: si alguien llega 10 min tarde, sus extras empiezan
  10 min después).
- Una marcación **sin turno** se cuenta como ordinaria y se marca para revisión.

Los porcentajes de recargo no viven aquí: Alegra los aplica al liquidar.
