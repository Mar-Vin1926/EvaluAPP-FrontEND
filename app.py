import streamlit as st
import requests
import pandas as pd
from datetime import datetime
import os
from dotenv import load_dotenv
from api_routes import ENDPOINTS, build_url

# Configuración de la página
st.set_page_config(
    page_title="EvaluApp - Sistema de Evaluación",
    page_icon="📊",
    layout="wide"
)

# Cargar variables de entorno
load_dotenv()

# Definir roles y sus respectivos headers
ROLES = {
    "admin": "ADMIN",
    "teacher": "TEACHER",
    "student": "STUDENT"
}

# Función para seleccionar rol
def select_role():
    st.sidebar.title("👤 Selecciona tu Rol")
    role = None
    
    if 'role' not in st.session_state:
        with st.sidebar.form("role_form"):
            role = st.selectbox("Selecciona tu rol", ["admin", "teacher", "student"])
            if st.form_submit_button("Continuar"):
                st.session_state.role = role
                st.rerun()
    else:
        st.sidebar.success(f"Rol seleccionado: {st.session_state.role}")
        if st.sidebar.button("Cambiar Rol"):
            del st.session_state.role
            st.rerun()
        role = st.session_state.role
    
    return role

def get_headers():
    """Devuelve los headers para las peticiones según el rol"""
    if 'role' in st.session_state:
        return {"X-Role": ROLES[st.session_state.role]}
    return {}

def make_request(method, endpoint, headers=None, data=None):
    """Función auxiliar para hacer peticiones HTTP"""
    try:
        # Construir URL usando el módulo de rutas
        url = build_url(endpoint)
        st.info(f"Haciendo petición a: {url}")
        
        # Mostrar detalles de la petición para debugging
        st.info(f"Método: {method}")
        st.info(f"Headers: {headers}")
        st.info(f"Data: {data}")
        
        response = requests.request(method, url, headers=headers, json=data)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Error en la petición: {e}")
        st.error(f"URL de la API: {url}")
        return None

def main():
    st.title("📊 EvaluApp - Panel de Control")
    
    # Seleccionar rol
    role = select_role()
    
    if not role:
        st.warning("Por favor selecciona tu rol para continuar")
        return
    
    # Menú de navegación según el rol
    if role == "admin":
        menu = ["Inicio", "Exámenes", "Resultados", "Usuarios", "Configuración"]
    elif role == "teacher":
        menu = ["Inicio", "Exámenes", "Resultados"]
    else:  # student
        menu = ["Inicio", "Exámenes", "Resultados"]
    
    choice = st.sidebar.selectbox("Menú", menu)
    
    # Obtener headers con el rol
    headers = get_headers()
    
    if choice == "Inicio":
        st.header(" Bienvenido a EvaluApp")
        st.write("Selecciona una opción del menú para comenzar.")
    
    elif choice == "Exámenes":
        st.header("📝 Exámenes")
        
        # Verificar el rol para mostrar las funcionalidades correctas
        if role in ["admin", "teacher"]:
            # Para admins y teachers: crear y gestionar exámenes
            st.subheader("Gestión de Exámenes")
            
            # Crear nuevo examen
            with st.expander("➕ Crear Nuevo Examen"):
                with st.form("create_exam"):
                    title = st.text_input("Título del Examen")
                    description = st.text_area("Descripción")
                    if st.form_submit_button("Crear Examen"):
                        data = {
                            "title": title,
                            "description": description
                        }
                        result = make_request("POST", ENDPOINTS["examenes"], headers=headers, data=data)
                        if result:
                            st.success("Examen creado exitosamente!")
                            st.rerun()
            
            # Listar y gestionar exámenes
            examenes = make_request("GET", ENDPOINTS["examenes"], headers=headers)
            if examenes:
                df = pd.DataFrame(examenes)
                st.dataframe(df, use_container_width=True)
                
                # Acciones para exámenes específicos
                exam_id = st.selectbox("Seleccionar Examen", df["id"])
                if exam_id:
                    selected_exam = next((e for e in examenes if e["id"] == exam_id), None)
                    if selected_exam:
                        # Editar examen
                        with st.expander("✏️ Editar Examen"):
                            with st.form("edit_exam"):
                                title = st.text_input("Título", selected_exam["title"])
                                description = st.text_area("Descripción", selected_exam["description"])
                                if st.form_submit_button("Actualizar"):
                                    data = {
                                        "title": title,
                                        "description": description
                                    }
                                    result = make_request("PUT", f"{ENDPOINTS['examenes']}/{exam_id}", headers=headers, data=data)
                                    if result:
                                        st.success("Examen actualizado exitosamente!")
                                        st.rerun()
                        
                        # Gestión de preguntas y opciones
                        with st.expander("📝 Gestión de Preguntas"):
                            # Listar preguntas del examen
                            questions = make_request("GET", f"{ENDPOINTS['exams']}/{exam_id}/questions", headers=headers)
                            if questions:
                                st.dataframe(questions, use_container_width=True)
                                
                                # Crear nueva pregunta
                                with st.form("create_question"):
                                    question_text = st.text_area("Texto de la Pregunta")
                                    correct_option = st.selectbox("Opción Correcta", ["A", "B", "C", "D"])
                                    if st.form_submit_button("Crear Pregunta"):
                                        data = {
                                            "text": question_text,
                                            "correct_option": correct_option
                                        }
                                        result = make_request("POST", f"{ENDPOINTS['examenes']}/{exam_id}/preguntas", headers=headers, data=data)
                                        if result:
                                            st.success("Pregunta creada exitosamente!")
                                            st.rerun()
                                
                                # Editar pregunta
                                question_id = st.selectbox("Seleccionar Pregunta", [q["id"] for q in questions])
                                if question_id:
                                    selected_question = next((q for q in questions if q["id"] == question_id), None)
                                    if selected_question:
                                        with st.form("edit_question"):
                                            question_text = st.text_area("Texto de la Pregunta", selected_question["text"])
                                            correct_option = st.selectbox("Opción Correcta", ["A", "B", "C", "D"], index=["A", "B", "C", "D"].index(selected_question["correct_option"]))
                                            if st.form_submit_button("Actualizar Pregunta"):
                                                data = {
                                                    "text": question_text,
                                                    "correct_option": correct_option
                                                }
                                                result = make_request("PUT", f"{ENDPOINTS['preguntas']}/{question_id}", headers=headers, data=data)
                                                if result:
                                                    st.success("Pregunta actualizada exitosamente!")
                                                    st.rerun()
                                
                                # Eliminar pregunta
                                if st.button("🗑️ Eliminar Pregunta"):
                                    if st.confirm("¿Estás seguro de eliminar esta pregunta?"):
                                        result = make_request("DELETE", f"{ENDPOINTS['preguntas']}/{question_id}", headers=headers)
                                        if result:
                                            st.success("Pregunta eliminada exitosamente!")
                                            st.rerun()
                        
                        # Eliminar examen
                        if st.button("🗑️ Eliminar Examen"):
                            if st.confirm("¿Estás seguro de eliminar este examen?"):
                                result = make_request("DELETE", f"{ENDPOINTS['examenes']}/{exam_id}", headers=headers)
                                if result:
                                    st.success("Examen eliminado exitosamente!")
                                    st.rerun()
            else:
                st.info("No hay exámenes disponibles")
        
        elif role == "student":
            # Para estudiantes: realizar exámenes
            st.subheader("Realizar Exámenes")
            
            # Listar exámenes disponibles
            examenes = make_request("GET", ENDPOINTS["examenes"], headers=headers)
            if examenes:
                df = pd.DataFrame(examenes)
                st.dataframe(df, use_container_width=True)
                
                # Seleccionar examen para realizar
                exam_id = st.selectbox("Seleccionar Examen para Realizar", df["id"])
                if exam_id:
                    with st.form("take_exam"):
                        # Obtener preguntas del examen
                        preguntas = make_request("GET", f"{ENDPOINTS['exaexamenesms']}/{exam_id}/preguntas", headers=headers)
                        if preguntas:
                            answers = {}
                            for q in preguntas:
                                st.subheader(f"Pregunta {q['id']}: {q['text']}")
                                answers[q['id']] = st.selectbox(f"Respuesta para pregunta {q['id']}", ["A", "B", "C", "D"])
                            
                            if st.form_submit_button("Enviar Examen"):
                                result = make_request("POST", f"{ENDPOINTS['examenes']}/{exam_id}/submit", headers=headers, data={"answers": answers})
                                if result:
                                    st.success("Examen enviado exitosamente!")
                                    st.info(f"Calificación: {result['score']} / {len(questions)}")
                                    st.rerun()
            else:
                st.info("No hay exámenes disponibles para realizar")
    
    elif choice == "Resultados":
        st.header("📊 Resultados de Exámenes")
        
        # Filtrar resultados
        with st.expander("🔍 Filtrar Resultados"):
            exam_filter = st.selectbox("Filtrar por Examen", ["Todos"] + [e["title"] for e in make_request("GET", ENDPOINTS["examenes"], headers=headers) or []])
            user_filter = st.selectbox("Filtrar por Usuario", ["Todos"] + [u["username"] for u in make_request("GET", ENDPOINTS["api/admin/users"], headers=headers) or []])
        
        # Listar resultados
        params = {}
        if exam_filter != "Todos":
            params["exam"] = exam_filter
        if user_filter != "Todos":
            params["user"] = user_filter
        
        results = make_request("GET", ENDPOINTS["resultados"], headers=headers, params=params)
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
        # Solo los admins pueden ver esta sección
        if st.session_state.role != "admin":
            st.warning("Esta sección solo está disponible para administradores")
            return
            
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
                    result = make_request("POST", ENDPOINTS["api/admin/users"], headers=headers, data=data)
                    if result:
                        st.success("Usuario creado exitosamente!")
                        st.rerun()
        
        # Listar y gestionar usuarios
        users = make_request("GET", ENDPOINTS["api/admin/users"], headers=headers)
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
                                result = make_request("PUT", f"{ENDPOINTS['api/admin/users']}/{user_id}", headers=headers, data=data)
                                if result:
                                    st.success("Usuario actualizado exitosamente!")
                                    st.rerun()
                    
                    if st.button("🗑️ Eliminar Usuario"):
                        if st.confirm("¿Estás seguro de eliminar este usuario?"):
                            result = make_request("DELETE", f"{ENDPOINTS['users']}/{user_id}", headers=headers)
                            if result:
                                st.success("Usuario eliminado exitosamente!")
                                st.rerun()
        else:
            st.info("No hay usuarios registrados")
    
    elif choice == "Configuración":
        # Solo los admins pueden ver esta sección
        if st.session_state.role != "admin":
            st.warning("Esta sección solo está disponible para administradores")
            return
            
        st.header("🔧 Configuración del Sistema")
        
        # Configuración general
        with st.expander("⚙️ Configuración General"):
            with st.form("settings"):
                # Configuraciones específicas
                pass  # Implementar según las necesidades de la API
                
        # Logs y auditoría
        with st.expander("📝 Logs del Sistema"):
            logs = make_request("GET", ENDPOINTS["logs"], headers=headers)
            if logs:
                df = pd.DataFrame(logs)
                st.dataframe(df, use_container_width=True)
            else:
                st.info("No hay logs disponibles")

if __name__ == "__main__":
    main()
