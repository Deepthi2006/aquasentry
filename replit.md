# AquaSentry Live - AI-Powered Water Tank Monitoring System

## Overview
AquaSentry Live is a comprehensive water tank monitoring system designed for Indian government water utilities. It features real-time monitoring, AI-powered predictions, and compliance with BIS standards and Jal Jeevan Mission guidelines.

## Recent Changes (December 2025)
- Added 10 new AI-powered features using Google Gemini API
- Implemented AquaCopilot AI chatbot for officer queries
- Added Vision AI for water contamination detection
- Created GIS ward-level heatmaps with GeoJSON support
- Implemented offline-first PWA mode for rural deployment

## Architecture

```
AquaSentry Live v2.0
=====================

┌─────────────────────────────────────────────────────────────────────────┐
│                          FRONTEND (HTML/JS/CSS)                        │
├─────────────────────────────────────────────────────────────────────────┤
│  dashboard.html │ alerts.html │ copilot.html │ vision.html │ map.html  │
│  maintenance.html │ recommendations.html │ login.html │ index.html     │
├─────────────────────────────────────────────────────────────────────────┤
│                    PWA Service Worker (sw.js)                          │
│              Offline caching, background sync                          │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                         FastAPI BACKEND (Python)                        │
├─────────────────────────────────────────────────────────────────────────┤
│  backend/main.py - API Routes & Endpoints                              │
├─────────────────────────────────────────────────────────────────────────┤
│                           SERVICES LAYER                                │
├──────────────────┬──────────────────┬───────────────────────────────────┤
│ Core Services    │ AI Services      │ New AI Features                   │
├──────────────────┼──────────────────┼───────────────────────────────────┤
│ tank_service.py  │ ai_service.py    │ ai_prediction_service.py          │
│ map_service.py   │                  │ ai_copilot_service.py             │
│ auth_service.py  │                  │ vision_ai_service.py              │
│ analytics_svc.py │                  │ gis_service.py                    │
└──────────────────┴──────────────────┴───────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                         GOOGLE GEMINI API                               │
│  - Text generation (gemini-2.5-flash)                                  │
│  - Vision analysis (image contamination detection)                     │
│  - JSON structured outputs                                              │
└─────────────────────────────────────────────────────────────────────────┘
```

## New API Endpoints (v2.0)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/ai/predict/{tank_id}` | GET | AI water quality prediction (24-48hr) |
| `/api/ai/leakage/{tank_id}` | GET | Leakage/overflow detection |
| `/api/ai/maintenance/{tank_id}` | GET | Predictive maintenance scheduling |
| `/api/ai/copilot` | POST | AquaCopilot AI chatbot |
| `/api/ai/vision/water` | POST | Vision AI water analysis |
| `/api/ai/vision/infrastructure` | POST | Infrastructure inspection |
| `/api/gis/wards` | GET | Ward-level GeoJSON data |
| `/api/gis/heatmap` | GET | Heatmap data by metric |
| `/api/ai/demand-forecast` | GET | Water demand forecasting |
| `/api/ai/rainwater` | GET | Rainwater harvesting analysis |
| `/api/ai/explain-alert/{alert_id}` | GET | Explainable AI alerts |
| `/api/offline-data` | GET | Offline data bundle |
| `/manifest.json` | GET | PWA manifest |

## 10 AI Features Implemented

### 1. AI Water Quality Prediction
- 24-48 hour forecasting for pH, turbidity, temperature
- Trend analysis and risk assessment
- Confidence scoring

### 2. AI Leakage/Overflow Detection
- Anomaly detection for water level patterns
- Estimated loss calculation
- Government alert triggering

### 3. AI Predictive Maintenance Scheduler
- Recommended cleaning dates based on water quality
- BIS and Jal Jeevan Mission compliance
- Cost estimation in INR

### 4. AquaCopilot AI Chatbot
- Natural language queries about tank status
- Alert interpretation and recommendations
- Report generation assistance

### 5. Vision AI Water Contamination Detection
- Image upload for water sample analysis
- Visual contamination indicators
- Safety assessment (drinking/domestic use)

### 6. GIS Ward-Level Heatmaps
- GeoJSON layer support on Leaflet map
- Health score visualization
- Ward-level aggregation

### 7. Rainwater Harvesting Predictor
- Overflow capacity analysis
- Monsoon readiness scoring
- Cost-benefit analysis in INR

### 8. Water Demand Forecasting
- 7-day consumption prediction
- Peak hour identification
- Supply adequacy assessment

### 9. Explainable AI Alerts
- Root cause analysis
- Recommended actions with priorities
- Plain language summaries

### 10. Offline-first PWA Mode
- Service worker with caching
- IndexedDB for offline data
- Background sync when online

## Government Use Cases (India)

1. **BIS Compliance**: Automated monitoring against IS 10500 standards
2. **Jal Jeevan Mission**: Tracking rural water supply targets
3. **CPHEEO Guidelines**: Maintenance scheduling compliance
4. **Swachh Bharat**: Water quality reporting for Gram Panchayats
5. **Disaster Response**: Rapid water quality assessment during emergencies

## Environment Variables

- `GEMINI_API_KEY` - Google AI API key for Gemini (required for AI features)
- `SESSION_SECRET` - Session encryption key

## Running the Application

The application runs on port 5000 with FastAPI/Uvicorn:
```bash
python -m backend.main
```

## File Structure

```
/
├── backend/
│   ├── main.py                    # FastAPI app with all routes
│   ├── services/
│   │   ├── ai_prediction_service.py  # Prediction, leakage, maintenance
│   │   ├── ai_copilot_service.py     # Chatbot & explainable alerts
│   │   ├── vision_ai_service.py      # Image analysis
│   │   ├── gis_service.py            # GeoJSON & heatmaps
│   │   ├── tank_service.py           # Tank data management
│   │   ├── map_service.py            # Map markers
│   │   ├── analytics_service.py      # Analytics
│   │   ├── auth_service.py           # Authentication
│   │   └── ai_service.py             # Original recommendations
│   ├── data/
│   │   ├── data.json                 # Tank data
│   │   └── users.json                # User credentials
│   ├── models/                       # Pydantic models
│   └── utils/                        # Utilities
├── frontend/
│   ├── css/styles.css
│   ├── js/
│   │   ├── api.js
│   │   ├── ai-features.js           # New AI API functions
│   │   ├── auth.js
│   │   ├── dashboard.js
│   │   └── ...
│   ├── dashboard.html
│   ├── copilot.html                 # AquaCopilot chat interface
│   ├── vision.html                  # Vision AI upload interface
│   ├── sw.js                        # Service worker for PWA
│   ├── offline.html                 # Offline fallback page
│   └── ...
└── replit.md                        # This file
```
