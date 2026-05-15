# GitReady API Bridge Documentation

## Overview

The `api_bridge.py` file is a production-ready FastAPI backend that serves as the RESTful API entry point for the GitReady application. It implements the exact specifications defined in `openapi.json` and `mcp-tools-config.json`, enabling watsonx Orchestrate to programmatically execute multi-step analysis workflows and interview loop operations.

## Architecture

### Design Principles

1. **Separation of Concerns**: API routing layer is completely separate from business logic (in `app.py`)
2. **Independence from UI**: No dependencies on Streamlit - can run standalone
3. **Standards Compliance**: Implements OpenAPI 3.0.3 specification exactly
4. **MCP Tool Compatibility**: Exposes endpoints matching MCP tool definitions
5. **Production Ready**: Includes authentication, CORS, logging, error handling, and monitoring

### Key Components

```
api_bridge.py
├── Enums (Status types, difficulty levels, etc.)
├── Pydantic Models (Request/Response schemas)
├── Security & Authentication (API Key + Bearer Token)
├── FastAPI Application Setup
├── Middleware (CORS, Logging, Error Handling)
├── Utility Functions (ID generation, scoring)
├── API Endpoints (7 endpoints across 4 tags)
└── Application Lifecycle (Startup/Shutdown)
```

## Installation

### Prerequisites

- Python 3.8+
- IBM Watsonx.ai credentials
- Git installed on system

### Install Dependencies

```bash
pip install -r requirements.txt
```

The following packages are required:
- `fastapi>=0.104.0` - Web framework
- `uvicorn[standard]>=0.24.0` - ASGI server
- `pydantic>=2.0.0` - Data validation
- `python-multipart>=0.0.6` - Form data support

## Configuration

### Environment Variables

```bash
# Required - IBM Watsonx.ai Credentials
export WATSONX_API_KEY="your_api_key_here"
export WATSONX_PROJECT_ID="your_project_id_here"
export WATSONX_URL="https://us-south.ml.cloud.ibm.com"  # Optional, defaults to US South

# Optional - API Security
export API_KEYS="key1,key2,key3"  # Comma-separated API keys for authentication

# Optional - Server Configuration
export HOST="0.0.0.0"  # Default: 0.0.0.0
export PORT="8000"     # Default: 8000
export DEBUG="false"   # Enable auto-reload in development
export LOG_LEVEL="info"  # Logging level: debug, info, warning, error

# Optional - CORS Configuration
export CORS_ORIGINS="http://localhost:3000,https://app.example.com"  # Default: *
```

### Windows PowerShell

```powershell
$env:WATSONX_API_KEY="your_api_key_here"
$env:WATSONX_PROJECT_ID="your_project_id_here"
$env:API_KEYS="dev-key-123,prod-key-456"
```

## Running the API

### Development Mode

```bash
# With auto-reload
python api_bridge.py

# Or using uvicorn directly
uvicorn api_bridge:app --reload --host 0.0.0.0 --port 8000
```

### Production Mode

```bash
# Using uvicorn with workers
uvicorn api_bridge:app --host 0.0.0.0 --port 8000 --workers 4

# Or with gunicorn (recommended for production)
gunicorn api_bridge:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

### Docker Deployment

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app.py api_bridge.py ./

ENV HOST=0.0.0.0
ENV PORT=8000

EXPOSE 8000

CMD ["uvicorn", "api_bridge:app", "--host", "0.0.0.0", "--port", "8000"]
```

## API Endpoints

### Base URL

- **Local Development**: `http://localhost:8000/v1`
- **Production**: `https://api.gitready.example.com/v1`

### Authentication

All endpoints (except `/health`) require authentication using one of:

1. **API Key Header**:
   ```
   X-API-Key: your-api-key-here
   ```

2. **Bearer Token**:
   ```
   Authorization: Bearer your-api-key-here
   ```

**Note**: If no `API_KEYS` environment variable is set, the API runs in development mode without authentication.

### Endpoint Reference

#### 1. Health Check

```http
GET /v1/health
```

**Response**:
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "timestamp": "2026-05-15T18:30:00.000Z",
  "watsonx_configured": true,
  "dependencies": {
    "watsonx": "configured",
    "git": "available",
    "storage": "in_memory"
  }
}
```

#### 2. Analyze Repository

```http
POST /v1/analyze/repository
Content-Type: application/json
X-API-Key: your-api-key
```

**Request Body**:
```json
{
  "repository_url": "https://github.com/username/repository",
  "analysis_depth": "standard",
  "include_dependencies": false,
  "max_file_size_mb": 1.0,
  "max_total_size_mb": 10.0
}
```

**Response**:
```json
{
  "analysis_id": "ana_a1b2c3d4e5f6g7h8",
  "repository_url": "https://github.com/username/repository",
  "repository_name": "repository",
  "status": "completed",
  "metadata": {
    "total_files": 42,
    "total_size_bytes": 524288,
    "token_count": 15000,
    "chunks_processed": 0
  },
  "created_at": "2026-05-15T18:30:00.000Z",
  "completed_at": "2026-05-15T18:30:05.000Z",
  "processing_time_ms": 5000
}
```

#### 3. Assess Code Quality

```http
POST /v1/analyze/code-quality
Content-Type: application/json
X-API-Key: your-api-key
```

**Request Body**:
```json
{
  "analysis_id": "ana_a1b2c3d4e5f6g7h8",
  "quality_checks": ["complexity", "security", "best_practices"],
  "severity_threshold": "medium",
  "include_suggestions": true
}
```

**Response**:
```json
{
  "analysis_id": "ana_a1b2c3d4e5f6g7h8",
  "quality_score": 85.5,
  "grade": "B+",
  "metrics": {
    "complexity": {
      "average_cyclomatic_complexity": 4.2,
      "max_cyclomatic_complexity": 15,
      "high_complexity_functions": 3
    },
    "maintainability": {
      "maintainability_index": 85.5,
      "code_duplication_percentage": 5.0
    },
    "security": {
      "vulnerabilities_found": 2,
      "critical": 0,
      "high": 1,
      "medium": 1
    }
  },
  "issues": [...],
  "recommendations": [...]
}
```

#### 4. Generate Interview Materials

```http
POST /v1/interview/generate
Content-Type: application/json
X-API-Key: your-api-key
```

**Request Body**:
```json
{
  "analysis_id": "ana_a1b2c3d4e5f6g7h8",
  "candidate_experience_level": "mid",
  "number_of_questions": 10,
  "question_difficulty": "mixed",
  "interview_format": "comprehensive",
  "include_non_technical": true,
  "include_weaknesses": true,
  "include_elevator_pitch": true
}
```

**Response**:
```json
{
  "interview_id": "int_x9y8z7w6v5u4t3s2",
  "analysis_id": "ana_a1b2c3d4e5f6g7h8",
  "status": "completed",
  "technical_questions": [...],
  "non_technical_explanation": "...",
  "code_weaknesses": {...},
  "elevator_pitch": "...",
  "created_at": "2026-05-15T18:30:00.000Z",
  "generation_time_ms": 45000
}
```

#### 5. Generate Technical Questions Only

```http
POST /v1/interview/questions
Content-Type: application/json
X-API-Key: your-api-key
```

**Request Body**:
```json
{
  "analysis_id": "ana_a1b2c3d4e5f6g7h8",
  "number_of_questions": 5,
  "difficulty": "hard",
  "include_follow_ups": true,
  "include_scoring_rubric": true
}
```

#### 6. Get Analysis by ID

```http
GET /v1/analysis/{analysis_id}
X-API-Key: your-api-key
```

#### 7. Get Interview by ID

```http
GET /v1/interview/{interview_id}
X-API-Key: your-api-key
```

## Interactive Documentation

FastAPI automatically generates interactive API documentation:

- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`
- **OpenAPI JSON**: `http://localhost:8000/openapi.json`

## Watsonx Orchestrate Integration

### Multi-Step Workflow Example

```python
# Step 1: Analyze Repository
analysis_response = requests.post(
    "http://localhost:8000/v1/analyze/repository",
    headers={"X-API-Key": "your-key"},
    json={"repository_url": "https://github.com/user/repo"}
)
analysis_id = analysis_response.json()["analysis_id"]

# Step 2: Assess Code Quality
quality_response = requests.post(
    "http://localhost:8000/v1/analyze/code-quality",
    headers={"X-API-Key": "your-key"},
    json={"analysis_id": analysis_id}
)

# Step 3: Generate Interview Materials
interview_response = requests.post(
    "http://localhost:8000/v1/interview/generate",
    headers={"X-API-Key": "your-key"},
    json={
        "analysis_id": analysis_id,
        "number_of_questions": 10
    }
)
```

### MCP Tool Mapping

| MCP Tool | API Endpoint | Method |
|----------|--------------|--------|
| `analyze_github_repository` | `/v1/analyze/repository` | POST |
| `assess_code_quality` | `/v1/analyze/code-quality` | POST |
| `generate_interview_materials` | `/v1/interview/generate` | POST |
| `generate_technical_questions` | `/v1/interview/questions` | POST |

## Error Handling

### Error Response Format

```json
{
  "error": "HTTP_404",
  "message": "Analysis ana_xyz123 not found",
  "detail": null,
  "timestamp": "2026-05-15T18:30:00.000Z",
  "path": "/v1/analysis/ana_xyz123"
}
```

### HTTP Status Codes

- `200` - Success
- `400` - Bad Request (invalid input)
- `401` - Unauthorized (missing/invalid API key)
- `404` - Not Found (resource doesn't exist)
- `422` - Validation Error (Pydantic validation failed)
- `500` - Internal Server Error

## Monitoring & Logging

### Request Logging

Every request is logged with:
- HTTP method and path
- Response status code
- Processing time in milliseconds

Example log output:
```
2026-05-15 18:30:00 - api_bridge - INFO - Request: POST /v1/analyze/repository
2026-05-15 18:30:05 - api_bridge - INFO - Response: 200 - 5000.00ms
```

### Custom Headers

All responses include:
- `X-Process-Time`: Processing time in milliseconds

### Health Monitoring

Use the `/v1/health` endpoint for:
- Kubernetes liveness/readiness probes
- Load balancer health checks
- Monitoring systems (Prometheus, Datadog, etc.)

## Storage

### Current Implementation

- **In-Memory Storage**: Analysis and interview results stored in Python dictionaries
- **Limitations**: Data lost on restart, not suitable for production at scale

### Production Recommendations

Replace in-memory storage with:

1. **PostgreSQL/MySQL**: For structured data with relationships
2. **MongoDB**: For flexible document storage
3. **Redis**: For caching and session management
4. **S3/Cloud Storage**: For large analysis results

Example database integration:
```python
# Replace this:
analysis_store[analysis_id] = {...}

# With this:
await db.analyses.insert_one({
    "_id": analysis_id,
    "data": {...},
    "created_at": datetime.utcnow()
})
```

## Security Best Practices

### Production Deployment

1. **Use HTTPS**: Always use TLS/SSL in production
2. **Rotate API Keys**: Implement key rotation policy
3. **Rate Limiting**: Add rate limiting middleware
4. **Input Validation**: Pydantic handles this automatically
5. **CORS Configuration**: Restrict origins in production
6. **Secrets Management**: Use AWS Secrets Manager, HashiCorp Vault, etc.

### Example Rate Limiting

```python
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

@app.post("/v1/analyze/repository")
@limiter.limit("10/minute")
async def analyze_repository(...):
    ...
```

## Testing

### Unit Tests

```python
from fastapi.testclient import TestClient
from api_bridge import app

client = TestClient(app)

def test_health_check():
    response = client.get("/v1/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

def test_analyze_repository():
    response = client.post(
        "/v1/analyze/repository",
        json={"repository_url": "https://github.com/test/repo"}
    )
    assert response.status_code == 200
    assert "analysis_id" in response.json()
```

### Integration Tests

```bash
# Install pytest
pip install pytest pytest-asyncio httpx

# Run tests
pytest tests/test_api_bridge.py -v
```

## Performance Optimization

### Async Operations

The API uses async/await for non-blocking I/O:
- Repository cloning runs in background
- Multiple requests can be processed concurrently
- Watsonx API calls don't block other requests

### Caching Strategy

Implement caching for:
- Analysis results (TTL: 1 hour)
- Code quality assessments (TTL: 30 minutes)
- Interview materials (TTL: 24 hours)

```python
from functools import lru_cache

@lru_cache(maxsize=100)
def get_cached_analysis(analysis_id: str):
    return analysis_store.get(analysis_id)
```

## Troubleshooting

### Common Issues

1. **Import Errors**: Ensure all dependencies installed
   ```bash
   pip install -r requirements.txt
   ```

2. **Watsonx Credentials**: Check environment variables
   ```bash
   echo $WATSONX_API_KEY
   echo $WATSONX_PROJECT_ID
   ```

3. **Port Already in Use**: Change port
   ```bash
   export PORT=8001
   python api_bridge.py
   ```

4. **CORS Errors**: Configure allowed origins
   ```bash
   export CORS_ORIGINS="http://localhost:3000"
   ```

## Contributing

When modifying the API:

1. Update Pydantic models to match OpenAPI schema
2. Add comprehensive docstrings to endpoints
3. Update this README with new endpoints
4. Test with both Swagger UI and curl
5. Ensure backward compatibility

## License

MIT License - See LICENSE file for details

## Support

- **Issues**: https://github.com/gitready/gitready/issues
- **Email**: support@gitready.example.com
- **Documentation**: https://docs.gitready.example.com

---

**Built for IBM Bob Hackathon** | Powered by IBM Watsonx.ai & FastAPI