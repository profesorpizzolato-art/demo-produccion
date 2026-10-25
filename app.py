import streamlit as st
import sys
import os

# 1. CONFIGURACIÓN INICIAL
st.set_page_config(page_title="IPCL MENFA - Simulador 3.0", layout="wide")

# 2. MANEJO DE RUTAS
BASE_DIR = os.path.dirname(__file__)
sys.path.append(os.path.join(BASE_DIR, "modulos"))
sys.path.append(os.path.join(BASE_DIR, "motor"))

# 3. IMPORTACIONES DE MÓDULOS INTERNOS
try:
    from manual_simulador import mostrar_manual
except ModuleNotFoundError:
    mostrar_manual = None

try:
    from modulos.nube import leer_estado_actual, enviar_falla, resetear_planta, conectar_db
except Exception as e:
    leer_estado_actual = None
    enviar_falla = None
    resetear_planta = None

# MÓDULO DE FÓRMULAS
try:
    from modulos.formulas_produccion import formulas_produccion
except ModuleNotFoundError:
    formulas_produccion = None

# MOTOR DE SIMULACIÓN
MotorSimulacion = None
try:
    from motor_simulacion import MotorSimulacion
except ModuleNotFoundError:
    try:
        from modulos.motor_simulacion import MotorSimulacion
    except ModuleNotFoundError:
        st.error("⚠️ No se encontró 'motor_simulacion.py'. Verifica las rutas en tu repositorio.")

# 4. INICIALIZACIÓN DEL ESTADO DE SESIÓN
if 'ingresado' not in st.session_state:
    st.session_state.ingresado = False
if 'rol' not in st.session_state:
    st.session_state.rol = "alumno"
if 'area_actual' not in st.session_state:
    st.session_state.area_actual = "🏠 Dashboard"

if 'motor' not in st.session_state and MotorSimulacion is not None:    
    st.session_state.motor = MotorSimulacion()  

# --- FUNCIONES DE ACCESO Y SEGURIDAD ---
def login():
    st.markdown("""
    <style>
    .stApp { background-color: #0e1117; }
    .contenedor-login { position: relative; width: 100%; max-width: 500px; margin: auto; }
    .stTextInput input { background-color: rgba(0,0,0,0) !important; color: white !important; border: none !important; font-size: 16px !important; height: 42px !important; }
    div[data-key="u_pizzolato"] { position: absolute; top: 435px; left: 65px; width: 310px; z-index: 10; }
    div[data-key="p_pizzolato"] { position: absolute; top: 490px; left: 65px; width: 310px; z-index: 10; }
    div[data-key="btn_pizzolato"] { position: absolute; top: 550px; left: 65px; width: 310px; z-index: 10; }
    label { display: none !important; }
    div[data-key="btn_pizzolato"] button { background: transparent !important; border: none !important; color: transparent !important; height: 45px !important; }
    </style>
    """, unsafe_allow_html=True)

    st.markdown('<div class="contenedor-login">', unsafe_allow_html=True)
    if os.path.exists("assets/login_menfa.png"):
        st.image("assets/login_menfa.png", use_container_width=True)
    else:
        st.info("📌 IPCL MENFA - Control de Acceso")

    u = st.text_input("U", key="u_pizzolato")
    p = st.text_input("P", type="password", key="p_pizzolato")
    
    if st.button("INGRESAR", key="btn_pizzolato", use_container_width=True):
        if u == "admin" and p == "menfa2026":
            st.session_state.ingresado = True  
            st.session_state.rol = "instructor"
            st.rerun()
        elif u == "alumno" and p == "alumno2026":
            st.session_state.ingresado = True  
            st.session_state.rol = "alumno"
            st.rerun()
        else:
            st.error("Credenciales incorrectas")

    st.markdown('</div>', unsafe_allow_html=True)

def verificar_emergencias_remotas():
    if not callable(leer_estado_actual):
        return
    try:
        estado = leer_estado_actual()
        if estado and estado.get("activo"):
            st.markdown("<style> .stApp {background-color: #3e0000 !important;}</style>", unsafe_allow_html=True)
            st.error("🚨 EMG_LNZ OPR")
            st.heading(estado.get('falla', 'Emergencia Remota'))
            st.warning(estado.get('descripcion', 'Atención requerida'))
            
            if 'motor' in st.session_state and hasattr(st.session_state.motor, 'simular_golpe_de_gas'):
                st.session_state.motor.simular_golpe_de_gas()
                
            respuesta = st.text_area("Procedimiento de Maniobra:")
            if st.button("Enviar Respuesta"):
                st.success("Respuesta enviada. Esperando normalización.")
            st.stop()
    except Exception as e:
        st.sidebar.caption(f"Estado Nube: Desconectado ({e})")

# --- PANEL DEL INSTRUCTOR ---
def modulo_instructor_pizzolato():
    st.title("👨‍🏫 Comando Maestro - Menfa 3.0")
    col1, col2 = st.columns(2)
    with col1:
        falla = st.selectbox("Inyectar Falla:", ["Fuga de H2S", "Cavitación", "BSW Alto", "ESD Activada"])
        detalles = st.text_area("Descripción del síntoma:")
        if st.button("🔴 LANZAR EMERGENCIA"):
            if callable(enviar_falla):
                enviar_falla(falla, detalles)
            if 'motor' in st.session_state:
                if falla == "ESD Activada" and hasattr(st.session_state.motor, 'activar_esd'):
                    st.session_state.motor.activar_esd()
                elif hasattr(st.session_state.motor, 'simular_golpe_de_gas'):
                    st.session_state.motor.simular_golpe_de_gas()
            st.toast("Falla enviada e inyectada en el motor")
    with col2:
        if st.button("🟢 NORMALIZAR PLANTA"):
            if callable(resetear_planta):
                resetear_planta()

# --- EJECUCIÓN ---
def principal():
    if not st.session_state.ingresado:
        login()
    else:
        if st.session_state.rol == "instructor":  
            modo = st.sidebar.selectbox("Vista:", ["🖥️ Simulador", "🎮 Control Maestro"])
            if modo == "🎮 Control Maestro":
                modulo_instructor_pizzolato()
            else:
                st.info("Vista de Simulador Activa (Aplicación Principal)")
        else:
            st.info("Vista de Alumno Activa")

if __name__ == "__main__":
    principal()
