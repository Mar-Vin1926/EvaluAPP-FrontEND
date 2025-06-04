import streamlit as st
import requests
import pandas as pd
from datetime import datetime, date
import os
from dotenv import load_dotenv
from api_routes import ENDPOINTS, build_url
from dataclasses import dataclass

# ---------------- DTO -------------------
@dataclass
class ExamenRequestDTO:
    titulo: str
    descripcion: str
    fechaInicio: date
    fechaFin: date
    creadorId: int
    preguntasIds: list[int] # Nuevo campo para los IDs de las preguntas

    def to_dict(self) -> dict:
        return {
            "titulo": self.titulo,
            "descripcion": self.descripcion,
            "fechaInicio": self.fechaInicio.isoformat(),
            "fechaFin": self.fechaFin.isoformat(),
            "creadorId": self.creadorId,
            "preguntasIds": self.preguntasIds # Incluir los IDs de las preguntas
        }

# --------------- Configuración -------------------
st.set_page_config(page_title="EvaluApp", page_icon="📊", layout="wide")
load_dotenv()

ROLES = {
    "admin": "ADMIN",
    "teacher": "TEACHER",
    "student": "STUDENT"
}

def select_role():
    st.sidebar.title("👤 Selecciona tu Rol")
    role = None
    if 'role' not in st.session_state:
        with st.sidebar.form("role_form"):
            role = st.selectbox("Selecciona tu rol", list(ROLES.keys()))
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
    if 'role' in st.session_state:
        return {"X-Role": ROLES[st.session_state.role]}
    return {}

def make_request(method, endpoint, headers=None, data=None, params=None):
    try:
        url = build_url(endpoint)
        response = requests.request(method, url, headers=headers, json=data, params=params)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Error en la petición: {e}")
        st.error(f"URL de la API: {url}")
        return None

# ---------------- Función principal de creación -------------------
def crear_examen():
    st.subheader("➕ Crear Nuevo Examen")

    # Obtener preguntas disponibles
    preguntas_disponibles = make_request("GET", ENDPOINTS["preguntas"], headers=get_headers())
    # st.write("Debug - Preguntas disponibles:", preguntas_disponibles) # <-- LÍNEA DE DEPURACIÓN ELIMINADA
    
    if preguntas_disponibles is None or not preguntas_disponibles: # Añadida comprobación de lista vacía
        st.error("No se pudieron cargar las preguntas o no hay preguntas disponibles. Inténtalo de nuevo más tarde o añade preguntas primero.")
        # Opcionalmente, podrías permitir crear el examen sin preguntas si es válido
        # preguntas_disponibles = [] 
        return # O decidir no continuar si las preguntas son cruciales

    # Crear un mapeo de enunciado de pregunta a ID de pregunta
    # La API devuelve 'id' y 'textoPregunta'
    pregunta_options = {pregunta['textoPregunta']: pregunta['id'] for pregunta in preguntas_disponibles}

    with st.form(key="form_create_exam", clear_on_submit=True):
        titulo = st.text_input("Título del Examen")
        descripcion = st.text_area("Descripción")
        fecha_inicio = st.date_input("Fecha de Inicio", datetime.now().date())
        fecha_fin = st.date_input("Fecha de Fin", datetime.now().date() + pd.Timedelta(days=7))
        
        # Selector de preguntas
        selected_enunciados = st.multiselect(
            "Seleccionar Preguntas",
            options=list(pregunta_options.keys()),
            help="Selecciona las preguntas que formarán parte de este examen."
        )

        if st.form_submit_button("Crear Examen"):
            if not titulo:
                st.error("El título es obligatorio")
                return
            if fecha_inicio >= fecha_fin:
                st.error("La fecha de inicio debe ser anterior a la de fin")
                return
            if not selected_enunciados: # Opcional: requerir al menos una pregunta
                st.warning("Es recomendable seleccionar al menos una pregunta para el examen.")
                # Podrías decidir si esto es un error o solo una advertencia

            # Obtener los IDs de las preguntas seleccionadas
            preguntas_seleccionadas_ids = [pregunta_options[enunciado] for enunciado in selected_enunciados]

            try:
                creador_id = 1  # ⚠️ Temporal — reemplazar por el ID del usuario actual logueado
                examen = ExamenRequestDTO(
                    titulo=titulo,
                    descripcion=descripcion,
                    fechaInicio=fecha_inicio,
                    fechaFin=fecha_fin,
                    creadorId=creador_id,
                    preguntasIds=preguntas_seleccionadas_ids # Pasar los IDs seleccionados
                )

                result = make_request(
                    "POST",
                    ENDPOINTS["examenes"],
                    headers=get_headers(),
                    data=examen.to_dict()
                )

                if result:
                    st.success("✅ Examen creado con éxito")
                    st.json(result)
                    st.rerun()
                else:
                    st.error("❌ Error al crear el examen")

            except Exception as e:
                st.error(f"⚠️ Error inesperado: {str(e)}")

# ----------------- Menú Principal -----------------
def main():
    st.title("📊 EvaluApp - Panel de Control")
    role = select_role()
    if not role:
        st.warning("Por favor selecciona tu rol para continuar")
        return

    menu = ["Inicio", "Exámenes", "Resultados", "Usuarios", "Configuración"] if role == "admin" else ["Inicio", "Exámenes", "Resultados"]
    choice = st.sidebar.selectbox("Menú", menu)
    headers = get_headers()

    if choice == "Inicio":
        st.header("Bienvenido a EvaluApp")

    elif choice == "Exámenes":
        st.header("📝 Gestión de Exámenes")
        crear_examen()

        st.subheader("📄 Exámenes Registrados")
        examenes = make_request("GET", ENDPOINTS["examenes"], headers=headers)
        if examenes:
            df = pd.DataFrame(examenes)
            st.dataframe(df, use_container_width=True)
        else:
            st.info("No hay exámenes disponibles.")

    elif choice == "Resultados":
        st.header("📊 Resultados de Exámenes")
        results = make_request("GET", ENDPOINTS["resultados"], headers=headers)
        if results:
            df = pd.DataFrame(results)
            columns_to_hide = ['creadorId', 'CreadorNombre', 'preguntasIds']
            df_display = df.drop(columns=[col for col in columns_to_hide if col in df.columns], errors='ignore')
            st.dataframe(df_display, use_container_width=True)
        else:
            st.info("No hay resultados disponibles.")

    elif choice == "Usuarios":
        if st.session_state.role != "admin":
            st.warning("Esta sección solo está disponible para administradores")
            return
        st.header("👥 Gestión de Usuarios")
        users = make_request("GET", ENDPOINTS["users"], headers=headers)
        if users:
            df = pd.DataFrame(users)
            columns_to_hide = ['creadorId', 'CreadorNombre', 'preguntasIds']
            df_display = df.drop(columns=[col for col in columns_to_hide if col in df.columns], errors='ignore')
            st.dataframe(df_display, use_container_width=True)

    elif choice == "Configuración":
        if st.session_state.role != "admin":
            st.warning("Esta sección solo está disponible para administradores")
            return
        st.header("⚙️ Configuración del Sistema")
        st.info("Aquí puedes agregar configuración avanzada más adelante.")

if __name__ == "__main__":
    main()
