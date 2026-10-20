import streamlit as st
import pandas as pd
import io
import re
import zipfile
import os
import pickle

st.set_page_config(page_title="PII Validator", layout="wide", initial_sidebar_state="expanded")

# Hack para ocultar menús de Streamlit y botón Deploy
st.markdown("""
    <style>
        #MainMenu {visibility: hidden;}
        .stAppDeployButton {display:none;}
        footer {visibility: hidden;}
    </style>
""", unsafe_allow_html=True)

# Palabras clave
hard_pii_keywords = ['EMAIL', 'PHONE', 'FAX', 'DNI', 'CUIT', 'RUC', 'SSN', 'VAT', 'FIRST_NAME', 'LAST_NAME', 'DOB', 'BIRTH', 'ADDRESS', 'IDENTIFIER']
medium_pii_keywords = ['CREATED_BY', 'LAST_UPDATED_BY', 'LAST_UPDATE_LOGIN', 'AUTHORIZED_BY', 'CANCELLED_BY', 'APPROVER_ID', 'USER_ID', 'PERSON_ID', 'DELIVER_TO_PERSON_ID', 'AGENT_ID', 'WORKER_ID', 'NAME', 'USER', 'PERSON']
email_regex = re.compile(r'^[\w\.-]+@[\w\.-]+\.\w+$')

def check_keywords(col_upper, keywords):
    col_spaced = col_upper.replace('_', ' ').replace('.', ' ')
    for kw in keywords:
        kw_spaced = kw.replace('_', ' ')
        if len(kw_spaced) <= 4:
            if re.search(rf"\b{kw_spaced}\b", col_spaced):
                return True
        else:
            if kw_spaced in col_spaced:
                return True
    return False

def profile_dataframe(df, table_name):
    profiles = []
    total_rows = len(df)
    
    for col in df.columns:
        col_upper = str(col).upper()
        risk_tag = "🟢 Baja"
        risk_reason = "No detectado"
        approve_default = False
        
        if check_keywords(col_upper, hard_pii_keywords):
            risk_tag = "🔴 Alta"
            risk_reason = "Nombre de columna sugiere PII fuerte"
            approve_default = True
        elif check_keywords(col_upper, medium_pii_keywords):
            risk_tag = "🟡 Media"
            risk_reason = "Columna de auditoría/usuario"
            approve_default = True
            
        if risk_tag in ["🟡 Media", "🟢 Baja"]:
            sample_vals = df[col].dropna().astype(str).head(200)
            for val in sample_vals:
                if email_regex.match(val.strip()):
                    risk_tag = "🔴 Alta"
                    risk_reason = "Se detectaron correos en los datos"
                    approve_default = True
                    break

        valid_data = df[col].dropna()
        top_3 = valid_data.value_counts().head(3).index.tolist()
        random_3 = valid_data.sample(min(3, len(valid_data))).tolist() if len(valid_data) > 0 else []
        
        null_count = df[col].isnull().sum()
        null_perc = round((null_count / total_rows) * 100, 1) if total_rows > 0 else 100
        unique_count = df[col].nunique()
        
        profiles.append({
            "🔍 Inspeccionar": False,
            "Aprobar PII": approve_default,
            "Riesgo": risk_tag,
            "Table": table_name,
            "Field_name": col,
            "Total Registros": total_rows,
            "Cant. Nulos": null_count,
            "% Nulos": f"{null_perc}%",
            "Cant. Únicos": unique_count,
            "Top 3 Valores": str(top_3),
            "Valores Aleatorios": str(random_3),
            "Comentarios": "",
            "Motivo Algoritmo": risk_reason,
            "Database": "ORACLE"
        })
    return profiles

def load_full_table(table_name):
    for fname, fbytes in st.session_state["files_data"].items():
        if fname.endswith('.zip'):
            with zipfile.ZipFile(io.BytesIO(fbytes)) as z:
                for info in z.infolist():
                    if info.filename.endswith('.csv') and table_name in info.filename:
                        with z.open(info) as f:
                            try:
                                return pd.read_csv(f, on_bad_lines='skip', encoding='utf-8')
                            except:
                                f.seek(0)
                                return pd.read_csv(f, on_bad_lines='skip', encoding='latin1')
        else:
            if table_name in fname:
                try:
                    return pd.read_csv(io.BytesIO(fbytes), on_bad_lines='skip', encoding='utf-8')
                except:
                    return pd.read_csv(io.BytesIO(fbytes), on_bad_lines='skip', encoding='latin1')
    return pd.DataFrame()


def save_session(session_name):
    os.makedirs("sessions", exist_ok=True)
    filepath = f"sessions/{session_name}.pkl"
    with open(filepath, "wb") as f:
        pickle.dump({
            "master_df": st.session_state.get("master_df", pd.DataFrame()),
            "files_data": st.session_state.get("files_data", {})
        }, f)
    st.session_state["active_session"] = session_name

@st.dialog("Guardar Sesión")
def modal_guardar_sesion():
    active = st.session_state.get("active_session")
    if active:
        st.write(f"Estás trabajando en la sesión: **{active}**")
        if st.button(f"Sobrescribir '{active}'", type="primary", use_container_width=True):
            save_session(active)
            st.rerun()
        st.markdown("---")
        st.write("O guardar como una sesión nueva:")
    else:
        st.write("Escribí un nombre para tu progreso. Si el nombre ya existe, te pedirá confirmación para pisarlo.")
        
    s_name = st.text_input("Nombre de sesión nueva:", key="input_modal_session_name")
    if s_name:
        clean = s_name.strip()
        filepath = f"sessions/{clean}.pkl"
        if os.path.exists(filepath) and clean != active:
            st.warning(f"Ya existe una sesión con el nombre '{clean}'.")
            if st.button("Sobrescribir", key="btn_overwrite_modal"):
                save_session(clean)
                st.rerun()
        else:
            if st.button("Guardar como nuevo", key="btn_save_new_modal"):
                save_session(clean)
                st.rerun()

@st.dialog("Eliminar Sesión")
def modal_eliminar_sesion(session_to_delete):
    st.warning(f"¿Estás seguro de que querés eliminar la sesión '{session_to_delete}' de forma permanente?")
    if st.button("Sí, eliminar", type="primary"):
        filepath = f"sessions/{session_to_delete}.pkl"
        if os.path.exists(filepath):
            os.remove(filepath)
        if st.session_state.get("active_session") == session_to_delete:
            st.session_state["active_session"] = None
        st.rerun()

# Estado global
if "current_page" not in st.session_state:
    st.session_state["current_page"] = "01 / Carga y Resumen"
if "master_df" not in st.session_state:
    st.session_state["master_df"] = pd.DataFrame()
if "files_data" not in st.session_state:
    st.session_state["files_data"] = {} # dict de fname -> bytes
if "inspect_target" not in st.session_state:
    st.session_state["inspect_target"] = None # {"table": "NAME", "field": "NAME"}
if "active_session" not in st.session_state:
    st.session_state["active_session"] = None

# Sidebar Navegación
with st.sidebar:
    st.markdown("<br><b>NAVEGACIÓN</b>", unsafe_allow_html=True)
    pages = ["01 / Carga y Resumen", "02 / Workspace de Revisión", "03 / Deep Dive", "04 / Exportación"]
    for p in pages:
        if st.button(p, use_container_width=True, type="primary" if st.session_state["current_page"] == p else "secondary"):
            st.session_state["current_page"] = p
            st.rerun()
            
    st.markdown("---")
    if not st.session_state["master_df"].empty:
        total_aprobados = st.session_state["master_df"]["Aprobar PII"].sum()
        st.info(f"**{total_aprobados}** campos aprobados como PII en total.")
        active = st.session_state.get("active_session")
        if active:
            st.caption(f"📁 Sesión activa: **{active}**")
        else:
            st.caption("📁 Sesión activa: *(Sin guardar)*")
        
    st.markdown("---")
    st.markdown("<br><b>SESIONES LOCALES</b>", unsafe_allow_html=True)

    if st.button("Guardar estado actual", use_container_width=True):
        if st.session_state["master_df"].empty:
            st.error("Cargá datos primero.")
        else:
            modal_guardar_sesion()
            
    st.markdown("<br>", unsafe_allow_html=True)
    os.makedirs("sessions", exist_ok=True)
    saved_sessions = [f.replace(".pkl", "") for f in os.listdir("sessions") if f.endswith(".pkl")]
    if saved_sessions:
        load_name = st.selectbox("Abrir sesión guardada:", saved_sessions)
        colC, colD = st.columns(2)
        with colC:
            if st.button("Cargar", use_container_width=True):
                with open(f"sessions/{load_name}.pkl", "rb") as f:
                    data = pickle.load(f)
                    st.session_state["master_df"] = data["master_df"]
                    st.session_state["files_data"] = data["files_data"]
                    st.session_state["active_session"] = load_name
                st.rerun()
        with colD:
            if st.button("Eliminar", use_container_width=True):
                modal_eliminar_sesion(load_name)

page = st.session_state["current_page"]
st.title(f"Auditoría PII — {page.split(' / ')[1] if ' / ' in page else page}")

if page == "01 / Carga y Resumen":
    st.write("Subí tus extracciones de base de datos para iniciar el escaneo de PII. El sistema perfilará las columnas y sugerirá un nivel de riesgo inicial.")
    uploaded_files = st.file_uploader("Arrastra los archivos CSV o un archivo ZIP", type=["csv", "zip"], accept_multiple_files=True)
    
    if st.button("Procesar Archivos", type="primary"):
        if not uploaded_files:
            st.warning("Primero subí al menos un archivo CSV o ZIP para procesar.")
        else:
            all_profiles = []
            files_dict = {}
            with st.spinner("Perfilando datos y guardando en memoria..."):
                for file in uploaded_files:
                    fbytes = file.getvalue()
                    files_dict[file.name] = fbytes
                    if file.name.endswith('.zip'):
                        with zipfile.ZipFile(io.BytesIO(fbytes)) as z:
                            for info in z.infolist():
                                if info.filename.endswith('.csv'):
                                    with z.open(info) as f:
                                        try:
                                            df = pd.read_csv(f, nrows=1000, on_bad_lines='skip', encoding='utf-8')
                                        except:
                                            f.seek(0)
                                            df = pd.read_csv(f, nrows=1000, on_bad_lines='skip', encoding='latin1')
                                        t_name = os.path.basename(info.filename).replace('_MUESTRA_PII.csv', '').replace('.csv', '')
                                        all_profiles.extend(profile_dataframe(df, t_name))
                    else:
                        try:
                            df = pd.read_csv(io.BytesIO(fbytes), nrows=1000, on_bad_lines='skip', encoding='utf-8')
                        except:
                            df = pd.read_csv(io.BytesIO(fbytes), nrows=1000, on_bad_lines='skip', encoding='latin1')
                        t_name = os.path.basename(file.name).replace('_MUESTRA_PII.csv', '').replace('.csv', '')
                        all_profiles.extend(profile_dataframe(df, t_name))
                        
            st.session_state["files_data"] = files_dict
            master = pd.DataFrame(all_profiles)
            risk_order = {"🔴 Alta": 1, "🟡 Media": 2, "🟢 Baja": 3}
            if not master.empty:
                master["_sort_order"] = master["Riesgo"].map(risk_order)
                master = master.sort_values(by=["_sort_order", "Table", "Field_name"]).drop(columns=["_sort_order"]).reset_index(drop=True)
            st.session_state["master_df"] = master
            st.session_state["active_session"] = None
            st.success("¡Datos cargados y escaneados con éxito!")

    if not st.session_state["master_df"].empty:
        df = st.session_state["master_df"]
        st.markdown("---")
        st.markdown("### KPIs Generales")
        
        total_tablas = df["Table"].nunique()
        total_altas = len(df[df["Riesgo"] == "🔴 Alta"])
        total_medias = len(df[df["Riesgo"] == "🟡 Media"])
        total_bajas = len(df[df["Riesgo"] == "🟢 Baja"])
        
        kpi1, kpi2, kpi3, kpi4 = st.columns(4)
        kpi1.metric("Tablas Procesadas", total_tablas)
        kpi2.metric("🔴 Riesgo Alto", total_altas)
        kpi3.metric("🟡 Riesgo Medio", total_medias)
        kpi4.metric("🟢 Riesgo Bajo", total_bajas)
        
        st.markdown("<br>### Detalle por Tabla", unsafe_allow_html=True)
        summary_data = []
        for i, t in enumerate(df["Table"].unique(), start=1):
            sub = df[df["Table"] == t]
            campos_total = len(sub)
            high = len(sub[sub["Riesgo"] == "🔴 Alta"])
            med = len(sub[sub["Riesgo"] == "🟡 Media"])
            low = len(sub[sub["Riesgo"] == "🟢 Baja"])
            rows = sub["Total Registros"].iloc[0] if len(sub) > 0 else 0
            
            summary_data.append({
                "#": i,
                "Nombre de la tabla": t,
                "Campos": campos_total,
                "🔴 Altas": high,
                "🟡 Medias": med,
                "🟢 Bajas": low,
                "Registros": rows
            })
            
        summary_df = pd.DataFrame(summary_data)
        st.dataframe(summary_df, hide_index=True, use_container_width=True)

elif page == "02 / Workspace de Revisión":
    if st.session_state["master_df"].empty:
        st.warning("No hay datos cargados. Por favor, subí tus archivos en la pantalla de **Carga y Resumen**.")
    else:
        colA, colB = st.columns([1, 2])
        with colA:
            agrupar_por = st.radio("Agrupar vista por:", ["Tabla", "Nivel de Riesgo"], horizontal=True)
        with colB:
            opt_cols = ["Total Registros", "Cant. Nulos", "% Nulos", "Cant. Únicos", "Top 3 Valores", "Valores Aleatorios", "Database", "Table", "Motivo Algoritmo"]
            def_cols = ["% Nulos", "Cant. Únicos", "Top 3 Valores", "Valores Aleatorios"]
            visible_cols = st.multiselect("Columnas adicionales visibles:", opt_cols, default=def_cols)
        
        base_cols = ["🔍 Inspeccionar", "Aprobar PII", "Riesgo", "Field_name", "Comentarios"]
        if agrupar_por == "Nivel de Riesgo" and "Table" not in visible_cols:
            base_cols.insert(3, "Table")
            
        final_cols = base_cols + visible_cols
        master_df = st.session_state["master_df"]
        groups = master_df["Table"].unique() if agrupar_por == "Tabla" else ["🔴 Alta", "🟡 Media", "🟢 Baja"]
        
        for g in groups:
            if agrupar_por == "Tabla":
                sub_df = master_df[master_df["Table"] == g]
                expander_title = f"Tabla: {g} ({len(sub_df)} campos totales)"
            else:
                sub_df = master_df[master_df["Riesgo"] == g]
                if sub_df.empty: continue
                expander_title = f"{g} ({len(sub_df)} campos totales)"
                
            # expanded=False por defecto para no saturar, el usuario abre el que necesita y se queda abierto
            with st.expander(expander_title, expanded=False):
                approved_c = sub_df["Aprobar PII"].sum()
                
                col_prog, col_mark, col_unmark = st.columns([2, 1, 1])
                with col_prog:
                    st.markdown(f"<div style='margin-top: 5px'><b>Progreso:</b> {approved_c} seleccionados</div>", unsafe_allow_html=True)
                with col_mark:
                    if st.button("Marcar todos", key=f"mark_all_{g}", use_container_width=True):
                        if agrupar_por == "Tabla":
                            st.session_state["master_df"].loc[st.session_state["master_df"]["Table"] == g, "Aprobar PII"] = True
                        else:
                            st.session_state["master_df"].loc[st.session_state["master_df"]["Riesgo"] == g, "Aprobar PII"] = True
                        st.rerun()
                with col_unmark:
                    if st.button("Desmarcar todos", key=f"unmark_all_{g}", use_container_width=True):
                        if agrupar_por == "Tabla":
                            st.session_state["master_df"].loc[st.session_state["master_df"]["Table"] == g, "Aprobar PII"] = False
                        else:
                            st.session_state["master_df"].loc[st.session_state["master_df"]["Riesgo"] == g, "Aprobar PII"] = False
                        st.rerun()
                
                view_df = sub_df[final_cols]
                
                edited_sub = st.data_editor(
                    view_df,
                    key=f"editor_{g}",
                    hide_index=True,
                    use_container_width=True,
                    disabled=[c for c in final_cols if c not in ["Aprobar PII", "Comentarios", "🔍 Inspeccionar"]]
                )
                
                must_rerun = False
                for idx in edited_sub.index:
                    if edited_sub.at[idx, "🔍 Inspeccionar"]:
                        st.session_state["inspect_target"] = {"table": master_df.at[idx, "Table"], "field": master_df.at[idx, "Field_name"]}
                        st.session_state["current_page"] = "03 / Deep Dive"
                        master_df.at[idx, "🔍 Inspeccionar"] = False
                        must_rerun = True
                    else:
                        master_df.at[idx, "Aprobar PII"] = edited_sub.at[idx, "Aprobar PII"]
                        master_df.at[idx, "Comentarios"] = edited_sub.at[idx, "Comentarios"]
                        
                if must_rerun:
                    st.rerun()

elif page == "03 / Deep Dive":
    if st.session_state["master_df"].empty:
        st.warning("No hay datos cargados. Por favor, subí tus archivos en la pantalla de **Carga y Resumen**.")
    else:
        master_df = st.session_state["master_df"]
        all_tables = master_df["Table"].unique().tolist()
        
        # Determine defaults based on inspect target
        def_table = all_tables[0]
        def_field = ""
        target = st.session_state["inspect_target"]
        if target and target["table"] in all_tables:
            def_table = target["table"]
            def_field = target["field"]
            
        col1, col2 = st.columns(2)
        with col1:
            selected_table = st.selectbox("Seleccionar Tabla a cargar (CSV Completo)", all_tables, index=all_tables.index(def_table))
        
        # Load the dataframe on demand
        with st.spinner(f"Cargando {selected_table} en memoria completa..."):
            full_df = load_full_table(selected_table)
            
        if full_df.empty:
            st.error("No se pudo cargar la tabla. Asegurate de haber subido los archivos en el paso 1.")
        else:
            all_fields = full_df.columns.tolist()
            with col2:
                # If target field exists in the table, set it as default index
                field_idx = all_fields.index(def_field) if def_field in all_fields else 0
                selected_field = st.selectbox("Fijar Campo a la izquierda", all_fields, index=field_idx)
                
            st.success(f"Se cargaron **{len(full_df)}** registros completos.")
            
            # Reorder columns so the selected field is first
            if selected_field in full_df.columns:
                cols = [selected_field] + [c for c in full_df.columns if c != selected_field]
                view_df = full_df[cols]
            else:
                view_df = full_df
                
            st.dataframe(view_df, hide_index=True, use_container_width=True)

elif page == "04 / Exportación":
    if st.session_state["master_df"].empty:
        st.warning("No hay datos cargados. Por favor, subí tus archivos en la pantalla de **Carga y Resumen**.")
    else:
        master_df = st.session_state["master_df"]
        approved_df = master_df[master_df["Aprobar PII"] == True]
        
        if approved_df.empty:
            st.info("Todavía no aprobaste ningún campo. Andá al **Workspace de Revisión** y tildá los campos sensibles.")
        else:
            st.markdown(f"### Reporte Listo\nVas a exportar **{len(approved_df)}** campos confirmados como PII.")
            export_df = pd.DataFrame()
            export_df["Database"] = approved_df["Database"]
            export_df["Table"] = approved_df["Table"]
            export_df["Field_name"] = approved_df["Field_name"]
            export_df["PII (Y/N)"] = "Y"
            export_df["Detection_Reason"] = approved_df["Motivo Algoritmo"]
            export_df["Review_Comments"] = approved_df["Comentarios"]
            export_df["Example_Value"] = approved_df["Valores Aleatorios"].apply(lambda x: eval(x)[0] if pd.notnull(x) and len(eval(x))>0 else "<Vacío>")
            
            st.dataframe(export_df, hide_index=True, use_container_width=True)
            
            st.markdown("---")
            active_session = st.session_state.get("active_session")
            
            if not active_session:
                st.warning("⚠️ **Sesión no guardada:** Para poder exportar el reporte oficial, primero debés guardar la sesión de trabajo.")
                
                with st.container(border=True):
                    st.markdown("#### 💾 Guardar Sesión para Exportar")
                    st.write("Escribí un nombre para tu sesión (por ejemplo: `INVENTARIO`). El nombre de la sesión se usará automáticamente como prefijo del archivo Excel.")
                    col_save_txt, col_save_btn = st.columns([3, 1])
                    with col_save_txt:
                        s_name_input = st.text_input("Nombre de sesión:", placeholder="Ej: INVENTARIO", key="export_session_input", label_visibility="collapsed")
                    with col_save_btn:
                        btn_guardar_export = st.button("Guardar Sesión", type="primary", use_container_width=True, key="btn_save_export")
                    
                    if btn_guardar_export:
                        s_clean = s_name_input.strip()
                        if not s_clean:
                            st.error("Por favor, ingresá un nombre para la sesión.")
                        else:
                            filepath = f"sessions/{s_clean}.pkl"
                            if os.path.exists(filepath) and st.session_state.get("export_confirm_overwrite") != s_clean:
                                st.session_state["export_confirm_overwrite"] = s_clean
                                st.warning(f"Ya existe una sesión llamada '{s_clean}'. Hacé clic nuevamente en **Guardar Sesión** para sobrescribirla.")
                            else:
                                st.session_state["export_confirm_overwrite"] = None
                                save_session(s_clean)
                                st.success(f"¡Sesión '{s_clean}' guardada con éxito!")
                                st.rerun()
            else:
                prefix = active_session.strip().replace(" ", "_")
                excel_filename = f"{prefix}_PII_Validado_Final.xlsx"
                
                col_info, col_rename = st.columns([3, 1])
                with col_info:
                    st.success(f"📁 **Sesión guardada:** `{active_session}`  \n📄 **Archivo a generar:** `{excel_filename}`")
                with col_rename:
                    if st.button("Cambiar / Guardar como...", use_container_width=True, key="btn_rename_export"):
                        modal_guardar_sesion()
                
                output = io.BytesIO()
                with pd.ExcelWriter(output, engine='openpyxl') as writer:
                    export_df.to_excel(writer, index=False, sheet_name="PII_FINAL")
                
                st.markdown("<br>", unsafe_allow_html=True)
                st.download_button(
                    label=f"Descargar Excel ({excel_filename})",
                    data=output.getvalue(),
                    file_name=excel_filename,
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    type="primary",
                    use_container_width=True
                )
