# Modo offline e instalación — Jona tenía 15 años

El sitio incorpora un modo offline básico mediante un Service Worker registrado desde la portada. También puede instalarse como una aplicación independiente en teléfonos y computadoras compatibles.

## Activación

La persona debe abrir al menos una vez la portada con conexión:

```text
https://jrrguille-bit.github.io/jona-logistica/
```

Durante esa visita el navegador registra `service-worker.js` y guarda los recursos operativos principales. A partir de ese momento, las páginas almacenadas pueden abrirse con una conexión inestable o sin internet.

## Instalación como app

La portada declara `manifest.webmanifest` y muestra la acción **Instalar app** cuando el navegador permite la instalación.

- En Android, Chrome y navegadores compatibles se utiliza el diálogo nativo de instalación.
- En iPhone o iPad aparece **Agregar al inicio** y se indica usar **Compartir → Agregar a pantalla de inicio** en Safari.
- Cuando la app está instalada se abre en una ventana independiente, conserva el tema oscuro y ofrece accesos rápidos a Clima, Movilidad y Docs cuando el sistema los admite.

La instalación no cambia el contenido ni crea una copia separada de los datos. La app sigue consultando el mismo sitio y utiliza el caché local cuando falta conexión.

## Acciones rápidas de la portada

La portada agrega dos controles de conveniencia:

- **Compartir:** abre el menú nativo del dispositivo; cuando no está disponible, copia el enlace al portapapeles.
- **Instalar app / Agregar al inicio:** se muestra únicamente cuando corresponde al dispositivo y al navegador.

También incorpora un enlace de accesibilidad **Saltar al contenido**, visible al recibir foco mediante teclado.

## Contenido guardado

El caché inicial incluye:

- portada;
- Movilidad;
- Docs;
- Clima;
- Compras;
- Apps;
- Discord;
- la redirección histórica de Links;
- página 404;
- manifiesto de instalación;
- estilos, iconos y fondos estáticos principales;
- imagen de vista previa social;
- póster estático de Movilidad;
- avatares del crew;
- último `data/weather.json` disponible.

Los recursos internos cargados posteriormente también se guardan para próximas visitas.

## Estrategias

### Páginas HTML

Las navegaciones intentan obtener primero la versión online. Si la conexión falla o demora más de unos segundos, se usa la copia guardada. Si una ruta concreta no está disponible, se vuelve a la portada almacenada.

### Clima

`data/weather.json` utiliza una estrategia de red primero. Cuando no hay conexión, se entrega el último pronóstico guardado. La interfaz conserva la fecha y hora original de generación, y el aviso offline aclara que los datos pueden estar desactualizados.

### Recursos estáticos

CSS, JavaScript, manifiesto, imágenes, iconos y fuentes locales usan caché primero y se actualizan en segundo plano cuando vuelve la conexión.

## Recursos excluidos

No se almacenan automáticamente:

- videos `.mp4` y `.webm`;
- ZIP de MENELAO;
- enlaces externos;
- archivos alojados en Google Drive o Google Docs;
- tiendas de aplicaciones, Maps, Discord u otros servicios externos.

La página de Docs puede abrirse offline, pero los documentos externos requieren internet salvo que la aplicación correspondiente los haya guardado por su cuenta.

## Avisos de conexión

`offline.js` muestra un aviso fijo cuando el navegador detecta que no hay conexión:

> Sin conexión · mostrando la última versión guardada. El clima puede estar desactualizado.

Cuando vuelve internet aparece temporalmente:

> Conexión recuperada · ya podés actualizar la información.

## Actualizaciones

El caché utiliza un nombre versionado. Al cambiar `CACHE_NAME` en `service-worker.js`, el navegador instala el nuevo conjunto y elimina las versiones antiguas durante la activación.

La portada registra el Service Worker con `updateViaCache: none` y solicita una comprobación de actualización al abrirse.

## Verificación manual

1. Abrir la portada con conexión.
2. Esperar unos segundos y confirmar que aparezca **Instalar app** cuando el navegador lo permita.
3. Navegar una vez por las secciones principales.
4. En las herramientas del navegador, comprobar que el Service Worker figure como activo y que el manifiesto sea válido.
5. Activar el modo Offline en la pestaña Network.
6. Recargar Inicio, Movilidad, Docs y Clima.
7. Confirmar que Clima muestre el último `generated_at` guardado y el aviso de conexión.
8. Volver a modo online y confirmar el mensaje de conexión recuperada.

El modo offline es una ayuda operativa. No garantiza acceso a servicios externos ni reemplaza copias locales de documentos críticos.
