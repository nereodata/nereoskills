# Diseño B-ADV-0011

Reutilizar `lista_reservas`, `espera_cuota`, `esperar`, `firma` y el registro actual del bucle. Añadir un bucle de intentos por perfil dentro de `bucle`; cada ejecución captura sus métricas y las señales de cuota de agentes. Antes de repetir, comprobar finalización en disco (firma cambiada y árbol limpio). Reintentos sin progreso no consumen iteraciones de pasos. Registrar cada fallo intermedio con su consumo y perfil; el registro final existente conserva el último intento.

`--reintentos-arnes`: entero >= 0; por defecto 3. Esperas en segundos 60, 300, 900, 900…; el mismo perfil conserva el mandato y empieza sin sesión tras fallo operacional. `esperar` admite motivo opcional para distinguir red de cuota, manteniendo el contrato por defecto y la señal de parada. Comprobar parada también antes de ejecutar un perfil/reintento. Conservar la menor cuota de todos los perfiles si se agotan reservas con errores mixtos. Cola final limitada a 2000 caracteres del último intento ejecutado.

## Impacto mecánico
- `bucle` es llamado por `main` y pruebas directas: quieren recuperación nueva. Namespace antiguos usan el valor por defecto mediante getattr.
- `esperar` es llamado por bucle para cuota y ahora por reintentos operacionales; gateway tiene su propia función. Se mantiene firma compatible mediante argumento opcional.
- Contrato sustituido: escenario orquestacion.feature:66 y rama paso de test_arnes_ausente.py::test_errores_operacionales_no_prueban_reservas. Autorización explícita del bug; conservar pruebas de agente/gateway. No cambia arquitectura ni capas.
- Archivos: motor, feature, nuevas pruebas test_fallos_arnes.py, ajuste del alcance de test_arnes_ausente.py, guía y SKILL.md.
- Tiempo: segundos relativos; espera cooperativa con sondeos de hasta 30 segundos. Sin costo añadido al camino exitoso, se comprueba con una sola llamada al arnés y cero esperas.
- Pruebas con proceso simulado, reloj/espera simulada y repositorios temporales, sin servicios ni red. No se introducen dependencias.


## Ajustes tras Hades
- `cuota_descartada` añade `incluir_recuperadas=False`: los llamantes existentes (`agente` y rutas previas de `bucle`) conservan su contrato. Solo la recuperación operacional del bucle solicita perfiles omitidos ya recuperados y los añade una vez a la lista de intentos. La selección se amplía solo con perfiles originales, de modo que no hay reintentos ilimitados.
- Comparar recuperaciones pendientes de todos los perfiles: las del paso usan plazos monotónicos para descontar las esperas de reintentos; las omitidas usan su vencimiento persistido. Se conserva el perfil de la menor espera. La frontera convierte ambos a segundos restantes.
- Identificar `modelo` explícitamente en cada fila de intento, independientemente de `modelos` reales de consumo.
