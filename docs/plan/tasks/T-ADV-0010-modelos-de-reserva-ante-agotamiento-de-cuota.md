---
id: T-ADV-0010
title: "Modelos de reserva ante agotamiento de cuota en pasos y subagentes"
type: funcional
weight: 100
dificultad: media
version: "v0.3.0"
status: planned
depende_de: []
origen: "Mejora operativa de resiliencia de cuota en /orquestar"
created_at: 2026-10-23
updated_at: 2026-10-23
---

# T-ADV-0010: Modelos de reserva ante agotamiento de cuota en pasos y subagentes

## 🎯 Objetivo de Negocio
Permitir que cada rol de `orchestration.json` defina un modelo/arnés de reserva —o una lista ordenada de reservas— para que, cuando el modelo principal agote su cuota o créditos, el orquestador conmute automáticamente al siguiente disponible en lugar de detener el desarrollo esperando horas a que se recupere la cuota.

## 📋 Criterios de Aceptación (Nivel Máster)
- [ ] **CA-M-1 (Definición de `reserva` en `orchestration.json`):** Cualquier rol (`atenea`, `artemisa`, `hades`, `clio`, `cronos`) o subbloque de configuración admite la clave opcional `"reserva"`, que puede ser un único objeto `{"harness": "...", "model": "...", "effort": "..."}` o una lista ordenada de objetos `[{"harness": "...", "model": "..."}, ...]`. Cada entrada hereda del rol los campos (`harness`, `model`, `effort`) que no redefina.
- [ ] **CA-M-2 (Conmutación automática en `agente()`):** Cuando `agente(root, rol, prompt)` detecta agotamiento de cuota (`espera_cuota(salida) is not None`), antes de devolver fallo por cuota recorre en orden las configuraciones de `reserva` del rol, probando la siguiente disponible y registrando cada intento en `orquestar_metricas.jsonl`. Solo si el modelo principal y todas sus reservas están sin cuota registra `sin_cuota: True` con el menor `espera_s` para que el bucle espere.
- [ ] **CA-M-3 (Conmutación automática en `bucle()`):** Cuando el paso principal (`ejecutar`) falla por falta de cuota propia y el rol tiene `reserva` configurada, `bucle()` reintenta inmediatamente el paso con la siguiente configuración de `reserva` (iniciando sesión nueva si cambia de arnés) antes de entrar en `esperar(root, cuota)`. Solo entra en `esperar(root, cuota)` cuando se agotan el modelo principal y todas las reservas configuradas.
- [ ] **CA-M-4 (Documentación en `/orquestar`):** `skills/orquestar/SKILL.md` documenta la clave `reserva` (objeto o lista) en la sección de Roles y Sin cuota.
