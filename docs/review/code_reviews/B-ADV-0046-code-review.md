# B-ADV-0046 · Revisión independiente de código, fase D

Veredicto: RECHAZADO

Producto revisado: 583b836296a5b87a66dab3268dde8e2f7e3771318cde5d9e0520d918e82b2f04

Hades · `/review-code` v1.1.2 · `hotfix/v1.1.3`

Revisé el delta desde `aaf7a5e7c1402141e3df6bcf8dbdf3e6a9a6517d` hasta el árbol de trabajo `c083217f336eb2960223b6dbf66c38e3043ed859`, incluido el nuevo módulo de persistencia. Comprobé la identidad del producto con `huella_producto`.

## Hallazgos

### D1 · 🟠 Alta · Un escritor de Windows abandona una solicitud válida por contención

En `adevv/registro_metricas.py:66`, `msvcrt.locking(..., LK_LOCK, 1)` agota sus reintentos. La recuperación mantiene ese bloqueo mientras analiza todo el registro, guarda y sincroniza la evidencia y publica el activo. Si tarda más que la espera del escritor, `registrar` propaga `OSError`. Esto alcanza, entre otros, el registro de un paso ya ejecutado en `skills/orquestar/orquestar.py:3984` y puede interrumpir el bucle antes de guardar su consumo.

**Reproducción focalizada en Windows.** Un proceso mantuvo `bloqueo(raiz)` en un directorio temporal y otro llamó al escritor real para registrar E3. A los **9,1 segundos** el escritor devolvió `OSError` con `errno=36`. El proceso terminó con el código 3 asignado por el reproductor y el activo seguía sin crearse. Bastó la contención entre dos procesos, con el directorio accesible y el titular del bloqueo vivo.

**Para:** desarrollador (Artemisa). **Destino:** `resolver` en B-ADV-0046. Reintentar la adquisición ante contención transitoria de Windows y propagar los errores permanentes. Verificar que, tras superar la ventana actual y liberar el bloqueo, la llamada pendiente termina y E3 consta exactamente una vez.

### D2 · 🟡 Media · Una copia incompleta puede quedar identificada como original

En `adevv/registro_metricas.py:85`, `guardar_evidencia` crea directamente `original-*.jsonl` con `delete=False`. Si la escritura falla a mitad por falta de espacio, el activo queda íntegro, pero la copia parcial permanece con el mismo patrón de nombre que las copias completas. Un reintento puede dejar ambas en el directorio de evidencia.

**Para:** desarrollador (Artemisa). **Destino:** `resolver` en B-ADV-0046. Reservar el nombre de evidencia definitiva para la copia escrita, sincronizada y cerrada con éxito. Limpiar el temporal si la operación devuelve un error. El activo debe seguir intacto.

## Contraste con el triaje, el diseño y C1

- **Lectura y cursores.** El lector compartido delimita líneas por LF antes de decodificar UTF-8. La lectura operativa diagnostica la fila cerrada inválida y conserva los objetos legibles a ambos lados. La exportación estricta valida el registro antes de abrir el CSV de destino. El cursor del bucle y el de espera de cuota cuentan objetos válidos, de modo que retirar un fragmento mantiene la posición del observador.
- **Escritura y recuperación.** Los cuatro productores pasan por el escritor común. Dentro del bloqueo, el append inspecciona el último byte y separa la cola pendiente. La recuperación conserva los bytes originales de las filas válidas, sincroniza la copia y el saneado y reemplaza el activo. Una segunda recuperación sobre un registro sano conserva la primera evidencia. D1 afecta a la adquisición del bloqueo y D2 al camino de error previo a la publicación.
- **Conformidad.** La persistencia usa la biblioteca estándar de Python según DEC-P03. La CLI, la agregación y el acceso del gateway permanecen en las skills según DEC-P09. El directorio auxiliar queda excluido de Git y del inventario empleado en los chequeos. El README y la skill documentan el diagnóstico y la recuperación explícita.
- **Seguimiento de C1 (8,75/10).** Cerradas las dos observaciones. La prueba focalizada alcanza el solapamiento tras guardar la copia bajo el bloqueo real y comprueba la confirmación de E3, los tres eventos y los bytes de evidencia. La prueba de cola admite LF y CRLF. El verde cubre ese solapamiento breve. D1 se reprodujo prolongando la contención.

## Puntuaciones

| Criterio | Puntuación | Fundamento |
|---|---:|---|
| Corrección | 7/10 | La contención reproducida impide registrar un evento legítimo. El activo queda protegido ante fallos previos al reemplazo. |
| Seguridad | 9/10 | Creación exclusiva de temporales y evidencia, sin interpolar el contenido del JSONL en órdenes de sistema. |
| Conformidad | 9/10 | Se respetan las capas, las dependencias y el esquema de publicación del diseño. La espera del escritor limita la garantía de concurrencia en Windows. |
| Calidad | 8/10 | La lógica física se concentra en un módulo. La salida por error de la copia requiere la limpieza indicada en D2. |
| Eficiencia | 9/10 | El append inspecciona un byte del historial. Lectura y recuperación son lineales en el tamaño del registro. |
| Documentación | 9/10 | La API documenta lectura, bloqueo y recuperación. El procedimiento de usuario indica cómo localizar el original y repetir la exportación. |
| **Media** | **8,50/10** | **D1 impide aprobar.** |

## Análisis estático y evidencia

El registro local `orquestar_evidencias.jsonl` acredita código 0 en el árbol revisado para el comando exacto de las **18 pruebas del triaje**, `git diff --check`, la búsqueda de patrones de secretos y `adevv orquestar --calidad --base` con la base del triaje. Formato y lint se omitieron por falta de herramientas configuradas. El tipado carece de configuración. Los manifiestos de dependencias no cambian. La única ejecución funcional adicional fue la reproducción aislada de D1 con datos sintéticos fuera del checkout.
