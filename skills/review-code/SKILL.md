---
name: review-code
description: Revisión independiente post-verde proporcional al riesgo del cambio
---

# /review-code

Revisa en contexto aislado el cambio entregado (código, configuración y pruebas) frente a su objetivo y a `PROJECT.md` (si existe).

1. **Verificación determinista**: Si el mandato incluye `base_calidad`, comprueba `adevv orquestar --calidad --base <base_calidad>` sin escritura (No uses `--aplicar`; el motor comprueba ambas etapas mediante `--verificar` reutilizando evidencias vigentes). Fallo de formato/lint o verificación: hallazgo para `desarrollador`, destino `resolver`, sin aprobación hasta corregirlo.
2. **Evaluación proporcional**: Ajusta la profundidad al riesgo real de lo tocado buscando errores lógicos, problemas de seguridad/permisos, condiciones de carrera, rotura de contratos o pruebas que no comprueban el comportamiento real.
3. **Informe (`docs/review/code_reviews/[ID]-code-review.md`)**:
   - Cabecera obligatoria: `**Veredicto:** APROBADO` (sin 🔴 ni 🟠) o `**Veredicto:** RECHAZADO`, seguida inmediatamente de `Producto revisado: <huella>` cuando corresponda.
   - Resumen conciso de lo comprobado y lista de **Hallazgos** (🔴 CRÍTICO | 🟠 ALTA con `para: desarrollador|especificador|humano`; 🟡 MEDIA | 🔵 BAJA con `destino: resolver|registrar|descartar`) únicamente si existen.
