from math import exp


def _epsilon_counterflow(ntu: float, c_ratio: float) -> float:
    """Effektivitet for motstrøms varmeveksler."""
    if c_ratio == 0:  # Spesialtilfelle, f.eks. kondensator
        epsilon = 1 - exp(-ntu)
    else:
        numerator = 1 - exp(-ntu * (1 - c_ratio))
        denominator = 1 - c_ratio * exp(-ntu * (1 - c_ratio))
        epsilon = numerator / denominator if denominator != 0 else 0
    return max(0.0, min(1.0, epsilon))


def _epsilon_crossflow(ntu: float, c_ratio: float) -> float:
    """Effektivitet for krysstrøms varmeveksler (unmixed/unmixed)."""
    if c_ratio == 0:
        c_ratio = 1e-9  # Unngå divisjon med null
    
    # Incropera/DeWitt-formel for unmixed/unmixed cross-flow
    term1 = (1 / c_ratio) * (ntu**0.22)
    term2 = exp(-c_ratio * (ntu**0.78))
    epsilon = 1 - exp(term1 * (term2 - 1))
    return max(0.0, min(1.0, epsilon))


def epsilon_ntu(
    hot_in_temperature_c: float,
    cold_in_temperature_c: float,
    hot_heatcapacity_rate: float,
    cold_heatcapacity_rate: float,
    ua_value: float,
    flow_configuration: str
) -> dict:
    """
    Beregner ytelsen til varmeveksleren med Epsilon-NTU-metoden.
    Returnerer en ordbok med ytelsesindikatorer.
    """

    # 1. Finn C_min, C_max og varmekapasitetsratio (Cr)
    c_min = min(hot_heatcapacity_rate, cold_heatcapacity_rate)
    c_max = max(hot_heatcapacity_rate, cold_heatcapacity_rate)
    c_ratio = c_min / c_max if c_max != 0 else 0

    # 2. Beregn NTU (Number of Transfer Units)
    ntu = ua_value / c_min if c_min != 0 else 0

    # 3. Beregn effektivitet (epsilon, ε) basert på konfigurasjon
    if flow_configuration == 'counter-flow':
        epsilon = _epsilon_counterflow(ntu, c_ratio)
    elif flow_configuration == 'cross-flow':
        epsilon = _epsilon_crossflow(ntu, c_ratio)
    else:
        raise ValueError(f"Ukjent flow_configuration: {flow_configuration}")

    # 4. Beregn faktisk overført varme (Q)
    q_max = c_min * (hot_in_temperature_c - cold_in_temperature_c)
    q_actual = epsilon * q_max

    # 5. Beregn utløpstemperaturer
    hot_out_temperature_c = hot_in_temperature_c - (
        q_actual / hot_heatcapacity_rate if hot_heatcapacity_rate != 0 else 0
    )
    cold_out_temperature_c = cold_in_temperature_c + (
        q_actual / cold_heatcapacity_rate if cold_heatcapacity_rate != 0 else 0
    )

    # 6. Beregn temperaturvirkningsgrad
    temp_diff_in = hot_in_temperature_c - cold_in_temperature_c
    temp_effectiveness_hot = (
        (hot_in_temperature_c - hot_out_temperature_c) / temp_diff_in
        if temp_diff_in != 0 else 0
    )
    temp_effectiveness_cold = (
        (cold_out_temperature_c - cold_in_temperature_c) / temp_diff_in
        if temp_diff_in != 0 else 0
    )

    return {
        "total_heat_transfer_w": q_actual,
        "ntu": ntu,
        "effectiveness_epsilon": epsilon,
        "temp_hot_out_c": hot_out_temperature_c,
        "temp_cold_out_c": cold_out_temperature_c,
        "temp_effectiveness_hot_side": temp_effectiveness_hot,
        "temp_effectiveness_cold_side": temp_effectiveness_cold,
        "heat_capacity_rate_ratio": c_ratio
    }


if __name__ == "__main__":
    # Eksempelbruk
    hot_in_temp = 30   # °C
    cold_in_temp = 10  # °C
    hot_c_rate = 4500   # W/K
    cold_c_rate = 4500  # W/K
    ua = 500            # W/K
    flow_config = 'cross-flow'  # eller 'counter-flow'

    results = epsilon_ntu(
        hot_in_temperature_c=hot_in_temp,
        cold_in_temperature_c=cold_in_temp,
        hot_heatcapacity_rate=hot_c_rate,
        cold_heatcapacity_rate=cold_c_rate,
        ua_value=ua,
        flow_configuration=flow_config
    )

    for key, value in results.items():
        print(f"{key}: {value:.2f}")
