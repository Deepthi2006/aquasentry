import os
import json
import logging
from typing import Dict, Any, List, Optional

client = None

def get_gemini_client():
    global client
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        return None
    if client is None:
        from google import genai
        client = genai.Client(api_key=api_key)
    return client


def generate_recommendations(tanks_data: List[dict]) -> Dict[str, Any]:
    gemini_client = get_gemini_client()
    
    if not gemini_client:
        return {
            'success': False,
            'error': 'GEMINI_API_KEY not configured. Please add your Gemini API key to use AI recommendations.',
            'fallback_recommendations': generate_fallback_recommendations(tanks_data)
        }
    
    try:
        from google.genai import types
        
        tanks_summary = []
        for tank in tanks_data:
            readings = tank.get('current_readings', {})
            tanks_summary.append({
                'name': tank.get('name', 'Unknown'),
                'id': tank.get('id', ''),
                'status': tank.get('status', 'unknown'),
                'ph': readings.get('ph', 7.0),
                'turbidity': readings.get('turbidity', 0),
                'temperature': readings.get('temperature', 20),
                'days_since_cleaned': tank.get('days_since_cleaned', 0),
                'days_until_maintenance': tank.get('days_until_maintenance', 0),
                'current_level_percent': tank.get('current_level_percent', 0)
            })
        
        prompt = f"""You are an expert water quality management AI assistant for AquaSentry Live, a water tank monitoring system.

Analyze the following water tank data and provide actionable recommendations:

{json.dumps(tanks_summary, indent=2)}

Based on this data, provide:
1. **Risk Assessment**: Identify tanks at highest risk and explain why
2. **Immediate Actions**: List urgent actions needed for critical tanks
3. **Water Quality Advice**: Specific advice to improve water quality for problematic tanks
4. **Maintenance Optimization**: Suggest optimal cleaning schedules based on current conditions
5. **Trend Forecast**: Predict potential issues based on current readings

Water Quality Standards Reference:
- pH: Ideal range 6.5-8.5 (critical if <6.0 or >9.0)
- Turbidity: Ideal <1 NTU, warning >3 NTU, critical >5 NTU
- Temperature: Ideal 15-22°C
- Cleaning: Should be done every 30 days maximum

Format your response as a structured JSON with these keys:
- risk_assessment: array of objects with tank_name, risk_level, and reason
- immediate_actions: array of strings
- water_quality_advice: array of objects with tank_name and advice
- maintenance_schedule: array of objects with tank_name, recommended_action, and priority
- trend_forecast: string with overall system forecast
- overall_health_score: number from 0-100
"""

        response = gemini_client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json"
            )
        )
        
        if response.text:
            try:
                result = json.loads(response.text)
                return {
                    'success': True,
                    'recommendations': result
                }
            except json.JSONDecodeError:
                return {
                    'success': True,
                    'recommendations': {
                        'raw_response': response.text
                    }
                }
        else:
            return {
                'success': False,
                'error': 'Empty response from AI'
            }
            
    except Exception as e:
        logging.error(f"AI recommendation error: {str(e)}")
        return {
            'success': False,
            'error': str(e),
            'fallback_recommendations': generate_fallback_recommendations(tanks_data)
        }


def generate_fallback_recommendations(tanks_data: List[dict]) -> Dict[str, Any]:
    critical_tanks = []
    warning_tanks = []
    immediate_actions = []
    
    for tank in tanks_data:
        readings = tank.get('current_readings', {})
        ph = readings.get('ph', 7.0)
        turbidity = readings.get('turbidity', 0)
        days_since_cleaned = tank.get('days_since_cleaned', 0)
        
        issues = []
        if ph < 6.5 or ph > 8.5:
            issues.append(f"pH imbalance ({ph})")
        if turbidity > 5:
            issues.append(f"High turbidity ({turbidity} NTU)")
        if days_since_cleaned > 30:
            issues.append(f"Overdue cleaning ({days_since_cleaned} days)")
        
        if len(issues) >= 2 or turbidity > 7 or ph < 6.0 or ph > 9.0:
            critical_tanks.append({
                'tank_name': tank.get('name', 'Unknown'),
                'issues': issues
            })
            for issue in issues:
                immediate_actions.append(f"{tank.get('name')}: Address {issue}")
        elif issues:
            warning_tanks.append({
                'tank_name': tank.get('name', 'Unknown'),
                'issues': issues
            })
    
    return {
        'risk_assessment': [
            {'tank_name': t['tank_name'], 'risk_level': 'critical', 'reason': ', '.join(t['issues'])}
            for t in critical_tanks
        ] + [
            {'tank_name': t['tank_name'], 'risk_level': 'warning', 'reason': ', '.join(t['issues'])}
            for t in warning_tanks
        ],
        'immediate_actions': immediate_actions,
        'water_quality_advice': [],
        'maintenance_schedule': [],
        'trend_forecast': 'Analysis based on rule-based fallback system',
        'overall_health_score': max(0, 100 - (len(critical_tanks) * 20) - (len(warning_tanks) * 10))
    }
