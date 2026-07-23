# Sistema de clima — Jona tenía 15 años

Esta documentación explica de dónde sale la información meteorológica, cómo se transforma y qué significa cada estado mostrado en la base de operaciones.

## Objetivo

Dar a producción una lectura rápida por jornada y, al mismo tiempo, permitir abrir el detalle de cada bloque horario. La interfaz busca responder cuatro preguntas:

1. ¿Hay una señal de lluvia durante el rodaje?
2. ¿Puede haber viento o ráfagas que compliquen exteriores?
3. ¿Los modelos coinciden?
4. ¿La fecha está lo bastante cerca como para confiar en el detalle?

La hora de generación incluida en `data/weather.json` también se muestra en la portada como **Última actualización del clima**.

## Flujo de datos

```text
INUMET ───────────────────────┐
ECMWF y GFS vía Open-Meteo ───┼─> scripts/update_weather_plan.py
MetSul ───────────────────────┘              │
                                             ▼
                                  scripts/update_weather.py
                                             │
                                             └─> data/weather.json
                                                        │
                                                        ▼
                                             scripts/translate_metsul.py
                                                        │
                                                        └─> data/metsul-translations.json
```

`update_weather_plan.py` contiene el plan específico de Jona: fechas, bloques, locaciones aproximadas y sensibilidades de cada escena. Ese script carga el recolector genérico `update_weather.py`, reemplaza su configuración y genera el JSON operativo.

`translate_metsul.py` se ejecuta después del recolector. Traduce al español titulares y extractos de MetSul, conserva el portugués original como respaldo y guarda una memoria de traducción para evitar trabajo repetido.

La página es estática: el navegador no consulta directamente a los proveedores, sino que lee el último `weather.json` publicado. Esto mejora la velocidad, evita múltiples consultas por visitante y permite conservar el último resultado cuando una fuente falla temporalmente.

El botón **Actualizar pronóstico** vuelve a descargar el JSON sin caché. El enlace **Forzar consulta en GitHub** abre el workflow; iniciar una nueva recolección requiere estar autenticado y tener permisos sobre la repo.

## Fuentes

### INUMET

Se consulta el pronóstico oficial del Área Metropolitana y el estado de las advertencias meteorológicas. Cuando hay una advertencia activa, la página la destaca y enlaza a la fuente oficial.

El alcance geográfico del pronóstico metropolitano no representa con la misma precisión todos los puntos del rodaje, especialmente Parque del Plata. Por eso se muestra como contexto oficial y se acompaña con modelos por coordenadas.

### ECMWF y GFS

Las series horarias de ambos modelos se obtienen mediante Open-Meteo para puntos aproximados de:

- Ciudad de la Costa;
- La Paz;
- Las Piedras;
- Parque del Plata.

Las variables utilizadas son temperatura, sensación térmica, probabilidad y cantidad de precipitación, nubosidad, viento y ráfagas.

### MetSul

Se consultan publicaciones recientes relacionadas con Uruguay. MetSul funciona como contexto meteorológico editorial: sus artículos pueden advertir sobre sistemas regionales relevantes, pero no se convierten artificialmente en valores horarios para una localidad.

La traducción automática no reemplaza el texto original. Cuando el motor de traducción no está disponible o falla, la interfaz conserva el portugués como alternativa.

## Resúmenes

El recolector calcula métricas para cada bloque del plan de rodaje y luego combina los bloques en un resumen diario. La interfaz conserva los resultados separados de ECMWF y GFS para que producción pueda ver desacuerdos.

Los estados son:

- **Sin señal fuerte por ahora:** no aparece una señal relevante de lluvia, ráfagas o suelo húmedo en los modelos disponibles.
- **Atención:** existe señal de lluvia, desacuerdo entre modelos, ráfagas relevantes o lluvia previa que podría dejar el suelo húmedo.
- **Riesgo meteorológico:** aparece precipitación más importante o ráfagas fuertes en al menos uno de los modelos.
- **Aún fuera del alcance:** la fecha no está dentro del horizonte disponible y no se inventa una previsión.

Estos estados son ayudas logísticas, no alertas oficiales.

## Confianza

La confianza baja cuando:

- falta uno de los modelos;
- ECMWF y GFS discrepan sobre la lluvia;
- la fecha está a muchos días de distancia;
- la jornada todavía no entra en el horizonte de consulta.

Aunque aparezca una confianza alta, el pronóstico puede cambiar. Para decisiones críticas deben revisarse también las actualizaciones y advertencias oficiales.

## Actualización automática

El workflow está definido en `.github/workflows/update-weather.yml` y ejecuta:

```text
python scripts/update_weather_plan.py
python scripts/translate_metsul.py
```

Está configurado para correr:

- alrededor del minuto 17 de cada hora;
- como redundancia, alrededor de las 00:43, 06:43, 12:43 y 18:43 en `America/Montevideo`;
- manualmente mediante `workflow_dispatch`;
- cuando cambian el recolector, el plan meteorológico, la traducción o el propio workflow.

El job utiliza Python 3.12. Argos Translate se instala con tolerancia a fallos: si el motor no puede instalarse, el sistema meteorológico sigue siendo utilizable y mantiene el texto original de MetSul.

Cuando cambian `data/weather.json` o `data/metsul-translations.json`, GitHub Actions crea un commit automático y hace `push` a `main`.

GitHub Actions puede demorar o descartar una ejecución programada. Los horarios de refuerzo reducen la posibilidad de pasar muchas horas sin datos nuevos, pero no constituyen una garantía absoluta.

## Tolerancia a fallos

Si una fuente no responde:

- las demás fuentes continúan procesándose;
- el error queda registrado en el JSON;
- cuando existe información anterior reutilizable, el recolector intenta conservarla;
- la interfaz identifica datos no disponibles en vez de rellenarlos con valores inventados;
- el sitio conserva el último archivo publicado hasta que una nueva ejecución válida lo reemplace.

## Cambiar jornadas o localidades

La configuración específica del rodaje está en `scripts/update_weather_plan.py`:

- `collector.LOCATIONS` contiene las coordenadas aproximadas utilizadas por los modelos;
- `collector.SHOOT_DAYS` define cada jornada y sus bloques horarios;
- `collector.WEEKENDS` define los grupos de fechas mostrados por la interfaz.

El comportamiento general del recolector permanece en `scripts/update_weather.py`.

Después de modificar la configuración, ejecutar:

```bash
python scripts/update_weather_plan.py
```

Luego revisar `data/weather.json` antes de publicar. No deben cargarse domicilios particulares: alcanza con una coordenada representativa de la localidad o zona de trabajo.

## Traducciones de MetSul

La memoria de traducción se guarda en:

```text
data/metsul-translations.json
```

El script intenta usar traducción directa de portugués a español. Cuando esa combinación no está disponible, puede utilizar inglés como idioma intermedio. La caché tiene un límite para evitar crecimiento indefinido.

Para ejecutarlo localmente:

```bash
python -m pip install argostranslate==1.11.0
python scripts/translate_metsul.py
```

## Verificación operativa

Antes de cada jornada conviene comprobar:

1. la hora de la última actualización mostrada en la portada y en Clima;
2. si INUMET tiene una advertencia activa;
3. si ECMWF y GFS coinciden;
4. el detalle del bloque exterior concreto;
5. el radar y la observación más cercana el mismo día;
6. que el plan de horarios y locaciones configurado siga coincidiendo con producción.

La decisión final de rodaje debe basarse en el estado más reciente, no solamente en una captura o lectura realizada varios días antes.
