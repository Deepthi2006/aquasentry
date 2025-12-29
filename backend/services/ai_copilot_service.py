import os
import json
import logging
from typing import Dict, Any, List

from groq import Groq

client: Groq | None = None


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


# ---------- AQUA COPILOT CHAT ---------- #

def chat_with_copilot(
    query: str,
    tanks_data: List[dict],
    alerts_data: List[dict],
    context: str = ""
) -> Dict[str, Any]:
    groq_client = get_groq_client()

    if not groq_client:
        return {
            "success": False,
            "error": "GROQ_API_KEY not configured. Please add your Groq API key.",
            "response": (
                "I'm sorry, but I need a valid Groq API key to answer questions. "
                "Please configure the GROQ_API_KEY environment variable on the server."
            ),
        }

    try:
        # Compact summarised data we send to the model
        tanks_summary = []
        for tank in tanks_data[:10]:
            readings = tank.get("current_readings", {})
            tanks_summary.append(
                {
                    "id": tank.get("id"),
                    "name": tank.get("name"),
                    "status": tank.get("status"),
                    "level": tank.get("current_level_percent"),
                    "ph": readings.get("ph"),
                    "turbidity": readings.get("turbidity"),
                    "days_since_cleaned": tank.get("days_since_cleaned"),
                    "location": tank.get("location", {}).get("address", ""),
                }
            )

        alerts_summary = []
        for alert in alerts_data[:10]:
            alerts_summary.append(
                {
                    "tank_id": alert.get("tank_id"),
                    "type": alert.get("type"),
                    "message": alert.get("message"),
                    "acknowledged": alert.get("acknowledged", False),
                }
            )

        system_prompt = """
You are AquaCopilot, an AI assistant for Indian government water utility officers
using the AquaSentry Live water tank monitoring system.

You help officers with:
1. Understanding tank status and water quality
2. Interpreting alerts and recommending actions
3. Planning maintenance schedules
4. Compliance with BIS standards and Jal Jeevan Mission guidelines
5. Generating reports for supervisors
6. Troubleshooting water quality issues

Guidelines:
- Be clear, professional, and actionable.
- Reference actual tank IDs/names from the data when useful.
- Use metric units and Indian Rupees when mentioning cost.
- Follow Indian BIS drinking water standards:
  • pH: 6.5–8.5 (ideal 7.0–7.5)
  • Turbidity: <1 NTU (acceptable <5 NTU)
"""

        user_context = f"Previous Context: {context}\n\n" if context else ""

        user_prompt = f"""
Current System Data:

TANKS ({len(tanks_summary)} total):
{json.dumps(tanks_summary, indent=2)}

ACTIVE ALERTS ({len(alerts_summary)} total):
{json.dumps(alerts_summary, indent=2)}

{user_context}Officer Query: {query}

Answer based only on the data above. Be specific and practical.
"""

        completion = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": system_prompt.strip()},
                {"role": "user", "content": user_prompt.strip()},
            ],
            temperature=0.4,
            max_tokens=800,
        )

        text = completion.choices[0].message.content if completion.choices else ""

        if text:
            return {
                "success": True,
                "response": text,
                "query": query,
                "tanks_analyzed": len(tanks_summary),
                "alerts_reviewed": len(alerts_summary),
            }

        return {"success": False, "error": "Empty response from Groq model"}

    except Exception as e:
        logging.error(f"AquaCopilot (Groq) error: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "response": f"I encountered an error processing your request: {str(e)}",
        }


# ---------- EXPLAINABLE ALERT ---------- #

def generate_explainable_alert(
    alert: dict,
    tank_data: dict,
    history: List[dict],
) -> Dict[str, Any]:
    groq_client = get_groq_client()

    if not groq_client:
        # fall back to rule-based explanation when Groq is not available
        return generate_fallback_explanation(alert, tank_data)

    try:
        history_snippet = json.dumps(history[-7:] if history else [], indent=2)

        prompt = f"""
You are an AI alert explanation system for AquaSentry Live water monitoring.

Generate a detailed, explainable alert analysis in STRICT JSON format.

ALERT:
- Type: {alert.get('type')}
- Message: {alert.get('message')}
- Tank: {alert.get('tank_id')}
- Time: {alert.get('created_at', 'Unknown')}

TANK DATA:
- Name: {tank_data.get('name', 'Unknown')}
- Status: {tank_data.get('status', 'unknown')}
- Current pH: {tank_data.get('current_readings', {}).get('ph', 'N/A')}
- Current Turbidity: {tank_data.get('current_readings', {}).get('turbidity', 'N/A')} NTU
- Temperature: {tank_data.get('current_readings', {}).get('temperature', 'N/A')}°C
- Days Since Cleaned: {tank_data.get('days_since_cleaned', 'N/A')}
- Water Level: {tank_data.get('current_level_percent', 'N/A')}%

HISTORICAL TREND (last 7 records):
{history_snippet}

Respond ONLY with valid JSON in this structure, no extra text:

{{
  "root_cause_analysis": {{
    "primary_cause": "main reason for alert",
    "contributing_factors": ["list of factors"],
    "confidence": 0.0
  }},
  "severity_assessment": {{
    "level": "info|warning|critical",
    "impact_score": 1,
    "affected_population_estimate": 0
  }},
  "trend_explanation": "How conditions led to this alert",
  "recommended_actions": [
    {{
      "action": "description",
      "priority": "immediate|high|medium|low",
      "estimated_time": "duration",
      "responsible": "role"
    }}
  ],
  "prevention_measures": ["how to prevent recurrence"],
  "compliance_impact": {{
    "bis_violation": false,
    "jjm_compliance": true,
    "reporting_required": false
  }},
  "plain_language_summary": "Simple explanation for non-technical staff"
}}
"""

        completion = groq_client.chat.completions.create(
            model="llama-3.1-70b-versatile",
            messages=[{"role": "user", "content": prompt.strip()}],
            temperature=0.2,
            max_tokens=900,
        )

        raw_text = completion.choices[0].message.content if completion.choices else ""

        if not raw_text:
            return {"success": False, "error": "Empty response from Groq model"}

        # Try to extract JSON (in case the model adds extra text)
        raw_text = raw_text.strip()
        # Find first "{" and last "}" to be safe
        start = raw_text.find("{")
        end = raw_text.rfind("}") + 1
        json_str = raw_text[start:end]

        explanation = json.loads(json_str)

        return {
            "success": True,
            "explanation": explanation,
            "alert": alert,
        }

    except Exception as e:
        logging.error(f"Alert explanation (Groq) error: {str(e)}")
        # graceful fallback
        return generate_fallback_explanation(alert, tank_data)


# ---------- FALLBACK (RULE-BASED) ---------- #

def generate_fallback_explanation(alert: dict, tank_data: dict) -> Dict[str, Any]:
    alert_type = alert.get("type", "info")
    message = alert.get("message", "")

    readings = tank_data.get("current_readings", {})
    ph = readings.get("ph", 7.0)
    turbidity = readings.get("turbidity", 0)

    causes: List[str] = []
    actions: List[dict] = []

    if "ph" in message.lower():
        causes.append("pH imbalance detected in water")
        actions.append(
            {
                "action": "Test water pH and add neutralizing agents",
                "priority": "high",
                "estimated_time": "2 hours",
                "responsible": "Water Quality Officer",
            }
        )

    if "turbidity" in message.lower():
        causes.append("Suspended particles in water causing cloudiness")
        actions.append(
            {
                "action": "Check filtration system and clean if needed",
                "priority": "high",
                "estimated_time": "4 hours",
                "responsible": "Maintenance Team",
            }
        )

    if "maintenance" in message.lower() or "clean" in message.lower():
        causes.append("Tank requires cleaning based on schedule")
        actions.append(
            {
                "action": "Schedule tank cleaning",
                "priority": "medium",
                "estimated_time": "6 hours",
                "responsible": "Maintenance Supervisor",
            }
        )

    if not causes:
        causes.append("Alert triggered based on monitoring thresholds")
        actions.append(
            {
                "action": "Review tank status and take appropriate action",
                "priority": "medium",
                "estimated_time": "1 hour",
                "responsible": "Duty Officer",
            }
        )

    return {
        "success": True,
        "explanation": {
            "root_cause_analysis": {
                "primary_cause": causes[0] if causes else "Unknown",
                "contributing_factors": causes[1:] if len(causes) > 1 else [],
                "confidence": 0.6,
            },
            "severity_assessment": {
                "level": alert_type,
                "impact_score": 8
                if alert_type == "critical"
                else 5
                if alert_type == "warning"
                else 2,
                "affected_population_estimate": 1000,
            },
            "trend_explanation": "Based on rule-based fallback analysis.",
            "recommended_actions": actions,
            "prevention_measures": [
                "Regular monitoring",
                "Scheduled maintenance",
            ],
            "compliance_impact": {
                "bis_violation": alert_type == "critical",
                "jjm_compliance": alert_type != "critical",
                "reporting_required": alert_type == "critical",
            },
            "plain_language_summary": message,
        },
        "alert": alert,
        "fallback": True,
    }
