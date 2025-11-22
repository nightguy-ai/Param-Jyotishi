# src/tools.py
from skyfield.api import load
from skyfield import almanac
import datetime
import streamlit as st

# --- CONSTANTS ---
ZODIAC_SIGNS = [
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"
]

NAKSHATRAS = [
    "Ashwini", "Bharani", "Krittika", "Rohini", "Mrigashira", "Ardra", "Punarvasu", "Pushya", "Ashlesha",
    "Magha", "Purva Phalguni", "Uttara Phalguni", "Hasta", "Chitra", "Swati", "Vishakha", "Anuradha", "Jyeshtha",
    "Mula", "Purva Ashadha", "Uttara Ashadha", "Shravana", "Dhanishta", "Shatabhisha", "Purva Bhadrapada", "Uttara Bhadrapada", "Revati"
]

DASHA_SYSTEM = [
    ("Ketu", 7), ("Venus", 20), ("Sun", 6), ("Moon", 10), ("Mars", 7),
    ("Rahu", 18), ("Jupiter", 16), ("Saturn", 19), ("Mercury", 17)
]

# --- VEDIC MATH HELPERS ---

def get_lahiri_ayanamsa(date_obj):
    """Calculates approximate Lahiri Ayanamsa."""
    ref_year = 2000
    ref_ayanamsa = 23.86
    diff_years = date_obj.year - ref_year
    shift = diff_years * (50.29 / 3600)
    return float(ref_ayanamsa + shift) # Force float

def tropical_to_sidereal(lon, ayanamsa):
    """Converts Western longitude to Vedic Sidereal longitude."""
    sidereal = (lon - ayanamsa) % 360
    return float(sidereal) # Force float

def decimal_to_dms(deg_float):
    d = int(deg_float)
    m = int((deg_float - d) * 60)
    return f"{d}° {m}'"

def get_nakshatra(lon):
    unit = 360 / 27
    idx = int(lon / unit)
    name = NAKSHATRAS[idx]
    rem = lon - (idx * unit)
    pada = int(rem / (unit / 4)) + 1
    return name, int(pada), int(idx)

def calculate_dasha(moon_lon, nak_idx):
    unit = 360 / 27
    traversed = moon_lon - (nak_idx * unit)
    remaining = unit - traversed
    percent_left = remaining / unit
    lord_idx = nak_idx % 9
    lord_name, duration = DASHA_SYSTEM[lord_idx]
    balance = duration * percent_left
    return lord_name, float(round(balance, 1)) # Force float

def is_sandhi(lon):
    pos = lon % 30
    # THE FIX IS HERE: explicit bool() conversion
    return bool(pos < 1 or pos > 29)

# --- CORE TOOLS ---

@st.cache_resource
def load_skyfield_data():
    return load('de421.bsp')

def calculate_vedic_chart(date: str, time: str, location: str):
    """
    Calculates Vedic Chart using Skyfield.
    """
    print(f"\n[TOOL] Calculating (Skyfield)... Date: {date} Time: {time}")

    eph = load_skyfield_data()
    earth = eph['earth']

    # Mock Location for robustness (New Delhi)
    lat, lon_geo = 28.61, 77.20

    try:
        # Robust Time Parsing
        dt_str = f"{date} {time}".strip()
        # Clean up common user inputs like "AM" vs "am"
        dt_str = dt_str.replace("am", "AM").replace("pm", "PM")

        try:
            dt_obj = datetime.datetime.strptime(dt_str, "%Y-%m-%d %H:%M")
        except ValueError:
            # Try 12-hour format
            dt_obj = datetime.datetime.strptime(dt_str, "%Y-%m-%d %I:%M %p")

        ts = load.timescale()
        # Approx UTC conversion (Simple offset for demo)
        t = ts.utc(dt_obj.year, dt_obj.month, dt_obj.day, dt_obj.hour, dt_obj.minute)

        ayanamsa = get_lahiri_ayanamsa(dt_obj)

        # --- MOON ---
        moon_astrometric = earth.at(t).observe(eph['moon'])
        _, moon_lon_trop, _ = moon_astrometric.apparent().ecliptic_latlon()
        moon_sidereal = tropical_to_sidereal(moon_lon_trop.degrees, ayanamsa)

        moon_sign_idx = int(moon_sidereal / 30)
        moon_sign = ZODIAC_SIGNS[moon_sign_idx]
        nak_name, pada, nak_idx = get_nakshatra(moon_sidereal)
        dasha_lord, balance = calculate_dasha(moon_sidereal, nak_idx)

        # --- ASCENDANT (Approximation) ---
        sun_astrometric = earth.at(t).observe(eph['sun'])
        _, sun_lon_trop, _ = sun_astrometric.apparent().ecliptic_latlon()
        sun_sidereal = tropical_to_sidereal(sun_lon_trop.degrees, ayanamsa)

        sunrise_approx_hour = 6
        hours_since_sunrise = (dt_obj.hour - sunrise_approx_hour)
        signs_passed = int(hours_since_sunrise / 2)
        sun_sign_idx = int(sun_sidereal / 30)
        asc_idx = (sun_sign_idx + signs_passed) % 12
        asc_sign = ZODIAC_SIGNS[asc_idx]

        # --- TRANSIT DATA FOR ANALYSIS ---
        # Fetch current transits internally for the agent to use
        current_transits = get_current_transits()

        return {
            "status": "success",
            "lagna": {
                "sign": str(asc_sign),
                "is_sandhi": False # Default safe value for approx
            },
            "moon": {
                "sign": str(moon_sign),
                "nakshatra": str(nak_name),
                "pada": int(pada),
                "is_sandhi": is_sandhi(moon_sidereal) # Returns Python bool now
            },
            "dasha": {
                "current_lord": str(dasha_lord),
                "balance_years": float(balance)
            },
            "current_transits": current_transits # Pass transits directly
        }

    except Exception as e:
        return {"status": "error", "message": str(e)}

def get_current_transits():
    """Fetches Live Transits."""
    eph = load_skyfield_data()
    earth = eph['earth']
    ts = load.timescale()
    t = ts.now()
    dt_now = datetime.datetime.utcnow()
    ayanamsa = get_lahiri_ayanamsa(dt_now)

    planets = {
        'Sun': eph['sun'], 'Jupiter': eph['jupiter_barycenter'],
        'Saturn': eph['saturn_barycenter'], 'Rahu': eph['moon'] # simplified for demo
    }

    transits = {}
    for name, body in planets.items():
        astrometric = earth.at(t).observe(body)
        _, lon, _ = astrometric.apparent().ecliptic_latlon()
        sidereal = tropical_to_sidereal(lon.degrees, ayanamsa)
        sign = ZODIAC_SIGNS[int(sidereal / 30)]
        transits[name] = sign

    return transits

# Tool Configuration
tools_list = [calculate_vedic_chart]
tool_map = {
    'calculate_vedic_chart': calculate_vedic_chart
}
