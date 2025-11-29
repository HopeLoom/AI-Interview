# 🚀 AI Interview Simulation Platform

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.0-blue)](https://www.typescriptlang.org/)
[![Python](https://img.shields.io/badge/Python-3.9+-green)](https://www.python.org/)

An open-source AI-powered interview simulation platform for candidate practice and company screening. Features real-time AI interviewers, multi-LLM support, and WebSocket communication.

**Key Features:**
- 🤖 **AI-Powered Interviewers** - Multiple LLM providers (OpenAI, DeepSeek, Gemini, Grok)
- 🎯 **Dual-Mode Operation** - Candidate practice and company screening modes
- ⚡ **Real-Time Communication** - WebSocket-based bidirectional communication
- 🎨 **Modern UI** - Built with React, TypeScript, and Tailwind CSS
- 🔧 **Flexible Configuration** - JSON-based interview configuration system
- 📊 **Comprehensive Evaluation** - Automated scoring and feedback system

## 🌟 Overview

This platform transforms the interview experience by providing AI-powered interviewers, real-time evaluation, and comprehensive feedback. Built with React, TypeScript, and modern web technologies, it supports three distinct deployment modes for different use cases.

## 🎯 Three-Mode Architecture

### **Mode 1: Candidate Practice** (`candidate-practice`)
**Purpose**: Independent candidates practice interviews to improve skills
- **Features**: Full signup, practice scenarios, skill development, resume upload
- **Target Users**: Job seekers, students, professionals wanting to practice
- **Experience**: Comprehensive practice platform with learning features

### **Mode 2: Company Interviewing** (`company-interviewing`)
**Purpose**: Companies create and manage AI-powered interview screening
- **Features**: Company signup, interview creation, candidate management, analytics
- **Target Users**: HR teams, hiring managers, recruitment agencies
- **Experience**: Full interview management and candidate screening platform

### **Mode 3: Company Candidate Interview** (`company-candidate-interview`)
**Purpose**: Candidates take company-created interviews
- **Features**: No signup, interview code login, focused interview experience
- **Target Users**: Candidates invited by companies for screening
- **Experience**: Streamlined, professional interview session

## 🛠️ Technology Stack

- **Frontend**: React 18 + TypeScript
- **Build Tool**: Vite
- **Styling**: Tailwind CSS + shadcn/ui components
- **Routing**: Wouter (lightweight React router)
- **State Management**: React Context API
- **Real-time Communication**: WebSocket
- **AI Integration**: OpenAI, DeepSeek, Gemini, Grok APIs
- **Audio/Video**: WebRTC, ElevenLabs, Google Speech

## 🚀 Quick Start

### Prerequisites
- **Node.js 18+** - [Download](https://nodejs.org/)
- **Python 3.9+** - [Download](https://www.python.org/downloads/)
- **npm or yarn** - Comes with Node.js
- **Git** - [Download](https://git-scm.com/)

### Installation

```bash
# Clone the repository
git clone git@github.com:HopeLoom/AI-Interview.git
cd AI-Interview

# Frontend setup
npm install

# Backend setup
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
cd ..

# Configure environment (see SETUP.md for details)
cp .env.example .env
cp backend/.env.example backend/.env
# Edit .env files with your API keys and configuration
```

### Development

**Start Backend:**
```bash
cd backend
python main.py
# Backend runs on http://localhost:8000
```

**Start Frontend (in another terminal):**
```bash
# Candidate Practice Mode
npm run dev:candidate

# Company Interviewing Mode  
npm run dev:company

# Company Candidate Interview Mode
npm run dev:company-candidate

# Default development mode
npm run dev
# Frontend runs on http://localhost:3000
```

📖 **For detailed setup instructions, see [SETUP.md](./SETUP.md)**

### Building for Production
```bash
# Build for different modes

# Candidate Practice Platform
npm run build:candidate

# Company Interviewing Platform
npm run build:company

# Company Candidate Interview Platform
npm run build:company-candidate

# Default build
npm run build
```

## ⚙️ Environment Configuration

The platform uses environment-specific configuration files that are automatically loaded based on the build mode.

### Environment File Structure
```
.env                                    # Base environment (fallback)
.env.staging                           # Staging backend config
.env.production                        # Production backend config

# Mode-specific configurations
.env.candidate-practice               # Development candidate mode + staging backend
.env.company-interviewing             # Development company mode + staging backend
.env.company-candidate-interview      # Development company candidate mode + staging backend

# Production mode-specific configurations
.env.candidate-practice.production    # Production candidate mode + production backend
.env.company-interviewing.production  # Production company mode + production backend
.env.company-candidate-interview.production # Production company candidate mode + production backend
```

### Environment Variables
```bash
# Core Configuration
VITE_APP_MODE=candidate-practice      # Application mode
VITE_API_BASE_URL=api.hopeloom.com   # Backend API URL
VITE_ENV=production                   # Environment (staging/production)

# Feature Flags
VITE_ENABLE_COMPANY_FEATURES=true     # Enable company-specific features
VITE_ENABLE_CANDIDATE_FEATURES=true   # Enable candidate-specific features

# Application Metadata
VITE_APP_TITLE=AI Interview Practice  # Application title
VITE_APP_DESCRIPTION=Practice interviews with AI-powered interviewers
```

## 🏗️ Architecture Overview

For detailed architecture documentation with diagrams, see [ARCHITECTURE.md](./ARCHITECTURE.md).

### Core Components

**Master Agent System:**
- Orchestrates the entire interview process
- Manages communication between all agents
- Handles WebSocket communication with frontend
- Tracks interview state and flow

**AI Panelist Agents:**
- Multiple AI panelists with distinct personalities
- Each panelist has memory, decision-making, and response generation
- Supports multiple LLM providers (OpenAI, DeepSeek, Gemini, Grok)

**Activity Agent:**
- Monitors coding activities during interviews
- Analyzes candidate code submissions
- Provides feedback to panelists

**WebSocket Communication:**
- Real-time bidirectional communication
- Handles audio, text, and code submissions
- Manages interview state synchronization

### Project Structure

```
Simulation/
├── client/                          # Frontend React application
│   ├── src/
│   │   ├── components/             # Reusable UI components
│   │   │   ├── signup/            # Signup form components
│   │   │   ├── interview/         # Interview-related components
│   │   │   ├── configuration/     # Interview configuration components
│   │   │   └── ui/               # Base UI components (shadcn/ui)
│   │   ├── pages/                # Page components
│   │   ├── contexts/             # React context providers
│   │   ├── hooks/                # Custom React hooks
│   │   ├── lib/                  # Utility libraries
│   │   └── services/             # API service layer
│   └── package.json
├── backend/                       # Python backend services
│   ├── master_agent/             # Master agent orchestration
│   ├── panelist_agent/           # AI panelist agents
│   ├── interview_configuration/  # Configuration management
│   ├── routers/                  # API route handlers
│   ├── core/                     # Core functionality
│   │   ├── database/            # Database abstraction
│   │   ├── memory/              # Agent memory systems
│   │   └── prompting/          # Prompt strategies
│   └── server/                  # WebSocket server
├── shared/                        # Shared TypeScript schemas
├── .env.*                        # Environment configuration files
└── README.md
```

### Database Support

The platform supports multiple database backends:
- **SQLite** - Easiest for development (included with Python)
- **PostgreSQL** - Production-ready relational database
- **Firebase** - NoSQL cloud database

See [SETUP.md](./SETUP.md) for database configuration.

## 🔧 Mode Configuration

### Mode-Specific Features
Each mode has different feature sets enabled:

| Feature | Candidate Practice | Company Interviewing | Company Candidate Interview |
|---------|-------------------|---------------------|----------------------------|
| **Candidate Signup** | ✅ | ✅ | ❌ |
| **Company Signup** | ❌ | ✅ | ❌ |
| **Candidate Dashboard** | ✅ | ✅ | ❌ |
| **Company Dashboard** | ❌ | ✅ | ❌ |
| **Interview Configuration** | ✅ | ✅ | ❌ |
| **Practice Mode** | ✅ | ❌ | ❌ |
| **Screening Mode** | ❌ | ✅ | ✅ |

### Routing Configuration
Each mode has different allowed routes and default destinations:

```typescript
// Example: Company Candidate Interview Mode
{
  mode: 'company-candidate-interview',
  routing: {
    defaultRoute: '/interview',
    allowedRoutes: ['/login', '/interview']
  }
}
```

## 🚀 Deployment

### Single Codebase, Multiple Deployments
The platform is designed to be deployed as three separate applications:

1. **Practice Platform**: `npm run build:candidate`
2. **Company Platform**: `npm run build:company`
3. **Interview Platform**: `npm run build:company-candidate`

### Deployment Commands
```bash
# Build all three platforms
npm run build:candidate
npm run build:company  
npm run build:company-candidate

# Each build creates optimized production files in dist/public/
```

### Environment-Specific Deployment
- **Staging**: Uses `.env.{mode}` files with staging backend
- **Production**: Uses `.env.{mode}.production` files with production backend

## 🔐 Authentication & User Management

### User Types
- **Candidates**: Practice users and company interview takers
- **Companies**: Interview creators and managers

### Authentication Flow
1. **Practice Mode**: Full signup/login for candidates
2. **Company Mode**: Company signup + candidate signup
3. **Interview Mode**: Email + interview code only

## 📱 Key Features

### AI-Powered Interviewers
- Multiple AI models (OpenAI, DeepSeek, Gemini, Grok)
- Real-time conversation simulation
- Context-aware responses
- Industry-specific knowledge

### Interview Management
- Custom question creation
- Multiple interview formats
- Candidate tracking
- Performance analytics

### Real-time Communication
- WebSocket-based communication
- Audio/video integration
- Live transcription
- Session recording

## 🧪 Testing

### TypeScript Compilation
```bash
npm run check
```

### Development Testing
```bash
# Test different modes
npm run dev:candidate
npm run dev:company
npm run dev:company-candidate
```

## 📚 API Documentation

### Backend Integration
The platform integrates with a Python backend that provides:
- User authentication and management
- Interview configuration and management
- AI model integration
- Real-time communication services

### API Endpoints
- `/api/auth/*` - Authentication endpoints
- `/api/interviews/*` - Interview management
- `/api/candidates/*` - Candidate management
- `/api/companies/*` - Company management

## 🔧 Key Features

### Core Interview Simulation
- ✅ **Multi-round interviews** with different panelists per round
- ✅ **Real-time AI conversation** via WebSocket
- ✅ **Coding activity monitoring** with live code analysis
- ✅ **Evaluation system** with scoring and feedback
- ✅ **Multiple LLM providers** (OpenAI, DeepSeek, Gemini, Grok)

### Configuration System
- ✅ **Dynamic interview configuration** generation from job descriptions
- ✅ **Template-based setup** with example configurations
- ✅ **Granular topic selection** for interview rounds
- ✅ **Custom panelist personalities** and roles

### Multi-Mode Support
- ✅ **Candidate Practice Mode** - Self-service interview practice
- ✅ **Company Interviewing Mode** - Full interview management
- ✅ **Company Candidate Mode** - Streamlined interview experience

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](./LICENSE) file for details.

## 🤝 Contributing

We welcome contributions! Please see [CONTRIBUTING.md](./CONTRIBUTING.md) for guidelines.

## 📚 Documentation

- **[SETUP.md](./SETUP.md)** - Detailed setup and configuration guide
- **[CONTRIBUTING.md](./CONTRIBUTING.md)** - Contribution guidelines
- **[REQUIREMENTS.md](./REQUIREMENTS.md)** - Feature requirements and specifications
- **[OPEN_SOURCE_READINESS_ASSESSMENT.md](./OPEN_SOURCE_READINESS_ASSESSMENT.md)** - Project readiness assessment

## 🆘 Support & Resources

- **Setup Guide**: [SETUP.md](./SETUP.md) - Detailed setup instructions
- **Contributing**: [CONTRIBUTING.md](./CONTRIBUTING.md) - How to contribute
- **Issues**: Report issues via GitHub Issues
- **Contact**: info@hopeloom.com

## ⚠️ Important Notes

**This is a prototype/starter project:**
- Authentication and authorization are intentionally simplified for development
- Add proper security (password hashing, JWT, authorization) before production use
- Database schema is created automatically on first run
- See [OPEN_SOURCE_READINESS_ASSESSMENT.md](./OPEN_SOURCE_READINESS_ASSESSMENT.md) for details

## 🔄 Version History

### v1.0.0 - Three-Mode System
- ✅ Candidate Practice Mode
- ✅ Company Interviewing Mode  
- ✅ Company Candidate Interview Mode
- ✅ Mode-aware routing and configuration
- ✅ Environment-specific builds
- ✅ Clean component architecture

---

**Built with ❤️ by the HopeLoom Team**
