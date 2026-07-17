# f1-strategy-pipeline

A comprehensive, data-driven pipeline for Formula 1 race strategy simulation and optimization. This end-to-end system integrates real-world F1 telemetry, advanced tire degradation modeling, and sophisticated simulation algorithms to deliver actionable race strategy insights through an interactive dashboard.

The pipeline transforms raw timing data into optimal race strategies, allowing engineers and analysts to explore "what-if" scenarios, compare tire compounds, and identify winning pit-stop strategies under varying race conditions.

---

## 🎯 Project Goals
- Build a modular, production-ready F1 strategy simulation engine
- Integrate real F1 telemetry data (via FastF1 API) for accurate modeling
- Implement advanced tire degradation and fuel effect models using scientific curve fitting
- Develop a high-performance simulation framework capable of testing thousands of strategies per race
- Create a modern, interactive dashboard for strategy visualization and analysis
- Provide a robust data pipeline with PostgreSQL persistence and Docker containerization
- Build an extensible architecture for adding weather, traffic, and safety car dynamics

---

## 🧠 How the Project Works
### 1. Data Ingestion & Storage
- FastF1 API Integration: Automatically fetches real F1 session data (lap times, telemetry, weather)
- PostgreSQL Database: Persists all raw and processed data for historical analysis
- SQL Schema: Optimized relational schema for race, driver, lap, and tire data
- Docker Deployment: Full containerization for easy setup and reproducibility

### 2. Performance Modeling
- Tire Degradation Curves: Fits exponential/polynomial degradation models per compound (Soft, Medium, Hard, Intermediate, Wet)
- Fuel Load Effect: Calculates lap time penalty based on fuel weight and consumption rates
- Stint Analysis: Computes average lap times, consistency metrics, and tire wear rates
- Track Characteristics: Incorporates track-specific data (length, corners, surface grip)
