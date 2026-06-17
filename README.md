# GPU-Accelerated PSO Sensor Placement Optimizer

A full-stack engineering tool that solves the **Wireless Sensor Network (WSN) deployment problem** — finding the optimal positions for N sensors across a 2D field to maximize coverage, energy efficiency, and connectivity simultaneously.

## Architecture

The project follows a strict layered architecture:
`Router -> Controller -> Service -> Core (Algorithms)`

### Backend Structure
- **Routers**: Routing only.
- **Controllers**: Request/Response handling.
- **Services**: Business logic.
- **Core**: Pure algorithms (PSO CPU/GPU, Fitness, etc.).

## Tech Stack
- **Backend**: Python 3.11, FastAPI, Numba (CUDA), NumPy
- **Frontend**: React, Tailwind CSS, Zustand, D3.js / HTML Canvas, Recharts

## Local Setup

```bash
docker-compose up
```

## API Reference
- `POST /api/v1/optimize` - Run PSO Optimization
- `GET /api/v1/optimize/{job_id}/status` - Check job status
- `GET /api/v1/optimize/{job_id}/result` - Get job result
- `POST /api/v1/compare` - Compare strategies (Random, Grid, PSO, PSO-VDCOA)
- `POST /api/v1/fault-inject` - Simulate sensor failures
- `GET /api/v1/health` - API Health check

## Benchmark Results
(To be updated during implementation)

## Future Improvements
- DRL Adaptive Redeployment
- Multi-GPU Support
- Real Hardware Validation
