import streamlit as st
import requests
import pandas as pd
from datetime import datetime, date
import os
from dotenv import load_dotenv
from api_routes import ENDPOINTS, build_url
from dataclasses import dataclass
from typing import Optional

@dataclass
class ExamenRequestDTO:
    """DTO para crear un nuevo examen"""
    titulo: str
    descripcion: str
    fechaInicio: date
    fechaFin: date
    creadorId: int
    
    def to_dict(self) -> dict:
        """Convierte el DTO a un diccionario con fechas en formato ISO"""
        return {
            "titulo": self.titulo,
            "descripcion": self.descripcion,
            "fechaInicio": self.fechaInicio.isoformat(),
            "fechaFin": self.fechaFin.isoformat(),
            "creadorId": self.creadorId
        }

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

def crear_examen():
    """
    Función para crear un nuevo examen usando ExamenRequestDTO
    """
    if 'create_exam_form' not in st.session_state:
        st.session_state.create_exam_form = True

    if st.session_state.create_exam_form:
        with st.form(key="form_create_exam", clear_on_submit=True):
            st.header("📝 Crear Nuevo Examen")
            
            # Campos del formulario
            titulo = st.text_input("Título del Examen", "", 
                                 help="Por ejemplo: 'Examen de Matemáticas'")
            descripcion = st.text_area("Descripción", "",
                                     help="Descripción detallada del examen")
            fecha_inicio = st.date_input("Fecha de Inicio", 
                                      datetime.now().date(),
                                      help="Fecha en que el examen estará disponible")
            fecha_fin = st.date_input("Fecha de Fin", 
                                   datetime.now().date() + pd.Timedelta(days=7),
                                   help="Fecha límite para realizar el examen")
            
            if st.form_submit_button("Crear Examen"):
                # Validación de campos
                if not titulo:
                    st.error("Por favor, ingresa un título para el examen")
                    return
                if fecha_inicio >= fecha_fin:
                    st.error("La fecha de inicio debe ser anterior a la fecha de fin")
                    return

                # Crear DTO con los datos del formulario
                try:
                    # Obtener el ID del usuario actual según el rol
                    usuario_id = 1  # Esto debería ser dinámico según el usuario actual
                    
                    examen_dto = ExamenRequestDTO(
                        titulo=titulo,
                        descripcion=descripcion,
                        fechaInicio=fecha_inicio,
                        fechaFin=fecha_fin,
                        usuarioId=usuario_id
                    )
                except Exception as e:
                    st.error(f"Error al crear el DTO: {str(e)}")
                    return

                try:
                    # Hacer la petición POST usando el DTO
                    response = make_request("POST", ENDPOINTS["examenes"], 
                                        headers=get_headers(), 
                                        data=examen_dto.to_dict())
                    
                    if response:
                        st.success("Examen creado con éxito!")
                        st.json(response)
                        st.session_state.create_exam_form = False
                    else:
                        st.error("Error al crear el examen")

                except Exception as e:
                    st.error(f"Error: {str(e)}")
                    if hasattr(e, 'response') and e.response:
                        try:
                            error_detail = e.response.json()
                            st.json(error_detail)
                        except:
                            st.error(f"Detalles del error: {e.response.text}")

                try:
                    # Hacer la petición POST usando el DTO
                    response = make_request("POST", ENDPOINTS["examenes"], 
                                        headers=get_headers(), 
                                        data=examen_dto.to_dict())
                    
                    if response:
                        st.success("Examen creado con éxito!")
                        st.json(response)
                        st.session_state.create_exam_form = False
                    else:
                        st.error("Error al crear el examen")

                except Exception as e:
                    st.error(f"Error: {str(e)}")
                    response = make_request("POST", ENDPOINTS["examenes"], headers=get_headers(), data=payload)
                    
                    if response:
                        st.success("Examen creado con éxito!")
                        st.json(response)
                        st.session_state.create_exam_form = False  # Ocultar el formulario después de crear
                    else:
                        st.error("Error al crear el examen")

                except Exception as e:
                    st.error(f"Error: {str(e)}")

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
                                title = st.text_input("Título", selected_exam.get("title", selected_exam.get("titulo", "")))
                                description = st.text_area("Descripción", selected_exam.get("description", selected_exam.get("descripcion", "")))
                                if st.form_submit_button("Actualizar"):
                                    data = {
                                        "title": title,
                                        "description": description
                                    }
                                    response = make_request("PUT", build_url(f"examenes/{exam_id}"), headers=headers, data=data)
                                    if response:
                                        st.success("Examen actualizado con éxito!")
                                        st.json(response)
                                    else:
                                        st.error("Error al actualizar el examen")

                        # Crear nuevo examen
                        with st.expander("➕ Crear Nuevo Examen"):
                            if st.button("Mostrar formulario de creación"):
                                st.session_state.create_exam_form = True
                            crear_examen()
                        
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
                        preguntas = make_request("GET", f"{ENDPOINTS['examenes']}/{exam_id}/preguntas", headers=headers)
                        if preguntas:
                            answers = {}
                            for q in preguntas:
                                st.subheader(f"Pregunta {q['id']}: {q['text']}")
                                answers[q['id']] = st.selectbox(f"Respuesta para pregunta {q['id']}", ["A", "B", "C", "D"])
                            enviar = st.form_submit_button("Enviar Examen")
                            if enviar:
                                result = make_request("POST", f"{ENDPOINTS['examenes']}/{exam_id}/submit", headers=headers, data={"answers": answers})
                                if result:
                                    st.success("Examen enviado exitosamente!")
                                    st.info(f"Calificación: {result['score']} / {len(preguntas)}")
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
