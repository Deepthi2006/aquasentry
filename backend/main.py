from fastapi import FastAPI, HTTPException, Query, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Optional, List
import os

from backend.services.tank_service import (
    get_all_tanks_with_status,
    get_single_tank,
    get_tank_history,
    get_tanks_summary
)
from backend.services.analytics_service import (
    analyze_water_quality,
    get_system_analytics,
    get_trend_analysis
)
from backend.services.ai_service import generate_recommendations
from backend.services.map_service import get_map_data
from backend.services.auth_service import authenticate_user, validate_token, logout
from backend.utils.json_loader import get_alerts, reload_data, update_maintenance

from backend.services.ai_prediction_service import (
    predict_water_quality,
    detect_leakage_overflow,
    predict_maintenance_schedule,
    forecast_water_demand,
    predict_rainwater_harvesting
)
from backend.services.ai_copilot_service import (
    chat_with_copilot,
    generate_explainable_alert
)
from backend.services.vision_ai_service import (
    analyze_water_image,
    analyze_tank_infrastructure
)
from backend.services.gis_service import (
    get_ward_geojson,
    get_heatmap_data,
    get_ward_details
)


class LoginRequest(BaseModel):
    username: str
    password: str


class MaintenanceRequest(BaseModel):
    tank_id: str
    cleaned_date: str
    notes: Optional[str] = None


class CopilotRequest(BaseModel):
    query: str
    context: Optional[str] = ""


app = FastAPI(
    title="AquaSentry Live API",
    description="Water Tank Monitoring System with AI-Powered Recommendations - Enhanced with 10 AI Features",
    version="2.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

frontend_path = os.path.join(os.path.dirname(__file__), '..', 'frontend')
app.mount("/static", StaticFiles(directory=frontend_path), name="static")


@app.get("/")
async def root():
    return FileResponse(os.path.join(frontend_path, 'index.html'))


@app.get("/login")
async def login_page():
    return FileResponse(os.path.join(frontend_path, 'login.html'))


@app.get("/dashboard")
async def dashboard():
    return FileResponse(os.path.join(frontend_path, 'dashboard.html'))


@app.get("/alerts")
async def alerts_page():
    return FileResponse(os.path.join(frontend_path, 'alerts.html'))


@app.get("/recommendations")
async def recommendations_page():
    return FileResponse(os.path.join(frontend_path, 'recommendations.html'))


@app.get("/map")
async def map_page():
    return FileResponse(os.path.join(frontend_path, 'map.html'))


@app.get("/maintenance")
async def maintenance_page():
    return FileResponse(os.path.join(frontend_path, 'maintenance.html'))


@app.get("/copilot")
async def copilot_page():
    return FileResponse(os.path.join(frontend_path, 'copilot.html'))


@app.get("/vision")
async def vision_page():
    return FileResponse(os.path.join(frontend_path, 'vision.html'))


@app.get("/api/tanks")
async def get_tanks():
    tanks = get_all_tanks_with_status()
    summary = get_tanks_summary()
    return {
        "tanks": tanks,
        "summary": summary
    }


@app.get("/api/tanks/{tank_id}")
async def get_tank(tank_id: str):
    tank = get_single_tank(tank_id)
    if not tank:
        raise HTTPException(status_code=404, detail="Tank not found")
    
    analysis = analyze_water_quality(tank)
    trend = get_trend_analysis(tank_id)
    
    return {
        "tank": tank,
        "analysis": analysis,
        "trend": trend
    }


@app.get("/api/tanks/{tank_id}/history")
async def get_history(tank_id: str):
    history = get_tank_history(tank_id)
    if history is None:
        raise HTTPException(status_code=404, detail="Tank not found")
    return {"history": history}


@app.get("/api/alerts")
async def get_all_alerts():
    alerts = get_alerts()
    critical = [a for a in alerts if a['type'] == 'critical']
    warnings = [a for a in alerts if a['type'] == 'warning']
    info = [a for a in alerts if a['type'] == 'info']
    
    return {
        "alerts": alerts,
        "summary": {
            "total": len(alerts),
            "critical": len(critical),
            "warning": len(warnings),
            "info": len(info),
            "unacknowledged": len([a for a in alerts if not a.get('acknowledged', False)])
        }
    }


@app.get("/api/map")
async def get_map():
    return get_map_data()


@app.get("/api/analytics")
async def get_analytics():
    return get_system_analytics()


@app.post("/api/recommendations")
async def get_ai_recommendations():
    tanks = get_all_tanks_with_status()
    result = generate_recommendations(tanks)
    return result


@app.post("/api/reload")
async def reload():
    reload_data()
    return {"status": "Data reloaded successfully"}


@app.post("/api/auth/login")
async def api_login(request: LoginRequest):
    result = authenticate_user(request.username, request.password)
    if not result["success"]:
        raise HTTPException(status_code=401, detail=result["error"])
    return result


@app.post("/api/auth/logout")
async def api_logout(token: str = Query("")):
    return logout(token)


@app.get("/api/auth/validate")
async def api_validate(token: str = Query("")):
    return validate_token(token)


@app.post("/api/maintenance/update")
async def api_update_maintenance(request: MaintenanceRequest):
    result = update_maintenance(request.tank_id, request.cleaned_date, request.notes or "")
    if not result["success"]:
        raise HTTPException(status_code=404, detail=result.get("error", "Update failed"))
    return result


@app.get("/api/ai/predict/{tank_id}")
async def api_predict_water_quality(tank_id: str):
    tank = get_single_tank(tank_id)
    if not tank:
        raise HTTPException(status_code=404, detail="Tank not found")
    
    history = get_tank_history(tank_id) or []
    result = predict_water_quality(tank, history)
    return result


@app.get("/api/ai/leakage/{tank_id}")
async def api_detect_leakage(tank_id: str):
    tank = get_single_tank(tank_id)
    if not tank:
        raise HTTPException(status_code=404, detail="Tank not found")
    
    history = get_tank_history(tank_id) or []
    result = detect_leakage_overflow(tank, history)
    return result


@app.get("/api/ai/maintenance/{tank_id}")
async def api_predict_maintenance(tank_id: str):
    tank = get_single_tank(tank_id)
    if not tank:
        raise HTTPException(status_code=404, detail="Tank not found")
    
    history = get_tank_history(tank_id) or []
    result = predict_maintenance_schedule(tank, history)
    return result


@app.post("/api/ai/copilot")
async def api_copilot_chat(request: CopilotRequest):
    tanks = get_all_tanks_with_status()
    alerts = get_alerts()
    result = chat_with_copilot(request.query, tanks, alerts, request.context or "")
    return result


@app.post("/api/ai/vision/water")
async def api_vision_water_analysis(
    file: UploadFile = File(...),
    tank_id: Optional[str] = Form(None)
):
    if not file.content_type or not file.content_type.startswith('image/'):
        raise HTTPException(status_code=400, detail="File must be an image")
    
    image_bytes = await file.read()
    
    tank_context = None
    if tank_id:
        tank_context = get_single_tank(tank_id)
    
    result = analyze_water_image(image_bytes, file.content_type, tank_context)
    return result


@app.post("/api/ai/vision/infrastructure")
async def api_vision_infrastructure(file: UploadFile = File(...)):
    if not file.content_type or not file.content_type.startswith('image/'):
        raise HTTPException(status_code=400, detail="File must be an image")
    
    image_bytes = await file.read()
    result = analyze_tank_infrastructure(image_bytes, file.content_type)
    return result


@app.get("/api/gis/wards")
async def api_get_ward_geojson():
    return get_ward_geojson()


@app.get("/api/gis/heatmap")
async def api_get_heatmap(metric: str = Query("health_score")):
    return get_heatmap_data(metric)


@app.get("/api/gis/wards/{ward_id}")
async def api_get_ward_details(ward_id: str):
    result = get_ward_details(ward_id)
    if not result["success"]:
        raise HTTPException(status_code=404, detail="Ward not found")
    return result


@app.get("/api/ai/demand-forecast")
async def api_forecast_demand():
    tanks = get_all_tanks_with_status()
    result = forecast_water_demand(tanks)
    return result


@app.get("/api/ai/rainwater")
async def api_rainwater_harvesting():
    tanks = get_all_tanks_with_status()
    result = predict_rainwater_harvesting(tanks)
    return result


@app.get("/api/ai/explain-alert/{alert_id}")
async def api_explain_alert(alert_id: str):
    alerts = get_alerts()
    alert = next((a for a in alerts if a.get('id') == alert_id), None)
    
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    
    tank_id = alert.get('tank_id')
    tank = get_single_tank(tank_id) if tank_id else None
    history = get_tank_history(tank_id) if tank_id else []
    
    result = generate_explainable_alert(alert, tank or {}, history or [])
    return result


@app.get("/manifest.json")
async def get_manifest():
    return {
        "name": "AquaSentry Live",
        "short_name": "AquaSentry",
        "description": "AI-Powered Water Tank Monitoring System for Government Utilities",
        "start_url": "/dashboard",
        "display": "standalone",
        "background_color": "#0ea5e9",
        "theme_color": "#0ea5e9",
        "icons": [
            {
                "src": "/static/icons/icon-192.png",
                "sizes": "192x192",
                "type": "image/png"
            },
            {
                "src": "/static/icons/icon-512.png",
                "sizes": "512x512",
                "type": "image/png"
            }
        ]
    }


@app.get("/api/offline-data")
async def get_offline_data():
    tanks = get_all_tanks_with_status()
    alerts = get_alerts()
    map_data = get_map_data()
    
    return {
        "tanks": tanks,
        "alerts": alerts,
        "map": map_data,
        "timestamp": "2025-12-08T12:00:00Z",
        "offline_capable": True
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5000)
