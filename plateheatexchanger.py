import math
from dataclasses import dataclass
from typing import Dict

# Konstanter for luft og vann
# R_DRY_AIR: Gasskonstant for tørr luft, 287.058 J/(kg·K) (se f.eks. ASHRAE Fundamentals 2017, kap. 1)
R_DRY_AIR = 287.058  # J/(kg·K)
# R_WATER_VAPOR: Gasskonstant for vanndamp, 461.495 J/(kg·K) (ASHRAE Fundamentals 2017, kap. 1)
R_WATER_VAPOR = 461.495  # J/(kg·K)
# CP_DRY_AIR: Spesifikk varmekapasitet for tørr luft, 1006 J/(kg·K) (ASHRAE Fundamentals 2017, tabell 1)
CP_DRY_AIR = 1006.0  # J/(kg·K)
# CP_WATER_VAPOR: Spesifikk varmekapasitet for vanndamp, 1860 J/(kg·K) (ASHRAE Fundamentals 2017, tabell 1)
CP_WATER_VAPOR = 1860.0  # J/(kg·K)
# LATENT_HEAT: Fordampningsvarme for vann ved 0°C, 2 501 000 J/kg (ASHRAE Fundamentals 2017, tabell 2)
LATENT_HEAT = 2501000.0  # J/kg (fordampningsvarme ved 0°C)

def get_saturation_pressure_pa(temp_c: float) -> float:
    """Beregn metningstrykk for vanndamp med Arden Buck-ligningen."""
    if temp_c > 0:
        return 611.21 * math.exp((18.678 - temp_c/234.5) * (temp_c/(257.14 + temp_c)))
    else:
        return 611.15 * math.exp((23.036 - temp_c/333.7) * (temp_c/(279.82 + temp_c)))

def get_humidity_ratio(temp_c: float, pressure_pa: float, relative_humidity: float) -> float:
    """Beregn fuktighetsratio (kg vann / kg tørr luft)."""
    p_sat = get_saturation_pressure_pa(temp_c)
    p_vapor = relative_humidity * p_sat
    return 0.622 * p_vapor / (pressure_pa - p_vapor)

def get_air_viscosity(temp_c: float) -> float:
    """Beregn dynamisk viskositet for luft ved gitt temperatur."""
    T = temp_c + 273.15
    return 1.458e-6 * T**1.5 / (T + 110.4)

def get_air_thermal_conductivity(temp_c: float) -> float:
    """Beregn termisk ledningsevne for luft."""
    T = temp_c + 273.15
    return 0.0241 + 6.8e-5 * temp_c

def get_air_density(temp_c: float, pressure_pa: float, humidity_ratio: float) -> float:
    """Beregn tetthet for fuktig luft."""
    T = temp_c + 273.15
    return pressure_pa / (R_DRY_AIR * T * (1 + 0.608 * humidity_ratio))

def get_specific_heat(humidity_ratio: float) -> float:
    """Beregn spesifikk varmekapasitet for fuktig luft."""
    return CP_DRY_AIR + humidity_ratio * CP_WATER_VAPOR

@dataclass
class MoistAir:
    """Klasse for fuktig luft med termodynamiske egenskaper."""
    temperature_c: float
    humidity_ratio: float
    pressure_pa: float = 101325.0

    @classmethod
    def from_rh(cls, temperature_c: float, relative_humidity: float, pressure_pa: float = 101325.0):
        """Alternativ konstruktør fra relativ fuktighet."""
        hr = get_humidity_ratio(temperature_c, pressure_pa, relative_humidity)
        return cls(temperature_c, hr, pressure_pa)

    @property
    def density(self) -> float:
        return get_air_density(self.temperature_c, self.pressure_pa, self.humidity_ratio)

    @property
    def dynamic_viscosity(self) -> float:
        return get_air_viscosity(self.temperature_c)

    @property
    def thermal_conductivity(self) -> float:
        return get_air_thermal_conductivity(self.temperature_c)

    @property
    def specific_heat(self) -> float:
        return get_specific_heat(self.humidity_ratio)

    @property
    def prandtl_number(self) -> float:
        mu = self.dynamic_viscosity
        cp = self.specific_heat
        k = self.thermal_conductivity
        return (cp * mu) / k if k > 0 else 0.7

@dataclass
class PlateHeatExchanger:
    """Klasse for platevarmeveksler beregninger."""
    
    # Geometri
    plate_width: float = 1.4  # m
    plate_height: float = 1.4  # m
    gap_between_plates: float = 0.015  # m
    number_of_plates: int = 50
    plate_thickness: float = 0.0005  # m (0.5 mm aluminium)
    
    # Materialegenskaper
    plate_thermal_conductivity: float = 237.0  # W/m·K (aluminium)
    surface_roughness: float = 1.5e-6  # m (typisk for aluminium)

    def __post_init__(self):
        self.calculate_geometry()

    def calculate_geometry(self):
        """Beregn geometriske parametre."""
        self.number_of_channels = self.number_of_plates - 1
        self.flow_area_per_channel = self.gap_between_plates * self.plate_width
        self.total_heat_transfer_area = (self.number_of_plates - 2) * 2 * self.plate_width * self.plate_height
        self.hydraulic_diameter = 2 * self.gap_between_plates

    def calculate_reynolds_number(self, velocity: float, density: float, viscosity: float) -> float:
        """Beregn Reynolds tall."""
        return (density * velocity * self.hydraulic_diameter) / viscosity

    def calculate_friction_factor(self, re: float) -> float:
        """Beregn friksjonsfaktor for platekanaler."""
        if re < 2300:
            # Laminær strømning
            return 96.0 / re
        else:
            # Turbulent strømning - Haaland's equation for ruhet
            rel_roughness = self.surface_roughness / self.hydraulic_diameter
            return (-1.8 * math.log10((rel_roughness/3.7)**1.11 + 6.9/re))**-2

    def calculate_nusselt_number(self, re: float, pr: float) -> float:
        """Beregn Nusselt tall for platevarmeveksler."""
        if re < 2300:
            # Laminær strømning - korrelasjon for utviklet strømning
            return 7.54
        else:
            # Turbulent strømning - Gnielinski korrelasjon
            f = self.calculate_friction_factor(re)
            return (f/8) * (re - 1000) * pr / (1 + 12.7 * math.sqrt(f/8) * (pr**(2/3) - 1))

    def calculate_convection_coefficient(self, air_properties: Dict[str, float], velocity: float) -> float:
        """Beregn konveksjonskoeffisient."""
        re = self.calculate_reynolds_number(velocity, air_properties['density'], air_properties['viscosity'])
        pr = air_properties['prandtl']
        nu = self.calculate_nusselt_number(re, pr)
        return (nu * air_properties['thermal_conductivity']) / self.hydraulic_diameter

    def calculate_u_value(self, hot_air: MoistAir, cold_air: MoistAir, velocity: float) -> float:
        """Beregn total U-verdi."""
        hot_props = {
            'density': hot_air.density,
            'viscosity': hot_air.dynamic_viscosity,
            'thermal_conductivity': hot_air.thermal_conductivity,
            'prandtl': hot_air.prandtl_number
        }
        
        cold_props = {
            'density': cold_air.density,
            'viscosity': cold_air.dynamic_viscosity,
            'thermal_conductivity': cold_air.thermal_conductivity,
            'prandtl': cold_air.prandtl_number
        }

        h_hot = self.calculate_convection_coefficient(hot_props, velocity)
        h_cold = self.calculate_convection_coefficient(cold_props, velocity)
        
        # Termisk motstand for plate
        r_plate = self.plate_thickness / self.plate_thermal_conductivity
        
        # Total termisk motstand
        r_total = 1/h_hot + r_plate + 1/h_cold
        
        return 1 / r_total

    def calculate_mass_flow_rate(self, velocity: float, density: float) -> float:
        """Beregn massestrøm per kanal."""
        return density * velocity * self.flow_area_per_channel

def main():
    """Hovedberegning for platevarmeveksler."""
    print("PLATEVARMVEKSLER BEREGNING")
    print("=" * 50)
    
    # Definer inngående forhold
    hot_air_in = MoistAir.from_rh(temperature_c=40, relative_humidity=0.5)
    cold_air_in = MoistAir.from_rh(temperature_c=10, relative_humidity=0.9)
    velocity = 6.0  # m/s
    
    # Opprett varmeveksler
    phe = PlateHeatExchanger()
    
    # Beregn U-verdi
    u_value = phe.calculate_u_value(hot_air_in, cold_air_in, velocity)
    
    # Beregn massestrømmer
    hot_mass_flow = phe.calculate_mass_flow_rate(velocity, hot_air_in.density)
    cold_mass_flow = phe.calculate_mass_flow_rate(velocity, cold_air_in.density)
    
    # Beregn varmekapasitetsrater
    hot_c_rate = hot_mass_flow * hot_air_in.specific_heat * phe.number_of_channels
    cold_c_rate = cold_mass_flow * cold_air_in.specific_heat * phe.number_of_channels
    
    # Beregn UA-verdi
    ua_value = u_value * phe.total_heat_transfer_area
    
    # Beregn Reynolds tall
    re_hot = phe.calculate_reynolds_number(velocity, hot_air_in.density, hot_air_in.dynamic_viscosity)
    re_cold = phe.calculate_reynolds_number(velocity, cold_air_in.density, cold_air_in.dynamic_viscosity)
    
    # Vis resultater
    print(f"\nGEOMETRI:")
    print(f"Antall plater: {phe.number_of_plates}")
    print(f"Antall kanaler: {phe.number_of_channels}")
    print(f"Kanalhøyde: {phe.gap_between_plates*1000:.1f} mm")
    print(f"Hydraulisk diameter: {phe.hydraulic_diameter*1000:.1f} mm")
    print(f"Varmeoverføringsareal: {phe.total_heat_transfer_area:.1f} m²")
    
    print(f"\nINNGÅENDE FORHOLD:")
    print(f"Varm luft: {hot_air_in.temperature_c:.1f}°C, 50% RF")
    print(f"Kald luft: {cold_air_in.temperature_c:.1f}°C, 90% RF")
    print(f"Hastighet: {velocity:.1f} m/s")
    
    print(f"\nLUFTPARAMETRE - VARM SIDE:")
    print(f"Tetthet: {hot_air_in.density:.3f} kg/m³")
    print(f"Viskositet: {hot_air_in.dynamic_viscosity:.2e} Pa·s")
    print(f"Termisk konduktivitet: {hot_air_in.thermal_conductivity:.4f} W/m·K")
    print(f"Prandtl tall: {hot_air_in.prandtl_number:.3f}")
    
    print(f"\nLUFTPARAMETRE - KALD SIDE:")
    print(f"Tetthet: {cold_air_in.density:.3f} kg/m³")
    print(f"Viskositet: {cold_air_in.dynamic_viscosity:.2e} Pa·s")
    print(f"Termisk konduktivitet: {cold_air_in.thermal_conductivity:.4f} W/m·K")
    print(f"Prandtl tall: {cold_air_in.prandtl_number:.3f}")
    
    print(f"\nRESULTATER:")
    print(f"U-verdi: {u_value:.2f} W/m²K")
    print(f"UA-verdi: {ua_value:.0f} W/K")
    print(f"Reynolds tall (varm side): {re_hot:.0f}")
    print(f"Reynolds tall (kald side): {re_cold:.0f}")
    print(f"Strømningstype: {'Turbulent' if re_hot > 2300 else 'Laminær'}")
    print(f"Massestrøm totalt: {hot_mass_flow * phe.number_of_channels:.2f} kg/s")
    print(f"Varmekapasitetsrate: {hot_c_rate:.0f} W/K")

if __name__ == "__main__":
    main()