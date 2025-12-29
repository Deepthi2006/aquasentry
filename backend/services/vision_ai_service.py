import os
import json
import logging
import base64
from typing import Dict, Any, Optional

from groq import Groq

client: Groq | None = None


# -------------------- CLIENT SETUP -------------------- #

def get_groq_client() -> Optional[Groq]:
    """
    Returns a singleton Groq client.
    Expects GROQ_API_KEY to be set in environment.
    """
    global client
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        return None

    if client is None:
        client = Groq(api_key=api_key)
    return client


def _image_bytes_to_data_url(image_bytes: bytes, mime_type: str) -> str:
    """
    Convert raw image bytes to a base64 data URL string that
    Groq vision models accept as image_url.url.
    """
    b64 = base64.b64encode(image_bytes).decode("utf-8")
    return f"data:{mime_type};base64,{b64}"


def _extract_json_from_text(text: str) -> Any:
    """
    Some models may wrap JSON in extra text or code fences.
    This helper finds the first '{' and last '}' and parses that.
    """
    text = text.strip()
    start = text.find("{")
    end = text.rfind("}") + 1
    if start == -1 or end == -1:
        raise ValueError("No JSON object found in model response")
    json_str = text[start:end]
    return json.loads(json_str)


# -------------------- WATER IMAGE ANALYSIS -------------------- #

def analyze_water_image(
    image_bytes: bytes,
    mime_type: str = "image/jpeg",
    tank_context: Optional[dict] = None,
) -> Dict[str, Any]:
    """
    Analyze a water sample / tank water image using a Groq vision model.
    """
    groq_client = get_groq_client()

    if not groq_client:
        return {
            "success": False,
            "error": "GROQ_API_KEY not configured. Please add your Groq API key for Vision AI.",
            "analysis": None,
        }

    try:
        data_url = _image_bytes_to_data_url(image_bytes, mime_type)

        context_info = ""
        if tank_context:
            context_info = f"""
Tank Context:
- Name: {tank_context.get('name', 'Unknown')}
- Last Cleaned: {tank_context.get('last_cleaned', 'Unknown')}
- Current pH: {tank_context.get('current_readings', {}).get('ph', 'N/A')}
- Current Turbidity: {tank_context.get('current_readings', {}).get('turbidity', 'N/A')} NTU
"""

        prompt = f"""You are an AI water quality visual inspector for AquaSentry Live, analyzing images of water samples or water tanks for Indian government water utilities.

{context_info}

Analyze this water image for:
1. Visual contamination indicators
2. Color abnormalities (should be clear/colorless)
3. Turbidity/cloudiness level
4. Presence of particles, sediment, or floating matter
5. Algae growth indicators
6. Signs of biological contamination
7. Surface conditions (for tank images)

Indian Water Quality Standards (BIS IS 10500):
- Water should be clear, colorless, odorless
- No visible suspended particles
- No algae or biological growth

Respond ONLY with valid JSON in exactly this structure, no extra text:

{{
    "contamination_detected": boolean,
    "contamination_level": "none|low|moderate|high|severe",
    "confidence": number,
    "visual_indicators": [
        {{"indicator": "name", "severity": "low|medium|high", "description": "details"}}
    ],
    "color_analysis": {{
        "detected_color": "description",
        "is_normal": boolean,
        "possible_causes": ["causes if abnormal"]
    }},
    "turbidity_estimate": {{
        "visual_ntu_estimate": number | null,
        "clarity_rating": "clear|slightly_cloudy|cloudy|very_cloudy|opaque"
    }},
    "biological_contamination": {{
        "algae_detected": boolean,
        "bacterial_indicators": boolean,
        "description": "details"
    }},
    "recommended_tests": ["laboratory tests recommended"],
    "immediate_actions": ["actions needed"],
    "safety_assessment": {{
        "safe_for_drinking": boolean,
        "safe_for_domestic_use": boolean,
        "requires_treatment": boolean
    }},
    "government_reporting": {{
        "report_to_authorities": boolean,
        "jjm_notification_needed": boolean,
        "phc_alert_needed": boolean
    }},
    "summary": "Plain language summary for officers"
}}"""

        completion = groq_client.chat.completions.create(
            model="meta-llama/llama-4-scout-17b-16e-instruct",  # vision-capable Groq model
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {"url": data_url},
                        },
                    ],
                }
            ],
            temperature=0.2,
            max_tokens=900,
        )

        raw_text = completion.choices[0].message.content if completion.choices else ""

        if not raw_text:
            return {"success": False, "error": "Empty response from Vision AI", "analysis": None}

        result = _extract_json_from_text(raw_text)

        return {
            "success": True,
            "analysis": result,
        }

    except Exception as e:
        logging.error(f"Vision AI error (Groq): {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "analysis": None,
        }


# -------------------- TANK INFRASTRUCTURE ANALYSIS -------------------- #

def analyze_tank_infrastructure(
    image_bytes: bytes,
    mime_type: str = "image/jpeg",
) -> Dict[str, Any]:
    """
    Analyze tank infrastructure (walls, pipes, valves, etc.) using Groq vision.
    """
    groq_client = get_groq_client()

    if not groq_client:
        return {
            "success": False,
            "error": "GROQ_API_KEY not configured",
            "analysis": None,
        }

    try:
        data_url = _image_bytes_to_data_url(image_bytes, mime_type)

        prompt = """You are an AI infrastructure inspector for water tank facilities.

Analyze this image of water tank infrastructure for:
1. Structural integrity
2. Visible damage or cracks
3. Corrosion or rust
4. Pipeline condition
5. Valve and fitting status
6. Safety equipment presence
7. Cleanliness and maintenance state

Respond ONLY with valid JSON in exactly this structure, no extra text:

{
  "infrastructure_assessment": {
    "overall_condition": "good|fair|poor|critical",
    "confidence": number
  },
  "issues_detected": [
    {
      "issue": "description",
      "severity": "minor|moderate|major|critical",
      "location": "where"
    }
  ],
  "structural_integrity": {
    "status": "sound|minor_issues|concerns|compromised",
    "details": "description"
  },
  "maintenance_needs": [
    {
      "item": "what needs attention",
      "urgency": "routine|soon|urgent|immediate",
      "estimated_cost_inr": number
    }
  ],
  "safety_concerns": ["list of safety issues"],
  "compliance_status": {
    "meets_standards": boolean,
    "violations": ["list if any"]
  },
  "recommendations": ["prioritized list of actions"],
  "summary": "Brief assessment for maintenance team"
}
"""

        completion = groq_client.chat.completions.create(
            model="meta-llama/llama-4-scout-17b-16e-instruct",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {"url": data_url},
                        },
                    ],
                }
            ],
            temperature=0.25,
            max_tokens=900,
        )

        raw_text = completion.choices[0].message.content if completion.choices else ""

        if not raw_text:
            return {"success": False, "error": "Empty response from Vision AI", "analysis": None}

        result = _extract_json_from_text(raw_text)

        return {
            "success": True,
            "analysis": result,
        }

    except Exception as e:
        logging.error(f"Infrastructure analysis error (Groq): {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "analysis": None,
        }
