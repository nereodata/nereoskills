# Dictamen vigente — B-ADV-0034

**Veredicto: APROBADO**
**Media: 8,67/10**
**Árbol revisado:** b2410a5911 · **Fecha:** 2026-11-11.

Dictamen de Hades recibido por `--agente hades --prompt-file`, transcrito por
Artemisa. Etiqueta de veredicto normalizada al formato canónico del proyecto.
Sin acceso al disco por fallo del ejecutor, revisión independiente sobre adjuntos.

## Última reevaluación

Limitada a HC-01 y delta: aceptación PID propio, publicar_pid atómico y uso por
padre/hijo. HC-02 resuelto sin cambios y resto de revisión previa conservada.
No se reauditan tests ni arquitectura.

HC-01 resuelto: main conserva PID propio sin eliminarlo, republicarlo ni ejecutar
preparación inicial. Si el hijo leyó ausencia antes de la publicación del padre,
su temporal sincronizado + os.replace sustituye el mismo PID sin vacío/ausencia.
En_fondo publica antes de retornar/liberar serialización; termina y espera hijo
si falla publicación. Cierra la discontinuidad concreta de reserva.
HC-02 resuelto: incorporación y reanudación se comunican en sus puntos reales.

Evidencia aceptada sin repetir: 64 pruebas dirigidas antes del último helper;
tras él, 13 controlintervenciones y 13 regresiones de llamantes verdes. Compilación
de tres Python y diff-check verdes. No se atribuye la ejecución previa de 64 al
árbol posterior: el cierre repite el comando del triaje sobre artefactos finales.
Formato/lint omitidos sin herramientas; sin tipado ni escáner configurados,
no dependencias cambiadas. Fallo del ejecutor impidió contraste independiente
de disco/calidad sin escritura; no declara esa orden como ejecutada en verde.

Puntuaciones: corrección 9, seguridad 9, conformidad 9, calidad 8, eficiencia 8,
documentación 9. Media 8,67. Sin hallazgos nuevos ni críticos/altos abiertos.
No ejecutó verificaciones ni suite completa.

## Historial

# Revisión de código — B-ADV-0034

**Veredicto: RECHAZADO**
**Media: 7,67/10**
**Fecha:** 2026-11-11

Hades revisó el delta completo de este bug por adjuntos (diff HEAD, producción,
diseño, triaje y plataforma), sin pruebas ni revisión de arquitectura.
Disco y calidad sin escritura inaccesibles por fallo del ejecutor registered
Core launch requires an installed app. No ejecutó verificaciones ni suite.
Aceptó 35 tests dirigidos OK, py_compile y diff-check verdes, test-review 8,75.
Formato/lint omitidos por ausencia de herramientas; sin tipado o escáner de
secretos configurado; no ve secretos añadidos; auditoría dependencias no aplica.
No contrastó independientemente diff/evidencia en disco.

Puntuaciones: corrección 6, seguridad 9, conformidad 7, calidad 8, eficiencia 8,
documentación 8. Media 7,67.

## HC-01 — 🟠 ALTA — Serialización termina antes de reservar el bucle

**Para:** desarrollador.
`en_fondo` retorna tras Popen sin publicar/reservar PID. El hijo lo escribe en
main posteriormente. Dos respuestas de preguntas/tareas distintas pueden entrar
serializadas y ambas ver que no hay PID, incorporar y lanzar dos bucles.
Conservar reserva exclusiva hasta titularidad observable, recuperando fallo de
lanzamiento, antes de liberar serialización. Ambos adaptadores deben compartirla.

## HC-02 — 🟠 ALTA — Aviso de reanudación prematuro

**Para:** desarrollador.
`incorporar` emite `Tarea <ID> reanudada: <texto>` antes de comprobar parada,
dependencias y lanzamiento efectivo. Con Telegram habilitado puede contradecir
la salida CLI posterior (parada o espera); incorporación entre pasos también lo
emite. Incumple CA-5 y DEC-ESP-0034-01. Describir incorporación como incorporación
y confirmar lanzamiento donde se conozca el resultado, preservando formatos
en lo posible, sin mantener una afirmación incorrecta.

Ambos corresponden al desarrollador, sin recurso externo ni decisión humana.
Reevaluar solo hallazgos y delta corrector; el verde anterior no los descarta.

## Reevaluación de Hades · árbol 35b33f5fe0

**Veredicto: RECHAZADO** · **Media: 8,17/10**.
Evidencia aceptada 64 tests, compilación y diff-check verdes; sin repetir nada.
Limitado HC-01/HC-02 y delta; sin disco ni calidad ejecutable por fallo del arnés.
HC-02 resuelto: incorporar comunica incorporación/bloqueo; respuesta síncrona
confirma tras en_fondo; bucle avisa tras resultado de ejecutar, no arnés ausente,
con marca durable previa al envío y política documentada de no reenvío.
HC-01 persiste, ALTA para desarrollador: el hijo acepta PID propio pero luego
entra en else, hace unlink, excluir y reescribe PID. La reserva desaparece
durante esa transición y otro adaptador puede lanzar otro hijo. Separar aceptación
de titularidad propia de adquisición inicial, conservando archivo sin eliminarlo
ni volverlo a publicar. Puntuaciones 7/9/8/8/8/9; sin nuevos independientes.
