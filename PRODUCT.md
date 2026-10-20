# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Stack

Python, Streamlit, Pandas, Openpyxl.

## Users

Ingenieros de Datos y Auditores de Plataforma (DataPlatform), trabajando localmente o en un entorno seguro para auditar y confirmar la sensibilidad (PII) de los metadatos de las bases de datos de Oracle previo a una migración a GCP.

## Product Purpose

Permitir a los ingenieros cargar muestras de datos extraídas, triar automáticamente los campos con probabilidad de PII mediante un escáner, revisar y confirmar visualmente campo por campo apoyándose en la muestra de datos en vivo, y finalmente exportar un reporte oficial en Excel de los campos PII validados para cumplir con los requerimientos de migración.

## Positioning

Es un puente humano-en-el-circuito (Human-in-the-Loop) rápido y auditable que une la abstracción del escaneo de datos en crudo con la validación humana final en una interfaz de una sola página.

## Operating Context

Se ejecuta localmente. Los usuarios suben múltiples archivos CSV o un archivo ZIP exportados desde Qlik/Oracle, revisan las tablas ordenadas por nivel de riesgo, inspeccionan la data real si tienen dudas (Deep Dive), y descargan un Excel validado para enviarlo al equipo de GCP.

## Capabilities and Constraints

Debe funcionar rápido en memoria, limitando a las primeras 1000 filas por tabla para la previsualización general y cargando datos On-Demand únicamente durante la "Inspección de Análisis Fino" para evitar crasheos de memoria. Debe generar un Excel específico. Toda la UI debe basarse en Streamlit, limitando las opciones avanzadas de frontend y animaciones.

## Evidence on Hand

Muestras de 27 tablas de CAPEX Oracle en CSV y archivos ZIP extraídos mediante un bypass binario en Qlik Sense.

## Product Principles

1. **Claridad sobre Volumen:** Mostrar en todo momento progreso y contadores; el usuario debe saber cuánto le falta auditar.
2. **Jerarquía Visual por Riesgo:** Destacar siempre Rojo (Alta), Amarillo (Media) y Verde (Baja).
3. **Carga Inteligente:** Nunca colgar la herramienta; la lectura profunda de CSVs solo ocurre cuando el humano lo pide expresamente.
