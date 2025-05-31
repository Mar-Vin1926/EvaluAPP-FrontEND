import streamlit as st
import requests
import pandas as pd
from datetime import datetime
import os
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Configuración de la página
st.set_page_config(
    page_title="EvaluApp - Sistema de Evaluación",
    page_icon="📊",
    layout="wide"
)

# URL base de la API en Render
API_BASE_URL = os.getenv("API_URL", "https://evaluapp.onrender.com/api")

# Función para hacer peticiones a la API
def fetch_data(endpoint):
    try:
        response = requests.get(f"{API_BASE_URL}/{endpoint}")
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Error al conectar con la API: {e}")
        return None

# Función para autenticación
def login(username, password):
    try:
        data = {
            "username": username,
            "password": password
        }
        result = make_request("POST", "auth/login", data=data)
        if result:
            return result["token"]
        else:
            st.error("Usuario o contraseña incorrectos")
            return None
    except Exception as e:
        st.error(f"Error al iniciar sesión: {e}")
        return None

# Barra lateral para autenticación
def sidebar_auth():
    st.sidebar.title("🔐 Autenticación")
    token = None
    
    if 'token' not in st.session_state:
        with st.sidebar.form("login_form"):
            username = st.text_input("Usuario")
            password = st.text_input("Contraseña", type="password")
            if st.form_submit_button("Iniciar sesión"):
                token = login(username, password)
                if token:
                    st.session_state.token = token
                    st.experimental_rerun()
    else:
        st.sidebar.success("Sesión iniciada")
        if st.sidebar.button("Cerrar sesión"):
            del st.session_state.token
            st.experimental_rerun()
        token = st.session_state.token
    
    return token

def make_request(method, endpoint, headers=None, data=None):
    """Función auxiliar para hacer peticiones HTTP"""
    try:
        url = f"{API_BASE_URL}/{endpoint}"
        response = requests.request(method, url, headers=headers, json=data)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Error en la petición: {e}")
        return None

def main():
    st.title("📊 EvaluApp - Panel de Control")
    
    # Verificar autenticación
    token = sidebar_auth()
    
    if not token:
        st.warning("Por favor inicia sesión para continuar")
        return
    
    # Menú de navegación
    menu = ["Inicio", "Exámenes", "Resultados", "Usuarios", "Configuración"]
    choice = st.sidebar.selectbox("Menú", menu)
    
    headers = {"Authorization": f"Bearer {token}"}
    
    if choice == "Inicio":
        st.header(" Bienvenido a EvaluApp")
        st.write("Selecciona una opción del menú para comenzar.")
        
        # Mostrar estadísticas rápidas
        try:
            stats = make_request("GET", "stats", headers=headers)
            if stats:
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Total Exámenes", stats.get("total_exams", 0))
                with col2:
                    st.metric("Total Usuarios", stats.get("total_users", 0))
                with col3:
                    st.metric("Promedio Calificación", f"{stats.get('average_score', 0):.1f}")
        except Exception as e:
            st.error(f"Error al cargar estadísticas: {e}")
    
    elif choice == "Exámenes":
        st.header("📝 Gestión de Exámenes")
        
        # Crear nuevo examen
        with st.expander("➕ Crear Nuevo Examen"):
            with st.form("create_exam"):
                title = st.text_input("Título del Examen")
                description = st.text_area("Descripción")
                questions = st.number_input("Número de Preguntas", min_value=1, value=5)
                if st.form_submit_button("Crear Examen"):
                    data = {
                        "title": title,
                        "description": description,
                        "questions": questions
                    }
                    result = make_request("POST", "exams", headers=headers, data=data)
                    if result:
                        st.success("Examen creado exitosamente!")
                        st.experimental_rerun()
        
        # Listar y gestionar exámenes
        exams = make_request("GET", "exams", headers=headers)
        if exams:
            df = pd.DataFrame(exams)
            st.dataframe(df, use_container_width=True)
            
            # Acciones para exámenes específicos
            exam_id = st.selectbox("Seleccionar Examen", df["id"])
            if exam_id:
                selected_exam = next((e for e in exams if e["id"] == exam_id), None)
                if selected_exam:
                    with st.expander("✏️ Editar Examen"):
                        with st.form("edit_exam"):
                            title = st.text_input("Título", selected_exam["title"])
                            description = st.text_area("Descripción", selected_exam["description"])
                            if st.form_submit_button("Actualizar"):
                                data = {
                                    "title": title,
                                    "description": description
                                }
                                result = make_request("PUT", f"exams/{exam_id}", headers=headers, data=data)
                                if result:
                                    st.success("Examen actualizado exitosamente!")
                                    st.experimental_rerun()
                    
                    if st.button("🗑️ Eliminar Examen"):
                        if st.confirm("¿Estás seguro de eliminar este examen?"):
                            result = make_request("DELETE", f"exams/{exam_id}", headers=headers)
                            if result:
                                st.success("Examen eliminado exitosamente!")
                                st.experimental_rerun()
        else:
            st.info("No hay exámenes disponibles")
    
    elif choice == "Resultados":
        st.header("📊 Resultados de Exámenes")
        
        # Filtrar resultados
        with st.expander("🔍 Filtrar Resultados"):
            exam_filter = st.selectbox("Filtrar por Examen", ["Todos"] + [e["title"] for e in make_request("GET", "exams", headers=headers) or []])
            user_filter = st.selectbox("Filtrar por Usuario", ["Todos"] + [u["username"] for u in make_request("GET", "users", headers=headers) or []])
        
        # Listar resultados
        params = {}
        if exam_filter != "Todos":
            params["exam"] = exam_filter
        if user_filter != "Todos":
            params["user"] = user_filter
        
        results = make_request("GET", "results", headers=headers, params=params)
        if results:
            df = pd.DataFrame(results)
            st.dataframe(df, use_container_width=True)
            
            # Descargar resultados
            if st.button("📥 Descargar Resultados"):
                csv = df.to_csv(index=False)
                st.download_button(
                    label="Descargar CSV",
                    data=csv,
                    file_name="resultados_examenes.csv",
                    mime="text/csv"
                )
        else:
            st.info("No hay resultados disponibles")
    
    elif choice == "Usuarios":
        st.header("👥 Gestión de Usuarios")
        
        # Crear nuevo usuario
        with st.expander("➕ Crear Nuevo Usuario"):
            with st.form("create_user"):
                username = st.text_input("Nombre de Usuario")
                password = st.text_input("Contraseña", type="password")
                email = st.text_input("Email")
                role = st.selectbox("Rol", ["admin", "teacher", "student"])
                if st.form_submit_button("Crear Usuario"):
                    data = {
                        "username": username,
                        "password": password,
                        "email": email,
                        "role": role
                    }
                    result = make_request("POST", "users", headers=headers, data=data)
                    if result:
                        st.success("Usuario creado exitosamente!")
                        st.experimental_rerun()
        
        # Listar y gestionar usuarios
        users = make_request("GET", "users", headers=headers)
        if users:
            df = pd.DataFrame(users)
            st.dataframe(df, use_container_width=True)
            
            # Acciones para usuarios específicos
            user_id = st.selectbox("Seleccionar Usuario", df["id"])
            if user_id:
                selected_user = next((u for u in users if u["id"] == user_id), None)
                if selected_user:
                    with st.expander("✏️ Editar Usuario"):
                        with st.form("edit_user"):
                            username = st.text_input("Nombre de Usuario", selected_user["username"])
                            email = st.text_input("Email", selected_user["email"])
                            role = st.selectbox("Rol", ["admin", "teacher", "student"], index=["admin", "teacher", "student"].index(selected_user["role"]))
                            if st.form_submit_button("Actualizar"):
                                data = {
                                    "username": username,
                                    "email": email,
                                    "role": role
                                }
                                result = make_request("PUT", f"users/{user_id}", headers=headers, data=data)
                                if result:
                                    st.success("Usuario actualizado exitosamente!")
                                    st.experimental_rerun()
                    
                    if st.button("🗑️ Eliminar Usuario"):
                        if st.confirm("¿Estás seguro de eliminar este usuario?"):
                            result = make_request("DELETE", f"users/{user_id}", headers=headers)
                            if result:
                                st.success("Usuario eliminado exitosamente!")
                                st.experimental_rerun()
        else:
            st.info("No hay usuarios registrados")
    
    elif choice == "Configuración":
        st.header("🔧 Configuración del Sistema")
        
        # Configuración general
        with st.expander("⚙️ Configuración General"):
            with st.form("settings"):
                # Configuraciones específicas
                pass  # Implementar según las necesidades de la API
                
        # Logs y auditoría
        with st.expander("📝 Logs del Sistema"):
            logs = make_request("GET", "logs", headers=headers)
            if logs:
                df = pd.DataFrame(logs)
                st.dataframe(df, use_container_width=True)
            else:
                st.info("No hay logs disponibles")

if __name__ == "__main__":
    main()
