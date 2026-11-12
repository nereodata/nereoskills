# B-ADV-0045 · Revisión de código de producción, fase D

Veredicto: APROBADO

Producto revisado: 34801f56d211a855e992a8ae979b5132ef883cb4a882475d4b8eb42d701a6a9a

## Alcance y dictamen

Desde la base de calidad `280eaf84a76230cd961ed2dd5d80fe60f4a3abe8`, el único cambio de producción son cuatro líneas en `agente`, en `skills/orquestar/orquestar.py`. El resto del delta corresponde a la ficha, las pruebas y los informes.

El ajuste actúa después de seleccionar el arnés de cada intento. Cuando un rol usa Codex en Windows y el padre tiene `CODEX_WINDOWS_REGISTERED_CORE`, copia el entorno, retira esa única clave y pasa la copia a `lanzar`. La seguí hasta `subprocess.Popen`. El padre conserva la marca incluso durante el lanzamiento. La sesión nueva y la reanudada reciben el entorno corregido. Si falla una reanudación y procede recuperarla, el intento nuevo recibe la misma copia. Al pasar a otro arnés, el bucle vuelve a construir los argumentos del lanzamiento.

Los comandos Codex de ambas modalidades conservan `workspace-write`, la política de aprobación `never` y la validación del checkout. El ajuste coincide con la causa aislada en la reproducción comparativa de la ficha y respeta la responsabilidad del motor definida en el plan de plataforma. El triaje omitió el diseño específico de tarea.

## Comprobación real del lanzador

- **Sesión nueva.** La ficha documenta la ejecución por la CLI corregida en un clon con el padre marcado. Hades leyó 48 bytes desconocidos, escribió el hash y releyó su informe. El cálculo independiente del padre coincidió.
- **Sesión reanudada.** En esta invocación del lanzador corregido leí el archivo de producción del checkout con PowerShell, calculé el SHA256 directamente sobre sus bytes y escribí este informe mediante las herramientas del revisor. El mandato identifica la marca heredada por el padre.

SHA256 de `skills/orquestar/orquestar.py`: `9B08FB01E6DE8B62D75507CBD88E3FA2406D695F9746734592096F6E218E4158`.

## Verificación y análisis estático

La evidencia del árbol `7e94a77cb5` registra 13 pruebas dirigidas verdes, incluidas las protecciones de B-ADV-0044 ante dictamen ausente y repetición. Los dos hallazgos de C1 están resueltos en el doble del proceso: comprueba el padre durante cada lanzamiento y admite la herencia implícita del entorno.

Se reutilizaron el verde de `git diff --check` y el de la búsqueda de firmas de credenciales en el delta. Ejecuté `adevv orquestar --calidad --base 280eaf84a76230cd961ed2dd5d80fe60f4a3abe8` en modo de lectura. Devolvió código 0 y comunicó «formato omitido: ausencia de herramientas» y «lint omitido: ausencia de herramientas». El proyecto carece de tipado configurado. La auditoría de dependencias no aplica porque el delta carece de cambios en manifiestos. La suite completa corresponde al cierre.

## Puntuaciones

| Criterio | Nota | Fundamento |
| --- | ---: | --- |
| Corrección | 10/10 | La copia llega al proceso hijo en los tres recorridos previstos y conserva el resto del entorno. |
| Seguridad | 10/10 | Se conservan las restricciones del revisor. El cambio no registra valores de entorno. |
| Conformidad | 10/10 | La condición de plataforma, arnés y presencia de la marca coincide con C2. |
| Calidad | 10/10 | El ajuste reutiliza el parámetro existente de lanzamiento y queda localizado en la selección del rol. |
| Eficiencia | 10/10 | Solo copia el entorno cuando hay una clave que retirar. El reintento reutiliza la copia. |
| Documentación | 10/10 | La ficha explica la causa y las condiciones de reproducción. El contrato público del lanzador sigue vigente. |

**Media: 10/10.** Sin hallazgos de producción.
