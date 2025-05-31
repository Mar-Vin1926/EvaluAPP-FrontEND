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

# URL base de la API (puedes cambiarla según sea necesario)
API_BASE_URL = os.getenv("API_URL", "http://localhost:8080/api")

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
        response = requests.post(
            f"{API_BASE_URL}/auth/login",
            json={"username": username, "password": password}
        )
        if response.status_code == 200:
            return response.json()["token"]
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

def main():
    st.title("📊 EvaluApp - Panel de Control")
    
    # Verificar autenticación
    token = sidebar_auth()
    
    if not token:
        st.warning("Por favor inicia sesión para continuar")
        return
    
    # Menú de navegación
    menu = ["Inicio", "Exámenes", "Resultados", "Usuarios"]
    choice = st.sidebar.selectbox("Menú", menu)
    
    headers = {"Authorization": f"Bearer {token}"}
    
    if choice == "Inicio":
        st.header("Bienvenido a EvaluApp")
        st.write("Selecciona una opción del menú para comenzar.")
        
        # Mostrar estadísticas rápidas
        try:
            stats = requests.get(f"{API_BASE_URL}/stats", headers=headers).json()
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Exámenes", stats.get("total_exams", 0))
            with col2:
                st.metric("Total Usuarios", stats.get("total_users", 0))
            with col3:
                st.metric("Promedio Calificación", f"{stats.get('average_score', 0):.1f}")
        except:
            pass
    
    elif choice == "Exámenes":
        st.header("📝 Gestión de Exámenes")
        
        # Listar exámenes
        exams = requests.get(f"{API_BASE_URL}/exams", headers=headers).json()
        if exams:
            df = pd.DataFrame(exams)
            st.dataframe(df, use_container_width=True)
        else:
            st.info("No hay exámenes disponibles")
    
    elif choice == "Resultados":
        st.header("📊 Resultados de Exámenes")
        
        # Listar resultados
        results = requests.get(f"{API_BASE_URL}/results", headers=headers).json()
        if results:
            df = pd.DataFrame(results)
            st.dataframe(df, use_container_width=True)
        else:
            st.info("No hay resultados disponibles")
    
    elif choice == "Usuarios":
        st.header("👥 Gestión de Usuarios")
        
        # Listar usuarios
        users = requests.get(f"{API_BASE_URL}/users", headers=headers).json()
        if users:
            df = pd.DataFrame(users)
            st.dataframe(df, use_container_width=True)
        else:
            st.info("No hay usuarios registrados")

if __name__ == "__main__":
    main()
