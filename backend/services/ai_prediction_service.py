import os
import json
import logging
from typing import Dict, Any, List
from datetime import datetime, timedelta

from groq import Groq

client = None


# -------------------- GROQ CLIENT HELPERS -------------------- #

def get_groq_client() -> Groq | None:
    """
    Returns a singleton Groq client instance.
    Expects GROQ_API_KEY to be set in the environment.
    """
    global client
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        return None

    if client is None:
        client = Groq(api_key=api_key)
    return client


def _extract_json_from_text(text: str) -> Any:
    """
    Sometimes models add extra text or code fences.
    This helper finds the first '{' and last '}' and parses that substring.
    """
    if not text:
        raise ValueError("Empty response from model")

    text = text.strip()
    start = text.find("{")
    end = text.rfind("}") + 1
    if start == -1 or end == 0:
        raise ValueError("No JSON object found in model response")
    json_str = text[start:end]
    return json.loads(json_str)


# -------------------- WATER QUALITY PREDICTION -------------------- #

def predict_water_quality(tank_data: dict, history: List[dict]) -> Dict[str, Any]:
    groq_client = get_groq_client()

    if not groq_client:
        return generate_fallback_prediction(tank_data, history)

    try:
        readings = tank_data.get("current_readings", {}) or {}
        prompt = f"""
You are an expert water quality prediction AI for AquaSentry Live,
a government water tank monitoring system in India.

Analyze this tank's historical data and predict water quality for the next 24–48 hours.

Tank: {tank_data.get('name', 'Unknown')}

Current Readings:
- pH: {readings.get('ph', 7.0)}
- Turbidity: {readings.get('turbidity', 0)} NTU
- Temperature: {readings.get('temperature', 20)} °C
- Water Level: {tank_data.get('current_level_percent', 0)} %
- Days Since Cleaned: {tank_data.get('days_since_cleaned', 0)}

Historical Data (last 7 days, if available):
{json.dumps(history[-7:] if history else [], indent=2)}

Indian Government BIS Standards:
- pH: 6.5–8.5 (ideal 7.0–7.5)
- Turbidity: <1 NTU (acceptable <5 NTU)
- Temperature: 15–25 °C

Predict values for:
1. Next 24 hours
2. Next 48 hours

Respond ONLY with valid JSON in this structure (no extra text):

{{
  "predictions": {{
    "24h": {{"ph": number, "turbidity": number, "temperature": number, "confidence": number}},
    "48h": {{"ph": number, "turbidity": number, "temperature": number, "confidence": number}}
  }},
  "trend_analysis": {{
    "ph_trend": "stable|increasing|decreasing",
    "turbidity_trend": "stable|increasing|decreasing",
    "temperature_trend": "stable|increasing|decreasing"
  }},
  "risk_level": "low|medium|high|critical",
  "risk_factors": ["list of risk factors"],
  "recommended_actions": ["list of actions"],
  "government_impact": "Brief explanation of impact for Indian water utilities"
}}
"""

        completion = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt.strip()}],
            temperature=0.3,
            max_tokens=900,
        )

        raw = completion.choices[0].message.content if completion.choices else ""
        result = _extract_json_from_text(raw)
        return {"success": True, "prediction": result}

    except Exception as e:
        logging.error(f"AI prediction error (Groq): {str(e)}")
        return generate_fallback_prediction(tank_data, history)


def generate_fallback_prediction(tank_data: dict, history: List[dict]) -> Dict[str, Any]:
    readings = tank_data.get("current_readings", {}) or {}
    ph = readings.get("ph", 7.0)
    turbidity = readings.get("turbidity", 1.0)
    temp = readings.get("temperature", 20.0)

    ph_trend = turb_trend = temp_trend = 0.0

    if history and len(history) >= 2:
        ph_trend = (history[-1].get("ph", ph) - history[0].get("ph", ph)) / len(history)
        turb_trend = (
            history[-1].get("turbidity", turbidity)
            - history[0].get("turbidity", turbidity)
        ) / len(history)
        temp_trend = (
            history[-1].get("temperature", temp)
            - history[0].get("temperature", temp)
        ) / len(history)

    prediction = {
        "predictions": {
            "24h": {
                "ph": round(ph + ph_trend, 2),
                "turbidity": round(max(0, turbidity + turb_trend), 2),
                "temperature": round(temp + temp_trend, 1),
                "confidence": 0.7,
            },
            "48h": {
                "ph": round(ph + ph_trend * 2, 2),
                "turbidity": round(max(0, turbidity + turb_trend * 2), 2),
                "temperature": round(temp + temp_trend * 2, 1),
                "confidence": 0.5,
            },
        },
        "trend_analysis": {
            "ph_trend": "stable"
            if abs(ph_trend) < 0.1
            else ("increasing" if ph_trend > 0 else "decreasing"),
            "turbidity_trend": "stable"
            if abs(turb_trend) < 0.2
            else ("increasing" if turb_trend > 0 else "decreasing"),
            "temperature_trend": "stable"
            if abs(temp_trend) < 0.3
            else ("increasing" if temp_trend > 0 else "decreasing"),
        },
        "risk_level": "low",
        "risk_factors": [],
        "recommended_actions": [],
        "government_impact": "Fallback prediction - AI unavailable",
    }

    if turbidity > 5 or ph < 6.5 or ph > 8.5:
        prediction["risk_level"] = "high"
        prediction["risk_factors"].append("Current readings exceed safe thresholds")

    return {"success": True, "prediction": prediction, "fallback": True}


# -------------------- LEAKAGE / OVERFLOW DETECTION -------------------- #

def detect_leakage_overflow(tank_data: dict, history: List[dict]) -> Dict[str, Any]:
    groq_client = get_groq_client()

    if not groq_client:
        return detect_leakage_fallback(tank_data, history)

    try:
        prompt = f"""
You are an AI anomaly detection system for water tank leakage and overflow detection.

Analyze this tank data for potential leakage or overflow.

Tank: {tank_data.get('name', 'Unknown')}
Capacity: {tank_data.get('capacity_liters', 0)} liters
Current Level: {tank_data.get('current_level_percent', 0)} %

Water Level History (last 7 records if present):
{json.dumps(history[-7:] if history else [], indent=2)}

Look for:
1. Unexplained water loss (potential leakage)
2. Rapid level changes (overflow risk)
3. Abnormal consumption patterns
4. Seasonal anomalies

Respond ONLY with valid JSON in this structure:

{{
  "anomaly_detected": boolean,
  "anomaly_type": "none|leakage|overflow|unusual_consumption",
  "severity": "none|low|medium|high|critical",
  "confidence": number,
  "details": {{
    "estimated_loss_liters_per_day": number | null,
    "overflow_risk_percent": number,
    "pattern_description": "string"
  }},
  "recommended_actions": ["list"],
  "government_alert_required": boolean,
  "impact_assessment": "Impact for Indian water utilities"
}}
"""

        completion = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt.strip()}],
            temperature=0.3,
            max_tokens=800,
        )

        raw = completion.choices[0].message.content if completion.choices else ""
        result = _extract_json_from_text(raw)
        return {"success": True, "analysis": result}

    except Exception as e:
        logging.error(f"Leakage detection error (Groq): {str(e)}")
        return detect_leakage_fallback(tank_data, history)


def detect_leakage_fallback(tank_data: dict, history: List[dict]) -> Dict[str, Any]:
    current_level = tank_data.get("current_level_percent", 50)

    level_changes = []
    if history and len(history) >= 2:
        for i in range(1, len(history)):
            change = history[i].get("turbidity", 0) - history[i - 1].get("turbidity", 0)
            level_changes.append(change)

    avg_change = sum(level_changes) / len(level_changes) if level_changes else 0

    anomaly_detected = current_level < 30 or current_level > 95 or abs(avg_change) > 1

    return {
        "success": True,
        "analysis": {
            "anomaly_detected": anomaly_detected,
            "anomaly_type": "none"
            if not anomaly_detected
            else (
                "overflow"
                if current_level > 95
                else "leakage"
                if current_level < 30
                else "unusual_consumption"
            ),
            "severity": "none" if not anomaly_detected else "medium",
            "confidence": 0.6,
            "details": {
                "estimated_loss_liters_per_day": None,
                "overflow_risk_percent": max(0, (current_level - 85) * 5)
                if current_level > 85
                else 0,
                "pattern_description": "Rule-based analysis - AI unavailable",
            },
            "recommended_actions": [],
            "government_alert_required": anomaly_detected and current_level < 20,
            "impact_assessment": "Fallback analysis",
        },
        "fallback": True,
    }


# -------------------- MAINTENANCE SCHEDULE PREDICTION -------------------- #

def predict_maintenance_schedule(tank_data: dict, history: List[dict]) -> Dict[str, Any]:
    groq_client = get_groq_client()

    if not groq_client:
        return predict_maintenance_fallback(tank_data)

    try:
        readings = tank_data.get("current_readings", {}) or {}

        prompt = f"""
You are an AI predictive maintenance system for government water tanks.

Analyze this tank and recommend an optimal cleaning/maintenance schedule.

Tank: {tank_data.get('name', 'Unknown')}
Capacity: {tank_data.get('capacity_liters', 0)} liters
Last Cleaned: {tank_data.get('last_cleaned', 'Unknown')}
Days Since Cleaned: {tank_data.get('days_since_cleaned', 0)}
Current Status: {tank_data.get('status', 'unknown')}

Current Readings:
- pH: {readings.get('ph', 7.0)}
- Turbidity: {readings.get('turbidity', 0)} NTU
- Chlorine: {readings.get('chlorine', 0)} ppm

Historical Trends (last 7 records if available):
{json.dumps(history[-7:] if history else [], indent=2)}

Indian Government Guidelines:
- Tanks should typically be cleaned every 30–45 days.
- High turbidity tanks need more frequent cleaning.
- Pre-monsoon cleaning is mandatory.

Respond ONLY with valid JSON in this structure:

{{
  "recommended_cleaning_date": "YYYY-MM-DD",
  "urgency": "routine|soon|urgent|immediate",
  "days_until_recommended": number,
  "cleaning_type": "routine|deep|emergency",
  "estimated_duration_hours": number,
  "resources_needed": ["list of resources"],
  "cost_estimate_inr": number,
  "risk_if_delayed": "low|medium|high|critical",
  "reason": "explanation",
  "government_compliance": {{
    "bis_compliant": boolean,
    "jal_jeevan_mission_aligned": boolean
  }}
}}
"""

        completion = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt.strip()}],
            temperature=0.25,
            max_tokens=700,
        )

        raw = completion.choices[0].message.content if completion.choices else ""
        result = _extract_json_from_text(raw)
        return {"success": True, "maintenance": result}

    except Exception as e:
        logging.error(f"Maintenance prediction error (Groq): {str(e)}")
        return predict_maintenance_fallback(tank_data)


def predict_maintenance_fallback(tank_data: dict) -> Dict[str, Any]:
    days_since_cleaned = tank_data.get("days_since_cleaned", 0)
    turbidity = tank_data.get("current_readings", {}).get("turbidity", 0)

    if turbidity > 5 or days_since_cleaned > 45:
        urgency = "immediate"
        days_until = 0
    elif turbidity > 3 or days_since_cleaned > 35:
        urgency = "urgent"
        days_until = 3
    elif days_since_cleaned > 25:
        urgency = "soon"
        days_until = 7
    else:
        urgency = "routine"
        days_until = max(0, 30 - days_since_cleaned)

    recommended_date = (datetime.now() + timedelta(days=days_until)).strftime("%Y-%m-%d")

    return {
        "success": True,
        "maintenance": {
            "recommended_cleaning_date": recommended_date,
            "urgency": urgency,
            "days_until_recommended": days_until,
            "cleaning_type": "emergency" if urgency == "immediate" else "routine",
            "estimated_duration_hours": 4,
            "resources_needed": ["Cleaning crew", "Water testing kit"],
            "cost_estimate_inr": 15000,
            "risk_if_delayed": "high"
            if urgency in ["immediate", "urgent"]
            else "medium",
            "reason": f"Based on {days_since_cleaned} days since last cleaning",
            "government_compliance": {
                "bis_compliant": days_since_cleaned <= 30,
                "jal_jeevan_mission_aligned": True,
            },
        },
        "fallback": True,
    }


# -------------------- WATER DEMAND FORECASTING -------------------- #

def forecast_water_demand(tanks_data: List[dict]) -> Dict[str, Any]:
    groq_client = get_groq_client()

    if not groq_client:
        return forecast_demand_fallback(tanks_data)

    try:
        tanks_summary = []
        for tank in tanks_data:
            tanks_summary.append(
                {
                    "name": tank.get("name"),
                    "capacity": tank.get("capacity_liters"),
                    "current_level": tank.get("current_level_percent"),
                    "location": tank.get("location", {}).get("address", ""),
                }
            )

        prompt = f"""
You are an AI water demand forecasting system for Indian government water utilities.

Analyze these water tanks and predict demand for the next 7 days.

Tanks Data:
{json.dumps(tanks_summary, indent=2)}

Total Capacity: {sum(t.get('capacity_liters', 0) for t in tanks_data)} liters
Average Current Level: {sum(t.get('current_level_percent', 0) for t in tanks_data) / len(tanks_data) if tanks_data else 0} %

Consider:
1. Typical consumption patterns in Indian urban areas
2. Seasonal variations (current month: {datetime.now().strftime('%B')})
3. Weekend vs weekday patterns
4. Peak hours (morning 6–9 AM, evening 5–8 PM)

Respond ONLY with valid JSON in this structure:

{{
  "daily_forecasts": [
    {{
      "day": 1,
      "date": "YYYY-MM-DD",
      "predicted_demand_liters": number,
      "peak_hours": ["HH:MM"],
      "confidence": number
    }}
  ],
  "weekly_total_demand_liters": number,
  "average_daily_demand_liters": number,
  "peak_demand_day": "day name",
  "low_demand_day": "day name",
  "supply_adequacy": {{
    "sufficient": boolean,
    "deficit_liters": number | null,
    "tanks_at_risk": ["tank names"]
  }},
  "recommendations": ["list"],
  "government_planning_insights": "Insights for Indian water department planning"
}}
"""

        completion = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt.strip()}],
            temperature=0.35,
            max_tokens=900,
        )

        raw = completion.choices[0].message.content if completion.choices else ""
        result = _extract_json_from_text(raw)
        return {"success": True, "forecast": result}

    except Exception as e:
        logging.error(f"Demand forecast error (Groq): {str(e)}")
        return forecast_demand_fallback(tanks_data)


def forecast_demand_fallback(tanks_data: List[dict]) -> Dict[str, Any]:
    total_capacity = sum(t.get("capacity_liters", 0) for t in tanks_data)
    avg_daily_consumption = total_capacity * 0.15

    forecasts = []
    for i in range(7):
        date = (datetime.now() + timedelta(days=i + 1)).strftime("%Y-%m-%d")
        day_multiplier = 1.0 if i < 5 else 0.85
        forecasts.append(
            {
                "day": i + 1,
                "date": date,
                "predicted_demand_liters": int(avg_daily_consumption * day_multiplier),
                "peak_hours": ["07:00", "18:00"],
                "confidence": 0.6,
            }
        )

    return {
        "success": True,
        "forecast": {
            "daily_forecasts": forecasts,
            "weekly_total_demand_liters": int(avg_daily_consumption * 6.7),
            "average_daily_demand_liters": int(avg_daily_consumption),
            "peak_demand_day": "Monday",
            "low_demand_day": "Sunday",
            "supply_adequacy": {
                "sufficient": True,
                "deficit_liters": None,
                "tanks_at_risk": [],
            },
            "recommendations": ["Monitor tank levels during peak hours"],
            "government_planning_insights": "Fallback forecast - AI unavailable",
        },
        "fallback": True,
    }


# -------------------- RAINWATER HARVESTING PREDICTION -------------------- #

def predict_rainwater_harvesting(tanks_data: List[dict]) -> Dict[str, Any]:
    groq_client = get_groq_client()

    if not groq_client:
        return rainwater_fallback(tanks_data)

    try:
        tanks_summary = []
        for tank in tanks_data:
            tanks_summary.append(
                {
                    "name": tank.get("name"),
                    "capacity": tank.get("capacity_liters"),
                    "current_level": tank.get("current_level_percent"),
                    "overflow_potential": 100 - tank.get("current_level_percent", 0),
                }
            )

        prompt = f"""
You are an AI rainwater harvesting and overflow utilization advisor for Indian government water utilities.

Analyze these tanks for rainwater harvesting potential.

Tanks:
{json.dumps(tanks_summary, indent=2)}

Current Month: {datetime.now().strftime('%B')}
Consider Indian monsoon patterns and regional rainfall.

Respond ONLY with valid JSON in this structure:

{{
  "harvesting_potential": {{
    "total_overflow_capacity_liters": number,
    "recommended_tanks": [
      {{"name": "tank name", "overflow_capacity_liters": number, "harvesting_score": number}}
    ],
    "estimated_monthly_collection_liters": number
  }},
  "overflow_risk_analysis": {{
    "tanks_at_overflow_risk": ["names"],
    "recommended_diversions": ["diversion suggestions"]
  }},
  "monsoon_readiness": {{
    "score": number,
    "gaps": ["list of gaps"],
    "preparations_needed": ["list"]
  }},
  "cost_benefit": {{
    "estimated_savings_inr_monthly": number,
    "implementation_cost_inr": number,
    "payback_months": number
  }},
  "government_scheme_alignment": {{
    "jal_shakti_compatible": boolean,
    "swachh_bharat_aligned": boolean,
    "recommendations": ["policy recommendations"]
  }}
}}
"""

        completion = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt.strip()}],
            temperature=0.35,
            max_tokens=900,
        )

        raw = completion.choices[0].message.content if completion.choices else ""
        result = _extract_json_from_text(raw)
        return {"success": True, "harvesting": result}

    except Exception as e:
        logging.error(f"Rainwater prediction error (Groq): {str(e)}")
        return rainwater_fallback(tanks_data)


def rainwater_fallback(tanks_data: List[dict]) -> Dict[str, Any]:
    total_overflow = sum(
        (100 - t.get("current_level_percent", 0)) * t.get("capacity_liters", 0) / 100
        for t in tanks_data
    )

    recommended = []
    for tank in tanks_data:
        overflow_cap = (
            (100 - tank.get("current_level_percent", 0))
            * tank.get("capacity_liters", 0)
            / 100
        )
        if overflow_cap > 50000:
            recommended.append(
                {
                    "name": tank.get("name"),
                    "overflow_capacity_liters": int(overflow_cap),
                    "harvesting_score": min(100, int(overflow_cap / 1000)),
                }
            )

    return {
        "success": True,
        "harvesting": {
            "harvesting_potential": {
                "total_overflow_capacity_liters": int(total_overflow),
                "recommended_tanks": recommended[:5],
                "estimated_monthly_collection_liters": int(total_overflow * 0.3),
            },
            "overflow_risk_analysis": {
                "tanks_at_overflow_risk": [
                    t.get("name")
                    for t in tanks_data
                    if t.get("current_level_percent", 0) > 90
                ],
                "recommended_diversions": [
                    "Install overflow pipes to secondary storage"
                ],
            },
            "monsoon_readiness": {
                "score": 70,
                "gaps": ["Check overflow drainage"],
                "preparations_needed": ["Clean intake filters"],
            },
            "cost_benefit": {
                "estimated_savings_inr_monthly": 50000,
                "implementation_cost_inr": 200000,
                "payback_months": 4,
            },
            "government_scheme_alignment": {
                "jal_shakti_compatible": True,
                "swachh_bharat_aligned": True,
                "recommendations": ["Apply for Jal Jeevan Mission funding"],
            },
        },
        "fallback": True,
    }
