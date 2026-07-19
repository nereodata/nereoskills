---
name: seo-audit
description: Audits, reviews, or diagnoses technical and on-page SEO issues on the site.
---

# Skill: SEO Audit (/seo-audit)

Identifica problemas de posicionamiento orgánico y proporciona recomendaciones técnicas y de contenido.

## 📋 Pasos de la Skill

### 1. Preparación y Contexto
- Buscar si existe el archivo `.agents/product-marketing-context.md` (o `.claude/...`) para entender el negocio y keywords prioritarias.
- Definir el alcance (completo o páginas específicas).

### 2. Detección de Schema Markup (¡Crítico!)
- `web_fetch` y `curl` NO pueden detectar JSON-LD inyectado por JavaScript de forma dinámica.
- Para verificar el Schema estructurado, usa el navegador integrado o ejecuta en consola:
  ```javascript
  document.querySelectorAll('script[type="application/ld+json"]')
  ```
  O usa la herramienta oficial Google Rich Results Test.

### 3. Auditoría Técnica
- **Rastreo e Indexación**: Verificar `robots.txt`, XML sitemaps, arquitectura de URLs, y directivas noindex/canonical.
- **Rendimiento**: Analizar Core Web Vitals (LCP, INP, CLS) y velocidad de carga.
- **Mobile-Friendliness**: Comprobar visualización móvil y diseño responsive.
- **Seguridad**: Validar HTTPS y certificados SSL.

### 4. Auditoría On-Page e Interacciones
- **Meta-tags**: Comprobar unicidad, extensión y keywords en títulos (50-60 car) y descripciones (150-160 car).
- **Encabezados**: Comprobar jerarquía de títulos (un solo `<h1>` por página).
- **Imágenes**: Comprobar atributos `alt` descriptivos y formatos modernos (WebP, AVIF).

### 5. Auditoría de Contenido
Usar la guía de detección de patrones de escritura IA en [`references/ai-writing-detection.md`](./references/ai-writing-detection.md) para identificar contenido generado por IA que dañe credibilidad. Aplicar los criterios de evaluación en [`evals/evals.json`](./evals/evals.json).

### 6. Reporte de Salida
Crear un reporte en `docs/review/seo_audit.md` detallando:
- Puntos críticos (bloqueos de indexación, redirecciones rotas).
- Mejoras de rendimiento y estructura.
- Optimizaciones de contenido y metadata.
- Hallazgos de escritura IA y recomendaciones de reescritura.
