# PII Validator (Análisis PII)

Herramienta interactiva desarrollada con **Streamlit** para auditoría y validación de campos con datos sensibles / **PII** (*Personally Identifiable Information*) en bases de datos (Oracle, etc.) previo a procesos de migración (ej. hacia GCP).

Permite un flujo *Human-in-the-Loop* rápido, auditable y ligero en memoria.

---

## 🚀 Flujo de Trabajo

1. **01 / Carga y Resumen:**
   - Carga de archivos CSV o ZIP con extracciones de tablas.
   - Perfilado automático (detección de palabras clave duras/medias de PII, regex de correos, conteo de nulos, valores únicos y muestras).
   - Métricas y KPIs de riesgo (🔴 Alta, 🟡 Media, 🟢 Baja).

2. **02 / Workspace de Revisión:**
   - Tabla interactiva editable para marcar/desmarcar campos como PII y agregar observaciones.
   - Vista agrupada por tabla o por nivel de riesgo.
   - Botón de acceso directo para inspección profunda.

3. **03 / Deep Dive:**
   - Inspección bajo demanda (*On-Demand*) de la muestra completa de la tabla.
   - Fijación de columnas clave para revisión humana exhaustiva.

4. **04 / Exportación:**
   - Requiere guardar la sesión de trabajo con un identificador claro (ej. `INVENTARIO`, `CAPEX`).
   - Genera dinámicamente el reporte oficial en Excel con el prefijo de la sesión guardada (`{SESION}_PII_Validado_Final.xlsx`).

---

## 💾 Persistencia de Sesiones

- Permite guardar y recuperar sesiones locales en la carpeta `sessions/`.
- Permite actualizar/sobrescribir sesiones activas o guardar con nuevos nombres en cualquier momento.

---

## 🛠️ Instalación y Uso

1. Clonar el repositorio:
   ```bash
   git clone https://github.com/mauriled/analisis-pii.git
   cd analisis-pii
   ```

2. Instalar dependencias:
   ```bash
   pip install -r requirements.txt
   ```

3. Ejecutar la aplicación:
   ```bash
   streamlit run app.py
   ```
