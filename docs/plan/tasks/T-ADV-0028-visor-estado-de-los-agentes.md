---
id: T-ADV-0028
title: "Visor gráfico: estado de los agentes, cuotas y bloqueos"
type: funcional
weight: 110
dificultad: media
version: "v1.1.0"
status: planned
depende_de: ["T-ADV-0027"]
origen: "Petición del usuario: visor gráfico del estado de los agentes configurados (v1.1)"
created_at: 2026-10-26
updated_at: 2026-10-26
---

# T-ADV-0028: Visor gráfico: estado de los agentes, cuotas y bloqueos

## 🎯 Objetivo de Negocio
Saber, sin consultar cada arnés, qué agentes están disponibles, cuánta cuota les queda y cuáles están bloqueados y hasta cuándo, para entender por qué un bucle espera o usa una reserva.

## 📋 Criterios de Aceptación (Nivel Máster)
- [ ] **CA-M-1 (Vista de agentes):** para los roles configurados (`atenea`, `artemisa`, `hades`, `clio`, `cronos`, `telegram`) de cada proyecto registrado: arnés, modelo y esfuerzo por dificultad y paso, escalada y reservas en su orden, y cuál es el perfil efectivo del paso pendiente. Es la misma información que `adevv orquestar --agentes`, reutilizando su cálculo.
- [ ] **CA-M-2 (Cuotas):** por cada `harness/model` único: porcentaje consumido, tokens frente al límite, origen del dato (nativo de Codex o estimado) y hora local de reinicio. Las cuotas compartidas entre proyectos se muestran una vez, con los proyectos que las usan.
- [ ] **CA-M-3 (Bloqueos):** modelos con agotamiento vigente, con el tiempo que les queda bloqueados (cuenta atrás); arneses no encontrados (B-ADV-0005); bucles en espera de cuota con su espera acumulada; y tareas bloqueadas o promovidas de dificultad por reintentos.
- [ ] **CA-M-4 (Avisos visuales):** colores o indicadores para cuota alta (p. ej. > 80 %), agotada y arnés no disponible, legibles en tema claro y oscuro.
- [ ] **CA-M-5 (Pruebas y documentación):** pruebas de la API de agentes con métricas y reloj simulados; documentación en la del visor.
