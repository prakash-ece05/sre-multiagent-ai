# SRE Multi-Agent AI System - Complete Setup Guide

## Quick Start (5 minutes)

```bash
# 1. Clone repository
git clone https://github.com/yourusername/sre-multiagent-ai.git
cd sre-multiagent-ai

# 2. Create virtual environment
python3.11 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment
cp .env.example .env
# Edit .env with your credentials

# 5. Run the application
streamlit run app.py
```

## Detailed Setup

### Prerequisites

- Python 3.11 or higher
- pip and virtualenv
- Access to:
  - Google Cloud account (for Gemini API)
  - Grafana instance with Prometheus and Tempo
  - Apollo Router (for failover features)
  - Harness (for deployment tracking)

### Step 1: Install Python Dependencies

```bash
pip install -r requirements.txt
```

**Core dependencies:**
- `google-genai==0.2.0` - Gemini AI integration
- `google-adk==0.2.0` - Agent Development Kit
- `streamlit==1.28.0` - Web UI framework
- `requests==2.31.0` - HTTP client
- `python-dotenv==1.0.0` - Environment variable management

### Step 2: Configure API Access

#### 2.1 Google Gemini API

1. Go to [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Create a new API key
3. Add to `.env`:
   ```
   GOOGLE_API_KEY=your_api_key_here
   ```

#### 2.2 Grafana Configuration

1. In Grafana, create an API token:
   - Settings → API Keys → New API Key
   - Role: Admin or Editor
   - Add to `.env`:
     ```
     GRAFANA_URL=https://your-grafana.com
     GRAFANA_API_TOKEN=your_token_here
     ```

2. Get Datasource IDs:
   - Go to Configuration → Data Sources
   - Note the ID from the URL for Prometheus and Tempo
   - Add to `.env`:
     ```
     PROMETHEUS_DATASOURCE_ID=2
     TEMPO_DATASOURCE_ID=3
     ```

#### 2.3 Apollo Router Configuration

1. Obtain admin API key from Apollo Router configuration
2. Add to `.env`:
   ```
   APOLLO_ROUTER_URL=https://your-apollo-router.com
   APOLLO_ADMIN_API_KEY=your_admin_key
   ```

#### 2.4 Harness Configuration

1. In Harness, generate API key:
   - Profile → API Keys → New API Key
2. Get account ID from URL or settings
3. Add to `.env`:
   ```
   HARNESS_URL=https://app.harness.io
   HARNESS_API_KEY=your_api_key
   HARNESS_ACCOUNT_ID=your_account_id
   ```

### Step 3: Configure Applications and KPIs

Edit `config/applications.py` to define your applications:

```python
APPLICATION_KPIS = {
    "your-app": {
        "business": {
            "login": "auth-service",
            "search": "search-service"
        },
        "services": [
            "auth-service",
            "search-service",
            "api-gateway"
        ]
    }
}

SERVICE_BACKEND_MAPPING = {
    "auth-service": [
        "https://auth-east.example.com",
        "https://auth-west.example.com"
    ]
}
```

### Step 4: Test the Setup

```bash
# Run the application
streamlit run app.py

# Access at http://localhost:8501
```

**Test queries:**
```
"Show me the health of auth-service"
"What's the P95 latency for search-service in the last hour?"
"Find error traces for checkout-api"
"Get backends for payment-service"
"What deployments happened in the last 4 hours?"
```

## Docker Deployment

### Build and Run with Docker

```bash
# Build image
docker build -t sre-ai-agent -f docker/Dockerfile .

# Run container
docker run -p 8501:8501 --env-file .env sre-ai-agent
```

### Using Docker Compose

```bash
# Start all services
docker-compose -f docker/docker-compose.yml up -d

# View logs
docker-compose -f docker/docker-compose.yml logs -f

# Stop services
docker-compose -f docker/docker-compose.yml down
```

## Project Structure

```
sre-multiagent-ai/
├── app.py                      # Main Streamlit application
├── requirements.txt            # Python dependencies
├── .env.example               # Environment template
├── README.md                  # Project documentation
├── SETUP_GUIDE.md            # This file
│
├── agents/                    # Agent implementations
│   ├── root_agent.py         # Orchestration agent
│   ├── kpi_agent.py          # KPI analysis
│   ├── metrics_agent.py      # VALE metrics
│   ├── trace_agent.py        # Distributed tracing
│   ├── failover_agent.py     # Traffic management
│   └── deployment_agent.py   # Deployment tracking
│
├── tools/                     # Tool functions
│   ├── kpi_tools.py
│   ├── metrics_tools.py
│   ├── trace_tools.py
│   ├── failover_tools.py
│   └── deployment_tools.py
│
├── clients/                   # API clients
│   ├── grafana_client.py
│   ├── apollo_client.py
│   └── harness_client.py
│
├── config/                    # Configuration
│   ├── applications.py        # App & KPI definitions
│   └── prompts.py            # Agent prompts
│
├── utils/                     # Utilities
│   ├── validation.py
│   ├── formatting.py
│   └── error_handling.py
│
└── docker/                    # Docker files
    ├── Dockerfile
    └── docker-compose.yml
```

## Troubleshooting

### Issue: "Module not found" errors

**Solution:**
```bash
# Ensure you're in the virtual environment
source venv/bin/activate

# Reinstall dependencies
pip install -r requirements.txt
```

### Issue: Grafana API returns 401 Unauthorized

**Solution:**
- Verify API token is valid and not expired
- Check token has appropriate permissions (Editor or Admin)
- Ensure `GRAFANA_URL` doesn't have trailing slash

### Issue: No traces found

**Solution:**
- Verify Tempo datasource is correctly configured
- Check service names match exactly (case-sensitive)
- Ensure traces exist in the time range specified
- Verify `x-scope-OrgID` header if using multi-tenancy

### Issue: Failover validation fails

**Solution:**
- Ensure backend URLs are exactly as configured in Apollo Router
- Check backend health endpoints are accessible
- Verify service-to-backend mapping in `config/applications.py`
- Review rate limit settings (default: 5 minutes between failovers)

### Issue: Gemini API rate limits

**Solution:**
- Implement exponential backoff (already included in code)
- Consider upgrading to higher API tier
- Reduce concurrent user sessions

## Development

### Running Tests

```bash
# Install dev dependencies
pip install pytest pytest-cov pytest-asyncio

# Run tests
pytest tests/

# With coverage
pytest --cov=agents --cov=tools --cov=clients tests/
```

### Code Formatting

```bash
# Install formatters
pip install black flake8 mypy

# Format code
black agents/ tools/ clients/

# Lint
flake8 agents/ tools/ clients/

# Type check
mypy agents/ tools/ clients/
```

### Adding a New Agent

1. Create agent file in `agents/new_agent.py`:
```python
from google.adk.agents.llm_agent import Agent
from tools.new_tools import tool1, tool2

def create_new_agent() -> Agent:
    return Agent(
        name="new_agent",
        model="gemini-2.0-flash-exp",
        description="Description of agent capabilities",
        instruction="Agent system prompt",
        tools=[tool1, tool2]
    )
```

2. Create tools in `tools/new_tools.py`

3. Add to root agent in `agents/root_agent.py`:
```python
from agents.new_agent import create_new_agent

new_agent = create_new_agent()
root_agent = Agent(
    tools=[
        # ... existing tools
        agent_tool.AgentTool(agent=new_agent)
    ]
)
```

4. Create prompt in `config/prompts.py`

## Production Deployment

### Kubernetes Deployment

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: sre-ai-agent
spec:
  replicas: 2
  selector:
    matchLabels:
      app: sre-ai-agent
  template:
    metadata:
      labels:
        app: sre-ai-agent
    spec:
      containers:
      - name: sre-ai-agent
        image: your-registry/sre-ai-agent:latest
        ports:
        - containerPort: 8501
        env:
        - name: GOOGLE_API_KEY
          valueFrom:
            secretKeyRef:
              name: sre-ai-secrets
              key: gemini-api-key
        # Add other env vars from ConfigMap/Secret
```

### Security Best Practices

1. **API Keys:**
   - Store in Kubernetes Secrets or vault
   - Rotate regularly
   - Use least-privilege access

2. **Network:**
   - Deploy behind authentication proxy
   - Use TLS for all connections
   - Implement rate limiting

3. **Audit:**
   - Log all failover operations
   - Track user actions
   - Monitor API usage

4. **Validation:**
   - Enforce backend health checks
   - Require manual approval for production failovers
   - Implement approval workflows

## Support

- **Issues:** GitHub Issues
- **Documentation:** `/docs` directory
- **Examples:** `/examples` directory

## License

MIT License - see LICENSE file for details
