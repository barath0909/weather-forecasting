import os
from datetime import datetime, timedelta
from flask import Flask, render_template, request, jsonify
import requests
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
WEATHER_API_KEY = os.getenv("WEATHER_API_KEY")

def deg_to_compass(num):
    val = int((num / 22.5) + 0.5)
    arr = ["North", "NNE", "NE", "ENE", "East", "ESE", "SE", "SSE",
           "South", "SSW", "SW", "WSW", "West", "WNW", "NW", "NNW"]
    return arr[(val % 16)]

def evaluate_aqi(aqi_val, pm25, pm10):
    # Mapping OpenWeather / Indian CPCB context
    aqi_map = {
        1: {"badge": "Good", "color": "aqi-good", "advice": "Air quality is satisfactory. Enjoy outdoor activities!"},
        2: {"badge": "Fair", "color": "aqi-fair", "advice": "Acceptable air quality; sensitive groups should consider limiting prolonged outdoor exertion."},
        3: {"badge": "Moderate", "color": "aqi-moderate", "advice": "Slight irritation possible for asthmatics. Sensitive individuals should wear a mask."},
        4: {"badge": "Poor", "color": "aqi-poor", "advice": "Unhealthy air. People with respiratory illnesses should avoid outdoor exertion."},
        5: {"badge": "Severe / Hazardous", "color": "aqi-severe", "advice": "Emergency condition: High pollution levels. Stay indoors and use air purifiers."}
    }
    details = aqi_map.get(aqi_val, aqi_map[2])
    return {
        "score": aqi_val,
        "badge": details["badge"],
        "color": details["color"],
        "advice": details["advice"],
        "pm25": round(pm25, 1),
        "pm10": round(pm10, 1)
    }

@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")

@app.route("/weather", methods=["GET"])
def get_weather():
    city = request.args.get("city", "").strip()
    lat = request.args.get("lat")
    lon = request.args.get("lon")

    base_url = "https://api.openweathermap.org/data/2.5"
    params = {
        "appid": WEATHER_API_KEY,
        "units": "metric"
    }

    if lat and lon:
        params["lat"] = lat
        params["lon"] = lon
    elif city:
        search_query = city if "," in city else f"{city},IN"
        params["q"] = search_query
    else:
        return render_template("index.html", error="Please enter a city name or use your current location.")

    try:
        curr_res = requests.get(f"{base_url}/weather", params=params, timeout=5)
        if curr_res.status_code == 404 and city and "," not in city:
            params["q"] = city
            curr_res = requests.get(f"{base_url}/weather", params=params, timeout=5)

        fore_res = requests.get(f"{base_url}/forecast", params=params, timeout=5)
    except requests.exceptions.RequestException:
        return render_template("index.html", error="Unable to retrieve weather information. Please try again later.")

    if curr_res.status_code == 404 or fore_res.status_code == 404:
        return render_template("index.html", error="Location not found. Please check spelling or select from the list.")

    if curr_res.status_code != 200 or fore_res.status_code != 200:
        return render_template("index.html", error="Unable to retrieve weather information. Please try again later.")

    curr_data = curr_res.json()
    fore_data = fore_res.json()

    # Coordinates for AQI and Map
    coord_lat = curr_data.get("coord", {}).get("lat")
    coord_lon = curr_data.get("coord", {}).get("lon")

    # Fetch Air Pollution Data
    aqi_data = {}
    try:
        pollution_res = requests.get(
            f"{base_url}/air_pollution",
            params={"lat": coord_lat, "lon": coord_lon, "appid": WEATHER_API_KEY},
            timeout=5
        )
        if pollution_res.status_code == 200:
            poll_json = pollution_res.json().get("list", [{}])[0]
            aqi_score = poll_json.get("main", {}).get("aqi", 2)
            components = poll_json.get("components", {})
            aqi_data = evaluate_aqi(aqi_score, components.get("pm2_5", 0), components.get("pm10", 0))
    except Exception:
        aqi_data = evaluate_aqi(2, 25.0, 45.0)

    # Sun & Solar calculations
    timezone_offset = curr_data.get("timezone", 19800)  # Default to IST (UTC+5:30)
    sunrise_ts = curr_data.get("sys", {}).get("sunrise", 0) + timezone_offset
    sunset_ts = curr_data.get("sys", {}).get("sunset", 0) + timezone_offset
    now_ts = datetime.utcnow().timestamp() + timezone_offset

    sunrise_dt = datetime.utcfromtimestamp(sunrise_ts)
    sunset_dt = datetime.utcfromtimestamp(sunset_ts)

    # Golden Hour: approx 1 hour before sunset
    golden_hour_start = (sunset_dt - timedelta(hours=1)).strftime("%I:%M %p")
    daylight_hours = round((sunset_ts - sunrise_ts) / 3600, 1)

    sun_info = {
        "sunrise": sunrise_dt.strftime("%I:%M %p"),
        "sunset": sunset_dt.strftime("%I:%M %p"),
        "golden_hour": golden_hour_start,
        "daylight": f"{daylight_hours} hrs",
        "is_day": sunrise_ts <= now_ts <= sunset_ts
    }

    # Wind and general parameters
    wind_deg = curr_data.get("wind", {}).get("deg", 0)
    wind_dir = deg_to_compass(wind_deg)
    wind_kmh = round(curr_data.get("wind", {}).get("speed", 0) * 3.6)
    temp_val = round(curr_data.get("main", {}).get("temp", 0))
    temp_sign = f"+{temp_val}" if temp_val > 0 else f"{temp_val}"

    weather_desc = curr_data.get("weather", [{}])[0].get("description", "")
    alerts = []
    if "storm" in weather_desc.lower() or "thunder" in weather_desc.lower():
        alerts.append("Severe Weather Warning: Thunderstorm active in this area.")
    if wind_kmh > 45:
        alerts.append(f"High Wind Advisory: Gusts up to {wind_kmh} km/h.")

    weather_info = {
        "city": curr_data.get("name"),
        "country": curr_data.get("sys", {}).get("country"),
        "day_name": datetime.now().strftime("%A"),
        "temp_display": temp_sign,
        "temperature": temp_val,
        "feels_like": round(curr_data.get("main", {}).get("feels_like", 0)),
        "humidity": curr_data.get("main", {}).get("humidity"),
        "pressure": curr_data.get("main", {}).get("pressure"),
        "wind_info": f"{wind_dir}, {wind_kmh} km/h",
        "icon": curr_data.get("weather", [{}])[0].get("icon", "01d"),
        "condition": curr_data.get("weather", [{}])[0].get("main", "Clear"),
        "lat": coord_lat,
        "lon": coord_lon,
        "alerts": alerts
    }

    # Aggregate by Day of the Week (Monday, Tuesday, Wednesday, etc.)
    daily_groups = {}
    chart_labels = []
    chart_temps = []

    for item in fore_data.get("list", []):
        dt = datetime.utcfromtimestamp(item["dt"] + timezone_offset)
        day_full = dt.strftime("%A")
        date_str = dt.strftime("%b %d")
        time_str = dt.strftime("%a %H:%M")
        temp = round(item["main"]["temp"], 1)

        chart_labels.append(time_str)
        chart_temps.append(temp)

        if day_full not in daily_groups:
            daily_groups[day_full] = {
                "day_name": day_full,
                "date": date_str,
                "temps": [],
                "conditions": [],
                "icons": [],
                "humidities": []
            }

        daily_groups[day_full]["temps"].append(temp)
        daily_groups[day_full]["conditions"].append(item["weather"][0]["main"])
        daily_groups[day_full]["icons"].append(item["weather"][0]["icon"])
        daily_groups[day_full]["humidities"].append(item["main"]["humidity"])

    daily_reports = []
    for day_name, ddata in daily_groups.items():
        daily_reports.append({
            "day_name": day_name,
            "date": ddata["date"],
            "max_temp": round(max(ddata["temps"])),
            "min_temp": round(min(ddata["temps"])),
            "avg_humidity": round(sum(ddata["humidities"]) / len(ddata["humidities"])),
            "condition": ddata["conditions"][len(ddata["conditions"]) // 2],
            "icon": ddata["icons"][len(ddata["icons"]) // 2]
        })

    return render_template(
        "weather.html",
        weather=weather_info,
        sun=sun_info,
        aqi=aqi_data,
        daily_reports=daily_reports[:7],
        chart_labels=chart_labels[:16],
        chart_temps=chart_temps[:16]
    )

@app.route("/health", methods=["GET"])
def health_check():
    return jsonify({"status": "healthy"}), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)