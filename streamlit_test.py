import io
from xhtml2pdf import pisa
import streamlit as st
from plateheatexchanger import PlateHeatExchanger, MoistAir
from ntutools import epsilon_ntu

st.title("Platevarmeveksler-beregning med Epsilon-NTU")
st.write("Fyll inn inndata og se resultater direkte.")

# --- Inndata ---
st.header("Inndata")
col1, col2 = st.columns(2)

with col1:
    plate_width = st.number_input("Platebredde (m)", value=1.4, min_value=0.1, step=0.01)
    plate_height = st.number_input("Platehøyde (m)", value=1.4, min_value=0.1, step=0.01)
    gap = st.number_input("Avstand mellom plater (m)", value=0.015, min_value=0.001, step=0.001, format="%.3f")
    n_plates = st.number_input("Antall plater", value=50, min_value=2, step=1)
    plate_thickness = st.number_input("Platetykkelse (m)", value=0.0005, min_value=0.0001, step=0.0001, format="%.4f")

with col2:
    hot_temp = st.number_input("Varm luft inn (°C)", value=40.0, step=1.0)
    hot_rh = st.slider("Varm luft relativ fuktighet", min_value=0.0, max_value=1.0, value=0.5, step=0.01)
    cold_temp = st.number_input("Kald luft inn (°C)", value=10.0, step=1.0)
    cold_rh = st.slider("Kald luft relativ fuktighet", min_value=0.0, max_value=1.0, value=0.9, step=0.01)
    velocity = st.number_input("Lufthastighet (m/s)", value=6.0, min_value=0.1, step=0.1)

# --- Beregning ---
phe = PlateHeatExchanger(
    plate_width=plate_width,
    plate_height=plate_height,
    gap_between_plates=gap,
    number_of_plates=int(n_plates),
    plate_thickness=plate_thickness
)
hot_air = MoistAir.from_rh(temperature_c=hot_temp, relative_humidity=hot_rh)
cold_air = MoistAir.from_rh(temperature_c=cold_temp, relative_humidity=cold_rh)

u_value = phe.calculate_u_value(hot_air, cold_air, velocity)
hot_mass_flow = phe.calculate_mass_flow_rate(velocity, hot_air.density)
cold_mass_flow = phe.calculate_mass_flow_rate(velocity, cold_air.density)
hot_c_rate = hot_mass_flow * hot_air.specific_heat * phe.number_of_channels
cold_c_rate = cold_mass_flow * cold_air.specific_heat * phe.number_of_channels
ua_value = u_value * phe.total_heat_transfer_area

# Volumstrømmer (m³/s)
hot_volum_flow = (hot_mass_flow * phe.number_of_channels / hot_air.density) if hot_air.density != 0 else 0
cold_volum_flow = (cold_mass_flow * phe.number_of_channels / cold_air.density) if cold_air.density != 0 else 0


# Volumstrømmer (m³/s)
hot_volum_flow = (hot_mass_flow * phe.number_of_channels / hot_air.density) if hot_air.density != 0 else 0
cold_volum_flow = (cold_mass_flow * phe.number_of_channels / cold_air.density) if cold_air.density != 0 else 0

# Reynolds-tall og strømningstype
re_hot = phe.calculate_reynolds_number(velocity, hot_air.density, hot_air.dynamic_viscosity)
re_cold = phe.calculate_reynolds_number(velocity, cold_air.density, cold_air.dynamic_viscosity)
flow_type_hot = "Turbulent" if re_hot > 2300 else "Laminær"
flow_type_cold = "Turbulent" if re_cold > 2300 else "Laminær"

results = epsilon_ntu(
    hot_in_temperature_c=hot_temp,
    cold_in_temperature_c=cold_temp,
    hot_heatcapacity_rate=hot_c_rate,
    cold_heatcapacity_rate=cold_c_rate,
    ua_value=ua_value,
    flow_configuration='cross-flow'
)

# --- Visning av resultater ---
st.header("Beregnete parametre")
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

st.header("Hovedresultater (Epsilon-NTU)")

# --- PDF-rapport med xhtml2pdf ---

def create_pdf_report():
    html = f"""
    <h2>Platevarmeveksler-beregning</h2>
    <h3>Inndata</h3>
    <ul>
        <li>Platebredde: {plate_width} m</li>
        <li>Platehøyde: {plate_height} m</li>
        <li>Avstand mellom plater: {gap} m</li>
        <li>Antall plater: {n_plates}</li>
        <li>Platetykkelse: {plate_thickness} m</li>
        <li>Varm luft inn: {hot_temp} °C, {hot_rh*100:.0f}% RF</li>
        <li>Kald luft inn: {cold_temp} °C, {cold_rh*100:.0f}% RF</li>
        <li>Lufthastighet: {velocity} m/s</li>
    </ul>
    <h3>Beregnete parametre</h3>
    <ul>
        <li>U-verdi: {u_value:.2f} W/m²K</li>
        <li>UA-verdi: {ua_value:.1f} W/K</li>
        <li>Varm side massestrøm: {hot_mass_flow*phe.number_of_channels:.2f} kg/s</li>
        <li>Kald side massestrøm: {cold_mass_flow*phe.number_of_channels:.2f} kg/s</li>
        <li>Varmekapasitetsrate varm side: {hot_c_rate:.1f} W/K</li>
        <li>Varmekapasitetsrate kald side: {cold_c_rate:.1f} W/K</li>
        <li>Varmeoverføringsareal: {phe.total_heat_transfer_area:.2f} m²</li>
        <li>Volumstrøm varm side: {hot_volum_flow:.3f} m³/s</li>
        <li>Volumstrøm kald side: {cold_volum_flow:.3f} m³/s</li>
        <li>Reynolds tall (varm side): {re_hot:.0f} ({flow_type_hot})</li>
        <li>Reynolds tall (kald side): {re_cold:.0f} ({flow_type_cold})</li>        
    </ul>
    <h3>Hovedresultater (Epsilon-NTU)</h3>
    <ul>
    """
    # Bruk norske etiketter for hovedresultater
    for key, value in results.items():
        label = result_labels.get(key, key)
        html += f"<li>{label}: {value:.2f}</li>" if isinstance(value, float) else f"<li>{label}: {value}</li>"
    html += "</ul>"
    pdf_buffer = io.BytesIO()
    pisa.CreatePDF(io.StringIO(html), dest=pdf_buffer)
    return pdf_buffer.getvalue()


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


st.subheader("Last ned rapport")
pdf_bytes = create_pdf_report()
st.download_button(
    label="Generer og last ned PDF-rapport",
    data=pdf_bytes,
    file_name="platevarmeveksler_rapport.pdf",
    mime="application/pdf"
)
