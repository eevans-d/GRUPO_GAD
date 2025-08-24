# Instrucciones para Probar el Dashboard de Administración

Sigue estos pasos para levantar el entorno y probar la última funcionalidad desarrollada.

## 1. Reconstruir los Servicios Docker

Es muy importante que reconstruyas las imágenes de Docker para incluir los últimos cambios (como el nuevo Dashboard y las dependencias de la API). 

Abre una terminal en la raíz del proyecto y ejecuta:

```bash
docker compose up -d --build
```

## 2. Acceder al Dashboard

Una vez que los contenedores estén en funcionamiento, abre tu navegador web y visita la siguiente dirección:

[**http://localhost:8000**](http://localhost:8000)

Deberías ver el panel de control con las tablas de tareas y efectivos disponibles.

## Nota Importante

Recuerda que esta es una **primera versión de solo lectura**. El siguiente paso en el que trabajaré será añadir interactividad (botones, formularios, etc.).
