import io
from xhtml2pdf import pisa

def create_pdf_report(
    description,
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
):
    html = f"""
    <h2>Platevarmeveksler-beregning</h2>
    <p><b>Beskrivelse:</b> {description}</p>
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
    <h3>Beregnede parametre</h3>
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
    for key, value in results.items():
        label = result_labels.get(key, key)
        html += f"<li>{label}: {value:.2f}</li>" if isinstance(value, float) else f"<li>{label}: {value}</li>"
    html += "</ul>"
    pdf_buffer = io.BytesIO()
    pisa.CreatePDF(io.StringIO(html), dest=pdf_buffer)
    return pdf_buffer.getvalue()
