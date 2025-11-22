import requests
from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

# ---------- CONSTANTS (API URLs) ----------

NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"
OVERPASS_URL = "https://overpass-api.de/api/interpreter"

HEADERS = {
    # Nominatim / Overpass require a proper user-agent
    "User-Agent": "TourismChatbot/1.0 (isha22ainds@cmrit.acin)"
}

# ---------- CUSTOM ERROR ----------

class PlaceNotFoundError(Exception):
    """Raised when geocoding cannot find the place."""
    pass

# ---------- CHILD AGENT 0: GEOCODING ----------

def geocode_place(place_name: str):
    params = {
        "q": place_name,
        "format": "json",
        "limit": 1
    }
    resp = requests.get(NOMINATIM_URL, params=params, headers=HEADERS, timeout=10)
    resp.raise_for_status()
    data = resp.json()

    if not data:
        raise PlaceNotFoundError(f"Place '{place_name}' not found.")

    first = data[0]
    return {
        "name": first.get("display_name", place_name),
        "lat": float(first["lat"]),
        "lon": float(first["lon"])
    }

# ---------- CHILD AGENT 1: WEATHER ----------

def get_weather(lat: float, lon: float):
    params = {
        "latitude": lat,
        "longitude": lon,
        "current_weather": True,
        "hourly": "precipitation_probability",
        "timezone": "auto",
    }

    resp = requests.get(OPEN_METEO_URL, params=params, timeout=10)
    resp.raise_for_status()
    data = resp.json()

    current = data.get("current_weather", {})
    hourly = data.get("hourly", {})

    rain_chance = None
    try:
        times = hourly.get("time", [])
        probs = hourly.get("precipitation_probability", [])
        current_time = current.get("time")

        if times and probs:
            if current_time in times:
                idx = times.index(current_time)
                rain_chance = probs[idx]
            else:
                for i, t in enumerate(times):
                    if t > current_time:
                        rain_chance = probs[i]
                        break
                if rain_chance is None:
                    rain_chance = probs[0]
    except Exception:
        rain_chance = None

    return {
        "temperature": current.get("temperature"),
        "windspeed": current.get("windspeed"),
        "weathercode": current.get("weathercode"),
        "rain_chance": rain_chance
    }

# ---------- CHILD AGENT 2: PLACES ----------

def get_places(lat: float, lon: float, radius_m: int = 15000, limit: int = 5):
    """
    Fetch up to 'limit' famous tourism spots near (lat, lon):
    temples, beaches, waterfalls, attractions, parks, historic places.
    """
    query = f"""
    [out:json][timeout:25];
    (
      // General tourist attractions
      node["tourism"~"attraction|museum|zoo|theme_park|viewpoint"](around:{radius_m},{lat},{lon});
      way["tourism"~"attraction|museum|zoo|theme_park|viewpoint"](around:{radius_m},{lat},{lon});
      relation["tourism"~"attraction|museum|zoo|theme_park|viewpoint"](around:{radius_m},{lat},{lon});

      // Parks & gardens
      node["leisure"~"park|garden"](around:{radius_m},{lat},{lon});
      way["leisure"~"park|garden"](around:{radius_m},{lat},{lon});

      // Temples / worship
      node["amenity"="place_of_worship"](around:{radius_m},{lat},{lon});
      way["amenity"="place_of_worship"](around:{radius_m},{lat},{lon});
      relation["amenity"="place_of_worship"](around:{radius_m},{lat},{lon});

      // Beaches
      node["leisure"="beach"](around:{radius_m},{lat},{lon});
      way["leisure"="beach"](around:{radius_m},{lat},{lon});
      node["natural"="beach"](around:{radius_m},{lat},{lon});
      way["natural"="beach"](around:{radius_m},{lat},{lon});
      relation["natural"="beach"](around:{radius_m},{lat},{lon});

      // Waterfalls
      node["natural"="waterfall"](around:{radius_m},{lat},{lon});
      way["natural"="waterfall"](around:{radius_m},{lat},{lon});
      relation["natural"="waterfall"](around:{radius_m},{lat},{lon});

      // Historic
      node["historic"]["name"](around:{radius_m},{lat},{lon});
      way["historic"]["name"](around:{radius_m},{lat},{lon});
      relation["historic"]["name"](around:{radius_m},{lat},{lon});
    );
    out center;
    """

    resp = requests.post(
        OVERPASS_URL,
        data=query.encode("utf-8"),
        headers=HEADERS,
        timeout=30,
    )
    resp.raise_for_status()
    data = resp.json()

    elements = data.get("elements", [])
    names = []
    seen = set()

    for e in elements:
        tags = e.get("tags", {})
        name = tags.get("name")
        if not name:
            continue
        if name in seen:
            continue
        seen.add(name)
        names.append(name)
        if len(names) >= limit:
            break

    return names

# ---------- INTENT CLASSIFIER ----------

def classify_intent(user_text: str):
    text = user_text.lower()

    ask_weather = any(word in text for word in [
        "weather", "temperature", "hot", "cold", "rain", "raining"
    ])

    ask_places = any(word in text for word in [
        "place", "places", "visit", "attraction", "tourist", "trip", "plan my trip"
    ])

    if ask_weather and ask_places:
        return "both"
    if ask_weather:
        return "weather"
    if ask_places:
        return "places"
    return "both"

# ---------- PARENT AGENT LOGIC (single-turn) ----------

def tourism_chat_reply(user_text: str) -> str:
    lower = user_text.lower()
    place = None

    for keyword in [" to ", " in "]:
        if keyword in lower:
            idx = lower.rfind(keyword)
            place_part = user_text[idx + len(keyword):].strip(" ?!.,")
            comma_idx = place_part.find(',')
            if comma_idx != -1:
                place_part = place_part[:comma_idx]
            for stop in [" what", " and", " which", " where", " when", " how", " let's"]:
                stop_idx = place_part.lower().find(stop)
                if stop_idx != -1:
                    place_part = place_part[:stop_idx].strip(" ,")
            place = place_part.strip()
            break

    if not place:
        return "Please mention where you're going (e.g., 'I'm going to go to Bangalore...')."

    intent = classify_intent(user_text)

    # Geocoding
    try:
        location = geocode_place(place)
    except PlaceNotFoundError:
        return "Sorry, I don't know this place exists. Could you check the spelling or try another location?"
    except Exception:
        return "I had trouble looking up that place. Please try again later."

    lat, lon = location["lat"], location["lon"]
    city_display = place

    weather_info = None
    places = None

    if intent in ("weather", "both"):
        try:
            weather_info = get_weather(lat, lon)
        except Exception:
            pass

    if intent in ("places", "both"):
        try:
            places = get_places(lat, lon)
        except Exception:
            pass

    # Build reply text
    lines = []

    if weather_info and weather_info.get("temperature") is not None:
        temp = weather_info["temperature"]
        rain_chance = weather_info.get("rain_chance")
        if rain_chance is not None:
            lines.append(
                f"In {city_display} it's currently {temp}°C with a chance of {rain_chance}% to rain."
            )
        else:
            lines.append(
                f"In {city_display} it's currently {temp}°C, but the rain percentage is not available."
            )

    if intent in ("places", "both"):
        if places:
            lines.append(f"In {city_display} these are the places you can go,")
            for p in places:
                lines.append(f"- {p}")
        else:
            lines.append(f"I couldn't find well-tagged tourist places near {city_display}.")

    if not lines:
        lines.append("I couldn't fetch any information right now, please try again later.")

    return "\n".join(lines)

# ---------- FLASK ROUTES ----------

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json(force=True)
    user_msg = data.get("message", "").strip()
    if not user_msg:
        return jsonify({"reply": "Please type a message."})
    reply = tourism_chat_reply(user_msg)
    return jsonify({"reply": reply})

if __name__ == "__main__":
    app.run(debug=True)