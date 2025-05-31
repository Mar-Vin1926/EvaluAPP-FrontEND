# Rutas de la API
API_BASE_URL = "https://evaluapp.onrender.com/api"

# Endpoints
ENDPOINTS = {
    "auth": "auth/login",
    "stats": "stats",
    "exams": "exams",
    "examenes": "exams",
    "questions": "questions",
    "options": "options",
    "results": "results",
    "users": "users",
    "logs": "logs"
}

# Roles disponibles
ROLES = {
    "admin": "ADMIN",
    "teacher": "TEACHER",
    "student": "STUDENT"
}

# Construir URL completa
def build_url(endpoint):
    return f"{API_BASE_URL}/{endpoint}"

# Funciones auxiliares para construir URLs específicas
def build_exam_url(exam_id):
    return f"{API_BASE_URL}/{ENDPOINTS['exams']}/{exam_id}"

def build_question_url(question_id):
    return f"{API_BASE_URL}/{ENDPOINTS['questions']}/{question_id}"

def build_option_url(option_id):
    return f"{API_BASE_URL}/{ENDPOINTS['options']}/{option_id}"
