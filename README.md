# Jona — logística Parque del Plata

Página estática de apoyo para producción, pensada para consultar rápido supermercados, almacenes y compras cercanas durante el rodaje.

Sitio publicado:

https://jrrguille-bit.github.io/jona-logistica-mapa/

## Qué contiene

- Lista de supermercados, almacenes y comercios útiles cerca de Parque del Plata.
- Horarios estimados o pendientes de confirmar.
- Distancia aproximada desde la zona de referencia de producción.
- Recomendación rápida: caminando, bici o auto.
- Botones directos para abrir cada lugar en Google Maps.
- Versión responsive: en escritorio se muestra como tabla; en celular se muestra como tarjetas grandes.

## Archivos principales

- `index.html` — página principal publicada en GitHub Pages.
- `921600d1-4054-4c42-b1e4-5f1d0202a7be.png` — imagen de fondo usada por la página.
- `jona_supermercados_simple_distancia_horario.csv` — versión CSV de la lista.
- `.nojekyll` — evita procesamiento innecesario de Jekyll en GitHub Pages.

## Notas de uso

La página está optimizada para celular: los botones son grandes, la tabla se reemplaza por tarjetas y los links abren Google Maps en una pestaña/app aparte.

Antes del rodaje conviene confirmar horarios en Google Maps o por teléfono, especialmente fuera de temporada, de noche o en feriados.

## Mantenimiento rápido

Para cambiar comercios, editar el arreglo `lugares` dentro de `index.html` y, si corresponde, actualizar también el CSV.

Para cambiar el fondo, subir la nueva imagen al repo y reemplazar la ruta en el CSS:

```css
background: url("nombre-del-archivo.png") center/cover no-repeat;
```
