# Diseño técnico: T-ADV-0024

## Arquitectura y cambios

Modificar skills/telegram_gateway/gateway.py: añadir --autoarranque on|off|estado al grupo excluyente; gestionarlo antes de consultar credenciales. Inicio se resuelve con SHGetFolderPathW(CSIDL_STARTUP), sin elevación. Una entrada .vbs con nombre SHA-256 de la raíz absoluta normalizada identifica cada proyecto; publicación mediante temporal y os.replace, baja idempotente y consulta sin escrituras.

El VBS ejecuta PowerShell -NoProfile -NonInteractive -WindowStyle Hidden -EncodedCommand mediante WScript.Shell.Run con ventana 0 y espera, propagando su código. El programa codificado utiliza literales PowerShell escapados, prueba la raíz, fija el directorio y ejecuta adevv telegram --fondo una vez. Redirige diagnósticos a LocalAppData/Adevv/autoarranque/<hash>.log (fallback AppData). No incluye credenciales ni rutas del almacén. Proyecto ausente termina antes de invocar adevv. Los demás rechazos reutilizan exclusivamente gateway.main y su validación vigente; el arranque de sesión no reserva PID por su cuenta.

## Mapa de impacto

Búsqueda: gateway.main es invocado por adevv.cli mediante despacho y por tests de gateway; en_fondo se consume desde main y tests. No cambian sus firmas ni los modos existentes; la nueva opción excluye los anteriores. No se invalidan tests ni escenarios previos. La ruta ordinaria solo añade el parseo de una opción y una rama; no agrega E/S al polling. No se contradice ninguna decisión arquitectónica: stdlib, motor único, sin dependencia inversa. Rutas absolutas locales, sin conversión de zona horaria o unidades.

## Pruebas

Crear skills/telegram_gateway/test_autoarranque_windows.py. CLI con Inicio temporal y plataforma simulada para alta, baja, consulta y rechazo fuera de Windows. En Windows ejecutar cscript sobre la entrada temporal: PowerShell y un adevv.cmd ficticio llegan al main real con Popen simulado, dejando observaciones de argumentos, cwd, flags, reserva PID y diagnóstico. Aislar/restaurar TELEGRAM_*, logs, PATH y directorio; sin Telegram ni procesos de gateway reales. En otros SO estas pruebas nativas se marcan skipped con motivo, conservando pruebas unitarias. Se incluyen proyecto con espacios/acentos/apóstrofe y logs en carpeta temporal.
