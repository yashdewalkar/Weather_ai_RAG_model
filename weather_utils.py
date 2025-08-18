
import os, re, requests
from dotenv import load_dotenv
load_dotenv(override=True) 

def _sanitize_city(city: str) -> str:
   
    city = re.sub(r"[^\w\s\-.]", "", city or "")
    city = city.strip(" .,-?")
    return re.sub(r"\s{2,}", " ", city)

def fetch_weather(city: str, units: str = "metric") -> str:
    key = os.getenv("OPENWEATHER_API_KEY")
    if not key:
        return "OpenWeather API key missing. Set OPENWEATHER_API_KEY in .env."

    city_q = _sanitize_city(city or os.getenv("DEFAULT_CITY", "Pune"))
    base = "https://api.openweathermap.org/data/2.5"

    def call(endpoint, q):
        return requests.get(
            f"{base}/{endpoint}",
            params={"q": q, "appid": key, "units": units},
            timeout=20,
        )

    
    r = call("weather", city_q)
   
    if r.status_code == 404 and "," not in city_q:
        r = call("weather", f"{city_q},IN")

    if r.status_code != 200:
        try:
            msg = r.json().get("message", r.text)
        except Exception:
            msg = r.text
        return f"Sorry, couldn't fetch weather data ({r.status_code}): {msg}"

    cur = r.json()
    
    fc = call("forecast", city_q)
    if fc.status_code == 404 and "," not in city_q:
        fc = call("forecast", f"{city_q},IN")
    forecast = fc.json() if fc.status_code == 200 else {"list": []}

    name = cur.get("name") or city_q
    desc = (cur.get("weather") or [{}])[0].get("description", "").title()
    temp = cur.get("main", {}).get("temp")
    hum = cur.get("main", {}).get("humidity")
    wind = cur.get("wind", {}).get("speed")
    unit_t = "°C" if units == "metric" else "°F"
    unit_w = "m/s" if units == "metric" else "mph"

    lines = [f"**{name}**: {desc}, {temp}{unit_t}, humidity {hum}%, wind {wind} {unit_w}."]
    for step in (forecast.get("list") or [])[:5]:
        t = step.get("main", {}).get("temp")
        d = (step.get("weather") or [{}])[0].get("description", "").title()
        lines.append(f"- {d}, {t}{unit_t}")
    return "\n".join(lines)
