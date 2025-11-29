# Setup Guide

This guide will help you set up the AI Interview Simulation Platform for local development.

## Prerequisites

### Required Software
- **Node.js 18+** - [Download](https://nodejs.org/)
- **Python 3.9+** - [Download](https://www.python.org/downloads/)
- **npm or yarn** - Comes with Node.js
- **Git** - [Download](https://git-scm.com/)

### Optional (for different database backends)
- **PostgreSQL** (if using PostgreSQL backend)
- **Firebase account** (if using Firebase backend)
- **SQLite** (included with Python)

## Quick Start

### 1. Clone the Repository

```bash
git clone git@github.com:HopeLoom/AI-Interview.git
cd AI-Interview
```

### 2. Frontend Setup

```bash
# Install dependencies
npm install

# Create environment file
cp .env.example .env
cp backend/.env.example backend/.env

# Edit .env with your configuration
# See Environment Configuration section below
```

### 3. Backend Setup

```bash
cd backend

# Create virtual environment (recommended)
python -m venv venv

# Activate virtual environment
# On macOS/Linux:
source venv/bin/activate
# On Windows:
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure backend
# Copy config.yaml and update with your settings
# See Backend Configuration section below
```

### 4. Database Setup

Choose one of the following database options:

#### Option A: SQLite (Easiest for Development)

No additional setup needed! SQLite is included with Python.

Update `backend/config.yaml`:
```yaml
database:
  type: "sqlite"
  sqlite_path: "./data/interview_sim_dev.db"
```

#### Option B: PostgreSQL

1. Install PostgreSQL
2. Create a database:
```sql
CREATE DATABASE interview_sim;
```

3. Update `backend/config.yaml`:
```yaml
database:
  type: "postgresql"
  host: "localhost"
  port: 5432
  database: "interview_sim"
  user: "your_username"
  password: "your_password"
```

#### Option C: Firebase

1. Create a Firebase project at [Firebase Console](https://console.firebase.google.com/)
2. Download service account credentials JSON file
3. Place it in `backend/` as `interview-simulation-firebase.json`
4. Update `backend/config.yaml`:
```yaml
database:
  type: "firebase"
  firebase_credentials_path: "interview-simulation-firebase.json"
  firebase_storage_bucket: "your-bucket-name.appspot.com"
```

### 5. Configure API Keys

The platform supports multiple LLM providers. You'll need at least one API key.

#### OpenAI (Recommended for testing)
1. Get API key from [OpenAI](https://platform.openai.com/api-keys)
2. Set environment variable:
```bash
export OPENAI_API_KEY="your-api-key-here"
```

Or update `backend/config.yaml`:
```yaml
llm_providers:
  - name: "openai"
    api_key: "your-api-key-here"
    enabled: true
```

#### Other Providers (Optional)
- **DeepSeek**: Get key from [DeepSeek](https://platform.deepseek.com/)
- **Gemini**: Get key from [Google AI Studio](https://makersuite.google.com/app/apikey)
- **Grok**: Get key from [xAI](https://x.ai/)

### 6. Start the Application

#### Terminal 1: Backend Server
```bash
cd backend
python main.py
# Or use the start script:
./start-dev.sh
```

The backend will start on `http://localhost:8000`

#### Terminal 2: Frontend Development Server
```bash
# For candidate practice mode
npm run dev:candidate

# For company interviewing mode
npm run dev:company

# For company candidate interview mode
npm run dev:company-candidate

# Or default mode
npm run dev
```

The frontend will start on `http://localhost:3000`

## Environment Configuration

### Frontend Environment Variables

Create a `.env` file in the root directory (or mode-specific files):

**Base `.env`:**
```bash
VITE_APP_MODE=candidate-practice
VITE_API_BASE_URL=http://localhost:8000
VITE_ENV=development
VITE_ENABLE_COMPANY_FEATURES=false
VITE_ENABLE_CANDIDATE_FEATURES=true
VITE_APP_TITLE=AI Interview Simulation
VITE_APP_DESCRIPTION=Practice interviews with AI-powered interviewers
```

**Mode-specific files:**
- `.env.candidate-practice` - For candidate practice mode
- `.env.company-interviewing` - For company interviewing mode
- `.env.company-candidate-interview` - For company candidate interview mode

### Backend Configuration

The backend uses `backend/config.yaml` for configuration. Key settings:

```yaml
default:
  environment: development
  debug: true
  host: "0.0.0.0"
  port: 8000
  
  database:
    type: "sqlite"  # or "firebase" or "postgresql"
    
  llm_providers:
    - name: "openai"
      api_key: ""  # Set via OPENAI_API_KEY env var or here
      enabled: true
```

## Running in Different Modes

### Candidate Practice Mode
```bash
# Frontend
npm run dev:candidate

# Backend (same for all modes)
cd backend && python main.py
```

**Features:**
- Candidate signup/login
- Practice interview configuration
- Skill tracking
- Interview history

### Company Interviewing Mode
```bash
# Frontend
npm run dev:company

# Backend
cd backend && python main.py
```

**Features:**
- Company signup/login
- Interview configuration creation
- Candidate management
- Analytics dashboard

### Company Candidate Interview Mode
```bash
# Frontend
npm run dev:company-candidate

# Backend
cd backend && python main.py
```

**Features:**
- Interview code login
- Focused interview experience
- No signup required

## Testing the Setup

### 1. Check Backend Health
```bash
curl http://localhost:8000/
# Should return: {"message": "Hello World"}
```

### 2. Check Frontend
Open `http://localhost:3000` in your browser. You should see the login page.

### 3. Test WebSocket Connection
The frontend automatically connects to the WebSocket at `ws://localhost:8000/ws` when you start an interview.

## Common Issues

### Port Already in Use
If port 8000 or 3000 is already in use:

**Backend:**
- Change port in `backend/config.yaml`:
```yaml
port: 8001
```

**Frontend:**
- Change port in `vite.config.ts` or use:
```bash
npm run dev -- --port 3001
```

### Database Connection Errors

**SQLite:**
- Ensure the `backend/data/` directory exists
- Check file permissions

**PostgreSQL:**
- Verify PostgreSQL is running: `pg_isready`
- Check credentials in `config.yaml`
- Ensure database exists

**Firebase:**
- Verify credentials file path
- Check service account permissions
- Verify storage bucket name

### API Key Issues

**Missing API Key:**
- Set environment variable: `export OPENAI_API_KEY="your-key"`
- Or update `backend/config.yaml`

**Invalid API Key:**
- Verify key is correct
- Check API key permissions
- Ensure account has credits/quota

### Frontend Can't Connect to Backend

1. Verify backend is running on correct port
2. Check `VITE_API_BASE_URL` in `.env` matches backend URL
3. Check CORS settings in `backend/config.yaml`:
```yaml
security:
  cors_origins:
    - "http://localhost:3000"
```

## Development Tips

### Hot Reload
- Frontend: Automatically reloads on file changes (Vite)
- Backend: Restart required for Python changes

### Debugging

**Backend:**
- Enable debug mode in `config.yaml`: `debug: true`
- Check logs in `data/logs/main/`

**Frontend:**
- Use browser DevTools
- Check Network tab for API calls
- Check Console for errors

### Database Migrations

For SQLite/PostgreSQL, the database schema is created automatically on first run.

For Firebase, ensure your service account has proper permissions.

## Next Steps

- Read [README.md](./README.md) for architecture overview
- Check [CONTRIBUTING.md](./CONTRIBUTING.md) for development guidelines
- Explore `backend/onboarding_data/` for example configurations
- Review `backend/README.md` for backend-specific documentation

## Getting Help

- Check existing issues in the repository
- Review documentation in `/docs` (if available)
- Contact: info@hopeloom.com

---

**Note:** This is a prototype/starter project. Authentication and authorization are intentionally simplified for development. Add proper security before production deployment.

