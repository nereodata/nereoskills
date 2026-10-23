# Diseño T-ADV-0014

Una función de presentación compartida en orquestar.py añade agentes efectivos y uso reciente a parte/resumen. Reutiliza dificultad_de, rol_de, ajustes, escalada y lista_reservas; no decide ni modifica el estado del bucle. Lista modelos configurados y observados por par arnés/modelo; suma entrada+cache_leida+cache_escrita+salida (razonamiento es subconjunto de salida). Cada cuota registra modelo_cuota y cuota_espera_s propios del intento, conservando sin_cuota y espera_s históricos para reanudación/espera del bucle. El plazo global de ESPERA se muestra por separado, nunca como disponibilidad del proveedor.

## Impacto
- parte: gateway.procesar (/estado) y gateway.main (--estado) quieren la nueva presentación.
- resumen: main (--estado) quiere la misma presentación. Sin cambio de firmas.
- agente y bucle: campos nuevos aditivos; no cambia sin_cuota ni la espera mínima global. Los lectores de métricas existentes ignoran campos adicionales.
- Pruebas existentes de reservas fijan la ausencia de sin_cuota al conmutar: se conservan. No se invalidan escenarios.
- Ninguna decisión contradicha; DEC-P09 autoriza motor y tests en skills/.
- Fechas ISO antiguas sin zona se interpretan en zona local; con zona se convierten al mismo instante. Ventana [ahora-5h, ahora]; cuota vencida no se muestra activa. JSONL incompleto se omite para tolerar lectura concurrente.
- Camino de consulta: un recorrido de métricas para el nuevo desglose, sin red ni escrituras; pruebas con reloj fijo y archivos temporales comprueban lectura y fronteras.

## Archivos
Modificar skills/orquestar/orquestar.py y ambas SKILL.md. Añadir skills/orquestar/test_estado_agentes.py. Escenarios en telegram_gateway.feature y artefactos de ciclo en docs/.
