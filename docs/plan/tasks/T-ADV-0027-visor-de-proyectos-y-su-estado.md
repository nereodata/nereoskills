---
id: T-ADV-0027
title: "Visor gráfico: registro de proyectos y estado de cada uno"
type: funcional
weight: 100
dificultad: dificil
version: "v1.1.0"
status: planned
depende_de: []
origen: "Petición del usuario: visor gráfico del estado de los proyectos (v1.1)"
created_at: 2026-10-26
updated_at: 2026-10-26
---

# T-ADV-0027: Visor gráfico: registro de proyectos y estado de cada uno

## 🎯 Objetivo de Negocio
Ver de un vistazo, en una sola ventana, todos los proyectos que gestiona Adevv en la máquina y en qué punto está cada uno, sin abrir cada repositorio ni preguntar en cada arnés. Es la base del visor de v1.1, sobre la que se montan la vista de agentes (T-ADV-0028) y el chat (T-ADV-0029).

## 📋 Criterios de Aceptación (Nivel Máster)
- [ ] **CA-M-1 (Registro de proyectos):** un registro por máquina en el almacén de Adevv (p. ej. `~/.adevv/proyectos.json`) con los proyectos gestionados. Desde el visor (y con `adevv proyectos añadir|quitar|listar`) se añade un proyecto existente (carpeta con `task_config.yaml`) o se quita del registro sin tocar el proyecto. `adevv orquestar` registra automáticamente el proyecto en el que se lanza.
- [ ] **CA-M-2 (Orden y forma del visor):** `adevv visor` abre el visor. Decisión por defecto, a confirmar en el diseño frente a `platform_plan.md`: servidor HTTP local solo en `127.0.0.1` con la librería estándar y una página estática (sin dependencias nuevas ni servicios externos), que se abre en el navegador. Si cambia el plan de plataforma, se registra la `DEC` correspondiente.
- [ ] **CA-M-3 (Vista de proyectos):** por proyecto: nombre, ruta, versión abierta y rama, fase/estado del bucle (lo mismo que `adevv orquestar --estado`: paso actual, PARAR con motivo, FIN), bucle y gateway en marcha o no, progreso de la versión (tareas completadas / pendientes / bloqueadas / en espera) y último paso con su hora. Un proyecto inaccesible se muestra como tal, sin romper la vista.
- [ ] **CA-M-4 (Detalle):** al abrir un proyecto se ve su backlog de la versión en curso (ID, título, estado, dificultad, dependencias) y el final de `orquestar.log`.
- [ ] **CA-M-5 (Actualización):** la vista se refresca sola cada pocos segundos leyendo solo el disco (sin lanzar pasos ni consumir cuota) y reutiliza las funciones de estado del motor, sin duplicar la lógica de `estado()`.
- [ ] **CA-M-6 (Pruebas y documentación):** pruebas del registro y de la API del visor con proyectos temporales; documentación en el README y en una skill o sección propia.
