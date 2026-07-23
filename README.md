# Jona tenía 15 años — Base de operaciones

[![Actualizar clima](https://github.com/JRRGUILLE-bit/jona-logistica/actions/workflows/update-weather.yml/badge.svg)](https://github.com/JRRGUILLE-bit/jona-logistica/actions/workflows/update-weather.yml)

Sitio web público de apoyo operativo para la producción audiovisual de **Jona tenía 15 años**. Centraliza información de rodaje, pronóstico meteorológico, movilidad, documentación, comercios cercanos, aplicaciones técnicas y comunicación del equipo.

**Sitio publicado:** [jrrguille-bit.github.io/jona-logistica](https://jrrguille-bit.github.io/jona-logistica/)

## Objetivo

Reducir la cantidad de mensajes, planillas y enlaces dispersos que el equipo necesita consultar durante la preparación y las jornadas de rodaje. La portada funciona como una **base de operaciones** rápida, adaptada a escritorio y celular.

La franja **Próxima jornada** cambia automáticamente según la fecha. Para las jornadas con movilidad cargada enlaza directamente al día correspondiente; para las restantes dirige a Docs. También muestra la hora real de la última actualización meteorológica publicada en `data/weather.json`.

## Secciones del sitio

| Sección | Ruta | Contenido |
|---|---|---|
| **Clima** | `/clima/` | Pronóstico por jornada, bloque horario y locación; comparación de modelos y fuentes oficiales. |
| **Movilidad** | `/movilidad/` | Autos, conductores, pasajeros, horarios, puntos de encuentro y recorridos del primer fin de semana. |
| **Compras** | `/supermercados/` | Supermercados, almacenes, carnicerías y búsquedas de farmacias cercanas, con accesos a Maps. |
| **Docs** | `/docs/` | Guion, guion técnico, plan de rodaje, plan de trabajo, citaciones y planillas de equipos. |
| **Apps** | `/apps/` | Aplicaciones oficiales para equipos del rodaje y descargas públicas de MENELAO. |
| **Discord** | `/discord/` | Descargas de Discord para iOS y Android y espacio reservado para la futura invitación al servidor. |

La ruta histórica `/links/` se conserva como redirección hacia `/docs/` para no romper accesos guardados.

## Jornadas configuradas

| Jornada | Fecha | Referencias operativas |
|---|---|---|
| Día 1 | sábado 25 de julio de 2026 | Taller en Ciudad de la Costa y Casa Negro en La Paz |
| Día 2 | domingo 26 de julio de 2026 | Plaza de La Paz y Colina en Las Piedras |
| Día 3 | sábado 1 de agosto de 2026 | Colina en La Paz y casa en Parque del Plata |
| Día 4 | domingo 2 de agosto de 2026 | Casa en Parque del Plata |

La sección Movilidad está cargada solamente para el 25 y 26 de julio. Las jornadas posteriores se consultan mediante los documentos de producción.

## Privacidad del sitio público

La repo y GitHub Pages son públicos. Para limitar la exposición de información personal:

- se muestran nombres de pila o alias, no nombres completos del crew;
- no se publican domicilios particulares como texto general del sitio;
- las consultas meteorológicas usan coordenadas aproximadas de localidades o zonas;
- los documentos externos conservan los permisos definidos en Google Drive;
- la información de producción debe retirarse o archivarse cuando deje de ser operativamente necesaria.

El sitio no debe usarse para publicar teléfonos, documentos personales, datos médicos, contraseñas ni información sensible del equipo.

## Sistema meteorológico

La página de Clima combina señales distintas sin presentar una fuente aislada como certeza.

| Fuente | Uso dentro del sitio |
|---|---|
| [INUMET](https://www.inumet.gub.uy/) | Pronóstico oficial del Área Metropolitana y advertencias meteorológicas. |
| [ECMWF](https://www.ecmwf.int/) | Modelo numérico consultado mediante Open-Meteo. |
| [GFS / NOAA](https://www.ncei.noaa.gov/products/weather-climate-models/global-forecast) | Segundo modelo para comparar señales y detectar desacuerdos. |
| [Open-Meteo](https://open-meteo.com/) | Interfaz para obtener series horarias por coordenadas. |
| [MetSul Meteorologia](https://metsul.com/) | Contexto meteorológico editorial reciente para Uruguay. |

El flujo actual es:

```text
Fuentes meteorológicas
        │
        ▼
scripts/update_weather_plan.py
        │ carga el recolector genérico
        ▼
scripts/update_weather.py
        │
        ├──> data/weather.json
        │
        ▼
scripts/translate_metsul.py
        │
        └──> data/metsul-translations.json
```

La implementación, los estados de riesgo y los límites del sistema están detallados en [docs/CLIMA.md](docs/CLIMA.md).

## Actualización automática del clima

El workflow `.github/workflows/update-weather.yml` se ejecuta:

- cada hora, alrededor del minuto 17;
- como refuerzo, alrededor de las 00:43, 06:43, 12:43 y 18:43 de `America/Montevideo`;
- manualmente desde **Actions**;
- cuando cambian el recolector, el plan meteorológico, la traducción o el workflow.

El job usa Python 3.12, actualiza `data/weather.json` y mantiene una memoria de traducciones de MetSul en `data/metsul-translations.json`. Cuando los datos cambian, GitHub Actions crea un commit automático.

El botón de actualización dentro de Clima vuelve a pedir el último JSON publicado sin caché. No inicia por sí solo una nueva consulta a las fuentes.

## Movilidad y avatares

La página de Movilidad organiza el primer fin de semana por:

- día y horario;
- punto de encuentro o traslado;
- auto y zona de salida;
- persona que conduce;
- pasajeros y rol dentro del equipo.

Los retratos goblin chibi están en `assets/avatars/`, optimizados como WebP con transparencia. Los primeros avatares visibles se cargan con prioridad y el resto utiliza carga diferida.

El fondo animado se descarga después de que la interfaz queda disponible. En conexiones con ahorro de datos o cuando el sistema solicita movimiento reducido, se mantiene el póster estático.

## Apps y MENELAO

Apps reúne enlaces oficiales para:

- HollyView;
- Sidus Link;
- DJI Ronin;
- Sound Devices Wingman;
- ZOOM Handy Control & Sync;
- H4essential Control.

La misma sección publica versiones portables de **MENELAO** para Windows y Linux. Los ZIP se sirven directamente desde:

```text
apps/downloads/
```

MENELAO es una herramienta independiente para copiar una fuente audiovisual a dos destinos y verificar las tres ubicaciones mediante hashes SHA-256.

Discord se mantiene como sección separada. El botón de ingreso al servidor queda desactivado hasta que producción genere una invitación válida.

## Rendimiento y accesibilidad

El sitio es estático y no depende de un framework. Las principales optimizaciones son:

- fondos principales en WebP;
- dimensiones explícitas y carga diferida para avatares;
- video de Movilidad diferido hasta que el navegador queda libre;
- alternativa estática para ahorro de datos y movimiento reducido;
- `content-visibility` para bloques fuera de pantalla;
- efectos de desenfoque reducidos en celular;
- iconos SVG integrados en el HTML;
- navegación y estados de foco utilizables con teclado;
- diseño responsive para celular, tablet y escritorio.

## Estructura principal

```text
.
├── index.html                         # Portada y próxima jornada dinámica
├── home.css                           # Estilos específicos de la portada
├── site-touchup.css                   # Capa visual compartida
├── clima/
│   └── index.html                     # Pronóstico operativo
├── movilidad/
│   └── index.html                     # Autos, personas y recorridos
├── supermercados/
│   └── index.html                     # Compras y farmacias
├── docs/
│   ├── index.html                     # Accesos a documentos de producción
│   └── CLIMA.md                       # Documentación técnica del clima
├── links/
│   └── index.html                     # Redirección histórica hacia Docs
├── apps/
│   ├── index.html                     # Apps técnicas y MENELAO
│   └── downloads/                     # ZIP públicos de MENELAO
├── discord/
│   └── index.html                     # Descargas y placeholder de invitación
├── assets/
│   └── avatars/                       # Retratos optimizados del crew
├── data/
│   ├── weather.json                   # Último pronóstico generado
│   └── metsul-translations.json       # Memoria de traducciones
├── scripts/
│   ├── update_weather.py              # Recolector meteorológico genérico
│   ├── update_weather_plan.py         # Fechas, bloques y locaciones de Jona
│   └── translate_metsul.py            # Traducción y caché de MetSul
├── .github/workflows/
│   └── update-weather.yml             # Actualización automática
└── .nojekyll
```

## Ejecución local

Para previsualizar el sitio con rutas y solicitudes `fetch` funcionando correctamente:

```bash
python -m http.server 8000
```

Luego abrir:

```text
http://localhost:8000/
```

Para regenerar el pronóstico con el plan actual de rodaje:

```bash
python scripts/update_weather_plan.py
```

La traducción de MetSul utiliza Argos Translate cuando está disponible:

```bash
python scripts/translate_metsul.py
```

Antes de publicar cambios meteorológicos, revisar `data/weather.json` y confirmar que `generated_at`, las fechas, las locaciones y los bloques sean correctos.

## Mantenimiento operativo

Antes de cada jornada conviene verificar:

1. la hora de la última actualización del clima;
2. advertencias vigentes de INUMET;
3. enlaces de Docs y permisos de Drive;
4. citaciones y puntos de encuentro;
5. horarios orientativos de comercios;
6. que las descargas públicas de MENELAO respondan;
7. que la invitación de Discord siga vigente una vez creada.

## Alcance

El sitio es una herramienta logística de producción. No sustituye avisos oficiales, decisiones de seguridad, comunicaciones formales de producción ni la información definitiva contenida en las citaciones y planes aprobados.

Ante advertencias meteorológicas o condiciones peligrosas, producción debe utilizar la información oficial más reciente y tomar la decisión operativa correspondiente.

---

Una producción de **Mala Hierba Producciones**.
