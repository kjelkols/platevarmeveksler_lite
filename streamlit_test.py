
import io
import json
import os
from datetime import datetime
from report_pdf import create_pdf_report
import streamlit as st
from plateheatexchanger import PlateHeatExchanger, MoistAir
from ntutools import epsilon_ntu

# --- Prosjektlagring ---
PROJECTS_DIR = "prosjekter"
DEFAULT_PROJECT = {
    "description": "",
    "inputs": {},
}

# --- Hjelpefunksjoner for prosjekt ---

# Ikke bruk safe_filename. Prosjektnavn må være gyldig filnavn (kun bokstaver, tall, _ og -)
def is_valid_project_filename(name):
    import re
    if not name or not name.strip():
        return False, "Prosjektnavn kan ikke være tomt."
    if not re.match(r'^[a-zA-Z0-9_\-]+$', name):
        return False, "Prosjektnavn kan kun inneholde bokstaver, tall, bindestrek og understrek."
    return True, ""


# --- Statusfelt i sidefeltet ---

def set_sidebar_status(msg, type_='info'):
    st.session_state['sidebar_status'] = (msg, type_)

# Sørg for at statusfeltet er initialisert utenfor funksjoner
if 'sidebar_status' not in st.session_state:
    st.session_state['sidebar_status'] = ''

def show_sidebar_status():
    val = st.session_state.get('sidebar_status', ('', 'info'))
    if isinstance(val, tuple) and len(val) == 2:
        msg, type_ = val
    else:
        msg, type_ = '', 'info'
    if msg:
        if type_ == 'success':
            st.sidebar.success(msg)
        elif type_ == 'error':
            st.sidebar.error(msg)
        else:
            st.sidebar.info(msg)

show_sidebar_status()

# --- Prosjektvalg og initialisering ---
def get_project_files():
    if not os.path.exists(PROJECTS_DIR):
        os.makedirs(PROJECTS_DIR)
    return [f for f in os.listdir(PROJECTS_DIR) if f.endswith('.json')]

def list_projects():
    return [os.path.splitext(f)[0] for f in get_project_files()]

def load_project(name):

    filename = os.path.join(PROJECTS_DIR, name + ".json")
    if os.path.exists(filename):
        with open(filename, 'r', encoding='utf-8') as f:
            return json.load(f)
    return None

# --- Prosjektlagring: lagre prosjekt til fil ---
def save_project(project, old_name=None):
    # Finn prosjektnavn fra '__project_name__' hvis mulig, ellers fra old_name
    project_name = project.get("__project_name__")
    if not project_name:
        project_name = old_name
    # Fjern 'name' fra dict hvis den finnes
    if "name" in project:
        del project["name"]
    if not project_name:
        raise ValueError("Kan ikke lagre prosjekt uten prosjektnavn.")
    if old_name and old_name != project_name:
        old_file = os.path.join(PROJECTS_DIR, old_name + ".json")
        if os.path.exists(old_file):
            os.remove(old_file)
    filename = os.path.join(PROJECTS_DIR, project_name + ".json")
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(project, f, ensure_ascii=False, indent=2)

def get_project_by_name(projects, name):
    for p in projects:
        if p.get("__project_name__") == name:
            return p
    return None

def is_valid_project_name(name, existing_names):
    if not name or not name.strip():
        return False, "Prosjektnavn kan ikke være tomt."
    if name in existing_names:
        return False, "Prosjektnavnet finnes allerede."
    return True, ""


# --- Prosjektvalg i sidepanelet ---

# --- Dynamisk scanning av prosjektfiler for dropdown ---
def get_projects_and_names():
    project_files = get_project_files()
    project_names = [os.path.splitext(f)[0] for f in project_files]
    projects = []
    invalid_projects = []
    for fname in project_files:
        try:
            with open(os.path.join(PROJECTS_DIR, fname), 'r', encoding='utf-8') as f:
                data = json.load(f)
                data['__project_filename__'] = fname
                data['__project_name__'] = os.path.splitext(fname)[0]
                projects.append(data)
        except Exception as e:
            invalid_projects.append((fname, str(e)))
    return projects, project_names, invalid_projects

selected_project_name = st.session_state.get('selected_project_name')
projects, project_names, invalid_projects = get_projects_and_names()

if invalid_projects:
    st.sidebar.warning("Følgende prosjektfiler kunne ikke lastes:")
    for fname, err in invalid_projects:
        st.sidebar.caption(f"{fname}: {err}")

if project_names:
    default_index = 0
    if selected_project_name in project_names:
        default_index = project_names.index(selected_project_name)
    selected = st.sidebar.selectbox(
        "Velg prosjekt",
        project_names,
        index=default_index if selected_project_name in project_names else 0,
        key="selected_project_dropdown"
    )
    if selected != selected_project_name:
        st.session_state['selected_project_name'] = selected
        st.rerun()
    # Oppdater prosjekter og navn etter evt. endring
    projects, project_names, _ = get_projects_and_names()
    selected_project = get_project_by_name(projects, selected)
else:
    st.sidebar.info("Ingen prosjekter funnet. Opprett et nytt prosjekt.")
    selected_project = None

# Prosjektnavn og beskrivelse
if selected_project:
    st.sidebar.markdown(f"**Prosjektnavn:** {selected_project['__project_name__']}")
    project_name = selected_project["__project_name__"]
    inputs = selected_project.get("inputs", {})
    project_description = selected_project.get("description", "")
else:
    st.sidebar.markdown("**Prosjektnavn:** <i>Ingen valgt</i>", unsafe_allow_html=True)
    project_name = ""
    inputs = {}
    project_description = ""

st.title("Platevarmeveksler-beregning med Epsilon-NTU")
st.write("Fyll inn inndata og se resultater direkte.")

# --- Inndata ---

st.header("Inndata")




# --- Bruk session_state for synkronisering og automatisk lagring ---
ss = st.session_state
def ss_init(key, value):
    if key not in ss:
        ss[key] = value

ss_init('desc_input', project_description)
ss_init('plate_width_input', inputs.get("plate_width", 1.4))
ss_init('plate_height_input', inputs.get("plate_height", 1.4))
ss_init('gap_input', inputs.get("gap", 0.015))
ss_init('n_plates_input', inputs.get("n_plates", 50))
ss_init('plate_thickness_input', inputs.get("plate_thickness", 0.0005))
ss_init('hot_temp_input', inputs.get("hot_temp", 40.0))
ss_init('hot_rh_input', inputs.get("hot_rh", 0.5))
ss_init('cold_temp_input', inputs.get("cold_temp", 10.0))
ss_init('cold_rh_input', inputs.get("cold_rh", 0.9))
ss_init('velocity_input', inputs.get("velocity", 6.0))

project_description = st.text_area("Beskrivelse", key="desc_input", disabled=not selected_project)
col1, col2 = st.columns(2)
with col1:
    plate_width = st.number_input("Platebredde (m)", min_value=0.1, step=0.01, disabled=not selected_project, key="plate_width_input")
    plate_height = st.number_input("Platehøyde (m)", min_value=0.1, step=0.01, disabled=not selected_project, key="plate_height_input")
    gap = st.number_input("Avstand mellom plater (m)", min_value=0.001, step=0.001, format="%.3f", disabled=not selected_project, key="gap_input")
    n_plates = st.number_input("Antall plater", min_value=2, step=1, disabled=not selected_project, key="n_plates_input")
    plate_thickness = st.number_input("Platetykkelse (m)", min_value=0.0001, step=0.0001, format="%.4f", disabled=not selected_project, key="plate_thickness_input")
with col2:
    hot_temp = st.number_input("Varm luft inn (°C)", step=1.0, disabled=not selected_project, key="hot_temp_input")
    hot_rh = st.slider("Varm luft relativ fuktighet", min_value=0.0, max_value=1.0, step=0.01, disabled=not selected_project, key="hot_rh_input")
    cold_temp = st.number_input("Kald luft inn (°C)", step=1.0, disabled=not selected_project, key="cold_temp_input")
    cold_rh = st.slider("Kald luft relativ fuktighet", min_value=0.0, max_value=1.0, step=0.01, disabled=not selected_project, key="cold_rh_input")
    velocity = st.number_input("Lufthastighet (m/s)", min_value=0.1, step=0.1, disabled=not selected_project, key="velocity_input")

# Sjekk og lagre endringer umiddelbart
if selected_project:
    new_inputs = {
        "plate_width": ss["plate_width_input"],
        "plate_height": ss["plate_height_input"],
        "gap": ss["gap_input"],
        "n_plates": ss["n_plates_input"],
        "plate_thickness": ss["plate_thickness_input"],
        "hot_temp": ss["hot_temp_input"],
        "hot_rh": ss["hot_rh_input"],
        "cold_temp": ss["cold_temp_input"],
        "cold_rh": ss["cold_rh_input"],
        "velocity": ss["velocity_input"]
    }
    if (
        new_inputs != inputs or ss["desc_input"] != selected_project.get("description", "")
    ):
        selected_project["inputs"] = new_inputs
        selected_project["description"] = ss["desc_input"]
    save_project(selected_project, old_name=selected_project["__project_name__"])



# --- Resultatberegning og visning ---

if selected_project:
    # Beregn fysiske størrelser
    hot_air = MoistAir.from_rh(temperature_c=hot_temp, relative_humidity=hot_rh)
    cold_air = MoistAir.from_rh(temperature_c=cold_temp, relative_humidity=cold_rh)
    phe = PlateHeatExchanger(
        plate_width=plate_width,
        plate_height=plate_height,
        gap_between_plates=gap,
        number_of_plates=int(n_plates),
        plate_thickness=plate_thickness
    )
    u_value = phe.calculate_u_value(hot_air, cold_air, velocity)
    ua_value = u_value * phe.total_heat_transfer_area
    hot_mass_flow = phe.calculate_mass_flow_rate(velocity, hot_air.density)
    cold_mass_flow = phe.calculate_mass_flow_rate(velocity, cold_air.density)
    hot_c_rate = hot_mass_flow * hot_air.specific_heat * phe.number_of_channels
    cold_c_rate = cold_mass_flow * cold_air.specific_heat * phe.number_of_channels
    hot_volum_flow = hot_mass_flow / hot_air.density if hot_air.density else 0
    cold_volum_flow = cold_mass_flow / cold_air.density if cold_air.density else 0
    re_hot = phe.calculate_reynolds_number(velocity, hot_air.density, hot_air.dynamic_viscosity)
    re_cold = phe.calculate_reynolds_number(velocity, cold_air.density, cold_air.dynamic_viscosity)
    flow_type_hot = "Turbulent" if re_hot > 2300 else "Laminær"
    flow_type_cold = "Turbulent" if re_cold > 2300 else "Laminær"

    st.header("Beregnede parametre")
    st.write(f"U-verdi: {u_value:.2f} W/m²K")
    st.write(f"UA-verdi: {ua_value:.1f} W/K")
    st.write(f"Varm side massestrøm: {hot_mass_flow*phe.number_of_channels:.2f} kg/s")
    st.write(f"Kald side massestrøm: {cold_mass_flow*phe.number_of_channels:.2f} kg/s")
    st.write(f"Volumstrøm varm side: {hot_volum_flow:.3f} m³/s")
    st.write(f"Volumstrøm kald side: {cold_volum_flow:.3f} m³/s")
    st.write(f"Varmekapasitetsrate varm side: {hot_c_rate:.1f} W/K")
    st.write(f"Varmekapasitetsrate kald side: {cold_c_rate:.1f} W/K")
    st.write(f"Varmeoverføringsareal: {phe.total_heat_transfer_area:.2f} m²")
    st.write(f"Reynolds tall (varm side): {re_hot:.0f} ({flow_type_hot})")
    st.write(f"Reynolds tall (kald side): {re_cold:.0f} ({flow_type_cold})")

    # Hovedresultater (Epsilon-NTU)
    st.header("Hovedresultater (Epsilon-NTU)")
    results = epsilon_ntu(
        hot_in_temperature_c=hot_temp,
        cold_in_temperature_c=cold_temp,
        hot_heatcapacity_rate=hot_c_rate,
        cold_heatcapacity_rate=cold_c_rate,
        ua_value=ua_value,
        flow_configuration='cross-flow'
    )
    # Norsk oversettelse for hovedresultater
    result_labels = {
        "total_heat_transfer_w": "Total varmeoverføring (W)",
        "ntu": "NTU",
        "effectiveness_epsilon": "Effektivitet (epsilon)",
        "temp_hot_out_c": "Varm side ut (°C)",
        "temp_cold_out_c": "Kald side ut (°C)",
        "temp_effectiveness_hot_side": "Temperaturvirkningsgrad varm side",
        "temp_effectiveness_cold_side": "Temperaturvirkningsgrad kald side",
        "heat_capacity_rate_ratio": "Varmekapasitetsrate-forhold (Cr)"
    }
    for key, value in results.items():
        label = result_labels.get(key, key)
        st.write(f"{label}: {value:.2f}" if isinstance(value, float) else f"{label}: {value}")

    # PDF-rapport
    st.subheader("Last ned rapport")
    pdf_bytes = create_pdf_report(
        project_description,
        plate_width,
        plate_height,
        gap,
        n_plates,
        plate_thickness,
        hot_temp,
        hot_rh,
        cold_temp,
        cold_rh,
        velocity,
        u_value,
        ua_value,
        hot_mass_flow,
        cold_mass_flow,
        hot_c_rate,
        cold_c_rate,
        phe,
        hot_volum_flow,
        cold_volum_flow,
        re_hot,
        re_cold,
        flow_type_hot,
        flow_type_cold,
        results,
        result_labels
    )
    st.download_button(
        label="Generer og last ned PDF-rapport",
        data=pdf_bytes,
        file_name="platevarmeveksler_rapport.pdf",
        mime="application/pdf"
    )


# --- Nytt prosjekt ---
if st.sidebar.button("Nytt prosjekt"):
    st.session_state['show_new_project_form'] = True

if st.session_state.get('show_new_project_form', False):
    with st.sidebar.form("nytt_prosjekt_form", clear_on_submit=True):
        new_name = st.text_input("Nytt prosjektnavn")
        new_desc = st.text_area("Beskrivelse")
        submitted = st.form_submit_button("Opprett prosjekt")
        if submitted:
            valid, msg = is_valid_project_filename(new_name)
            if not valid:
                set_sidebar_status(msg, type_='error')
            elif new_name in project_names:
                set_sidebar_status("Prosjektnavnet finnes allerede.", type_='error')
            else:
                # Bruk verdier fra aktivt prosjekt hvis det finnes, ellers default
                if selected_project is not None:
                    new_inputs = dict(selected_project.get("inputs", {}))
                else:
                    new_inputs = dict(DEFAULT_PROJECT["inputs"])
                new_proj = DEFAULT_PROJECT.copy()
                new_proj["description"] = new_desc
                new_proj["inputs"] = new_inputs
                new_proj["__project_name__"] = new_name
                # Lagre aktivt prosjekt før bytte
                if selected_project is not None:
                    old_name = selected_project["__project_name__"]
                    selected_project["description"] = project_description
                    selected_project["inputs"] = {
                        "plate_width": plate_width,
                        "plate_height": plate_height,
                        "gap": gap,
                        "n_plates": n_plates,
                        "plate_thickness": plate_thickness,
                        "hot_temp": hot_temp,
                        "hot_rh": hot_rh,
                        "cold_temp": cold_temp,
                        "cold_rh": cold_rh,
                        "velocity": velocity
                    }
                    save_project(selected_project, old_name=old_name)
                # Lagre med nytt filnavn
                save_project(new_proj, old_name=None)
                set_sidebar_status("Prosjekt opprettet!", type_='success')
                st.session_state['selected_project_name'] = new_name
                st.session_state['show_new_project_form'] = False
                st.rerun()
