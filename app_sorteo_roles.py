import streamlit as st
import random
import pandas as pd
import io

st.set_page_config(
    page_title="Sorteo de Roles - Práctica UT1 TJK",
    page_icon="🎲",
    layout="wide"
)

st.title("🎲 Aplicación de Sorteo de Roles y Tarjetas para Usuarios Ficticios")
st.caption("Módulo: Técnicas de Tiempo Libre (TJK) — 2º ACO | Evaluación Práctica de la UT 1 (RA 1)")

st.markdown("""
Esta aplicación realiza el **sorteo automatizado y equilibrado** de las tarjetas de rol para los **12 usuarios ficticios** en cada una de las 4 rotaciones de la práctica simulada.
""")

st.sidebar.header("⚙️ Configuración del Sorteo")

seed_input = st.sidebar.number_input("Semilla Aleatoria (Seed)", value=42, step=1, help="Cambia este número para generar un nuevo sorteo distinto.")

default_names = [
    "Álvarez Gómez, Laura", "Barreto Pérez, Carlos", "Cabrera Díaz, Elena", "Delgado Luis, David",
    "Expósito Hernández, Sofía", "Fernández Rodríguez, Mateo", "González Martín, Lucía", "Hernández Afonso, Pablo",
    "Jiménez Mesa, Alba", "León Santana, Hugo", "Morera Castro, Paula", "Núñez Reyes, Adrián",
    "Ojeda Ramos, Marta", "Padrón Vega, Diego", "Quintero Suárez, Valeria", "Rios Lorenzo, Gabriel"
]

with st.sidebar.expander("👥 Lista de los 16 Alumnos/as", expanded=False):
    students = []
    for i in range(16):
        name = st.text_input(f"Alumno/a {i+1}", value=default_names[i], key=f"st_{i}")
        students.append(name)

# Define Groups
groups = {
    "Equipo 1": students[0:4],
    "Equipo 2": students[4:8],
    "Equipo 3": students[8:12],
    "Equipo 4": students[12:16]
}

roles_info = {
    "Tarjeta A": {
        "nombre": "Personas Mayores (65+ años)",
        "perfil": "Movilidad reducida (bastón/silla), pérdida auditiva leve. Requiere ritmo pausado, lenguaje claro y acogida afectuosa.",
        "badge": "👴 Mayores"
    },
    "Tarjeta B": {
        "nombre": "Jóvenes con Adicción Digital / Apatía (14-16 años)",
        "perfil": "Uso constante del smartphone, impaciencia y rechazo inicial. Requiere retos dinámicos y enganche activo.",
        "badge": "📱 Jóvenes"
    },
    "Tarjeta C": {
        "nombre": "Infancia con Diversidad Intelectual / Atención Dispersa (8-11 años)",
        "perfil": "Atención dispersa, energía alta y dificultad con normas complejas. Requiere pictogramas, apoyos gestuales y normas sencillas.",
        "badge": "🧩 Infancia"
    },
    "Tarjeta D": {
        "nombre": "Adultos en Programa de Respiro Familiar (Cuidadores)",
        "perfil": "Alto nivel de estrés acumulado y sobrecarga emocional. Requiere espacio seguro, distendido y orientación al bienestar.",
        "badge": "🌿 Respiro"
    }
}

random.seed(seed_input)

# Perform draw logic
draw_data = []

for rot_num in range(1, 5):
    animator_group = f"Equipo {rot_num}"
    
    # Pool of 12 user cards (3 of each type)
    card_pool = ["Tarjeta A"] * 3 + ["Tarjeta B"] * 3 + ["Tarjeta C"] * 3 + ["Tarjeta D"] * 3
    random.shuffle(card_pool)
    
    card_idx = 0
    for grp_name, grp_mems in groups.items():
        if grp_name == animator_group:
            for st_name in grp_mems:
                draw_data.append({
                    "Rotación": f"Rotación {rot_num}",
                    "Equipo Animador": animator_group,
                    "Alumno/a": st_name,
                    "Equipo Origen": grp_name,
                    "Rol Actividad": "DINAMIZADOR/A",
                    "Tarjeta Código": "-",
                    "Perfil Asignado": "Equipo Evaluado de Animación",
                    "Pautas Técnicas": "Gestión de la estación, dinamización, accesibilidad y seguridad"
                })
        else:
            for st_name in grp_mems:
                assigned_card = card_pool[card_idx]
                card_idx += 1
                draw_data.append({
                    "Rotación": f"Rotación {rot_num}",
                    "Equipo Animador": animator_group,
                    "Alumno/a": st_name,
                    "Equipo Origen": grp_name,
                    "Rol Actividad": "USUARIO FICTICIO",
                    "Tarjeta Código": assigned_card,
                    "Perfil Asignado": roles_info[assigned_card]["nombre"],
                    "Pautas Técnicas": roles_info[assigned_card]["perfil"]
                })

df_draw = pd.DataFrame(draw_data)

# Layout Tabs
tab1, tab2, tab3 = st.tabs(["📋 Sorteo por Rotaciones", "👤 Agenda por Alumno/a", "🎴 Fichas de las Tarjetas de Rol"])

with tab1:
    st.subheader("📋 Distribución de Roles por Rotación de la Práctica (30 min cada una)")
    
    for r in [1, 2, 3, 4]:
        rot_label = f"Rotación {r}"
        df_rot = df_draw[df_draw["Rotación"] == rot_label]
        
        anim_group_name = f"Equipo {r}"
        
        with st.expander(f"📌 **{rot_label}** — Dinamiza: **{anim_group_name}** (12 Usuarios Ficticios)", expanded=(r==1)):
            st.dataframe(
                df_rot[["Alumno/a", "Equipo Origen", "Rol Actividad", "Tarjeta Código", "Perfil Asignado", "Pautas Técnicas"]],
                use_container_width=True,
                hide_index=True
            )

with tab2:
    st.subheader("👤 Plan de Trabajo Individual por Alumno/a (Las 4 Rotaciones)")
    
    selected_student = st.selectbox("Selecciona un/a alumno/a para ver sus roles:", students)
    
    df_st = df_draw[df_draw["Alumno/a"] == selected_student]
    
    st.info(f"**Agenda de Prácticas para:** {selected_student} ({df_st['Equipo Origen'].iloc[0]})")
    
    col1, col2, col3, col4 = st.columns(4)
    cols = [col1, col2, col3, col4]
    
    for i, (_, row) in enumerate(df_st.iterrows()):
        with cols[i]:
            st.markdown(f"#### {row['Rotación']}")
            if row["Rol Actividad"] == "DINAMIZADOR/A":
                st.success("🟢 **DINAMIZADOR/A**")
                st.write("Te evalúa el profesorado durante la conducción.")
            else:
                st.warning(f"🎭 **{row['Tarjeta Código']}**")
                st.write(f"**{row['Perfil Asignado']}**")
                st.caption(row["Pautas Técnicas"])

with tab3:
    st.subheader("🎴 Descripción Completa de las Tarjetas de Rol")
    
    for code, info in roles_info.items():
        st.markdown(f"### {code}: {info['nombre']} {info['badge']}")
        st.write(f"**Pautas de interpretación:** {info['perfil']}")
        st.divider()

st.sidebar.markdown("---")
st.sidebar.success("✅ Sorteo asignado correctamente con garantía de 3 tarjetas de cada tipo por rotación.")
