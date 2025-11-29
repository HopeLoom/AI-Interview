# Architecture Documentation

This document describes the architecture of the AI Interview Simulation Platform, including both backend and frontend components.

## Backend Architecture

The backend is built with Python FastAPI and follows an agent-based architecture with a master agent orchestrating multiple specialized agents.

```mermaid
graph TB
    subgraph "Client Layer"
        FE[Frontend Client]
    end
    
    subgraph "API Gateway"
        WS[WebSocket Handler<br/>/ws]
        REST[REST API Routes<br/>/api/*]
    end
    
    subgraph "Connection Management"
        CM[ConnectionManager]
        UMIM[UserMasterInstanceManager]
    end
    
    subgraph "Master Agent System"
        MA[Master Agent<br/>Orchestrator]
        ITT[Interview Topic Tracker]
        MM[Master Memory]
    end
    
    subgraph "Specialized Agents"
        PA1[Panelist Agent 1]
        PA2[Panelist Agent 2]
        AA[Activity Agent<br/>Code Monitor]
        EA[Evaluation Agent<br/>Scoring]
    end
    
    subgraph "Core Services"
        DB[(Database<br/>Firebase/PostgreSQL/SQLite)]
        LLM[LLM Providers<br/>OpenAI/DeepSeek/Gemini/Grok]
        SPEECH[Speech Services<br/>TTS/STT]
        IMG[Image Generator]
        MEMORY[Memory System<br/>Character/Recall Memory]
    end
    
    subgraph "Configuration & Setup"
        ICS[Interview Configuration Service]
        IDA[Interview Details Agent]
        CFA[Candidate Profile Generator]
        PF[Panelist Factory]
    end
    
    subgraph "REST API Routes"
        CONFIG[Interview Configuration]
        COMPANY[Company Management]
        CANDIDATE[Candidate Management]
        JOB[Job Postings]
        APP[Applications]
        EVAL[Evaluations]
        IMG_UPLOAD[Image Upload]
        VIDEO[Video Chunk]
    end
    
    FE -->|WebSocket| WS
    FE -->|HTTP| REST
    
    WS --> CM
    WS --> UMIM
    CM --> MA
    UMIM --> MA
    
    MA --> ITT
    MA --> MM
    MA -->|Orchestrates| PA1
    MA -->|Orchestrates| PA2
    MA -->|Orchestrates| AA
    MA -->|Orchestrates| EA
    
    PA1 --> LLM
    PA2 --> LLM
    AA --> LLM
    EA --> LLM
    MA --> LLM
    
    PA1 --> MEMORY
    PA2 --> MEMORY
    MA --> MEMORY
    
    AA -->|Monitors| DB
    EA --> DB
    MA --> DB
    
    ICS --> IDA
    ICS --> CFA
    ICS --> PF
    PF --> IMG
    
    REST --> CONFIG
    REST --> COMPANY
    REST --> CANDIDATE
    REST --> JOB
    REST --> APP
    REST --> EVAL
    REST --> IMG_UPLOAD
    REST --> VIDEO
    
    CONFIG --> ICS
    COMPANY --> DB
    CANDIDATE --> DB
    JOB --> DB
    APP --> DB
    EVAL --> EA
    
    WS --> SPEECH
    
    style MA fill:#ff6b6b
    style LLM fill:#4ecdc4
    style DB fill:#95e1d3
    style CM fill:#fce38a
    style WS fill:#f38181
```

### Backend Component Details

#### **Master Agent** (Central Orchestrator)
- Manages interview flow and state
- Routes messages between agents and frontend
- Determines who speaks next
- Generates advice for panelists
- Performs topic completion checks
- Maintains interview transcript

#### **Specialized Agents**
- **Panelist Agents**: AI interviewers with unique personalities
  - Think → Access Domain Knowledge → Respond → Reflect → Evaluate
  - Multiple panelists per interview round
- **Activity Agent**: Monitors coding activities
  - Analyzes code changes in real-time
  - Provides insights to panelists
- **Evaluation Agent**: Performs scoring and assessment
  - Evaluates candidate responses
  - Generates comprehensive feedback

#### **Core Services**
- **Database Layer**: Abstracted database interface
  - Supports Firebase, PostgreSQL, SQLite
  - User profiles, sessions, configurations
- **LLM Providers**: Multi-provider AI support
  - OpenAI (GPT-4, GPT-3.5)
  - DeepSeek, Gemini, Grok, Perplexity
- **Speech Services**: Text-to-speech and speech-to-text
  - OpenAI, ElevenLabs, Google, Groq
- **Memory System**: Context and character memory
  - Character memory for panelist personalities
  - Recall memory for interview context
  - Graph-based memory structure

#### **Communication Flow**
```
Frontend ↔ WebSocket ↔ ConnectionManager ↔ Master Agent
                                         ↓
                          ┌──────────────┼──────────────┐
                          ↓              ↓              ↓
                    Panelist Agents  Activity Agent  Evaluation Agent
                          ↓              ↓              ↓
                          └──────────────┼──────────────┘
                                         ↓
                                    LLM Providers
                                         ↓
                                    Database/Memory
```

## Frontend Architecture

The frontend is a React TypeScript application with mode-aware routing and real-time WebSocket communication.

```mermaid
graph TB
    subgraph "Entry Point"
        APP[App.tsx]
        MAIN[main.tsx]
    end
    
    subgraph "Routing Layer"
        ROUTER[ModeAwareRouter]
        PROTECTED[Protected Routes]
        MODE_LOGIN[Mode-Specific Login]
    end
    
    subgraph "Context Providers"
        USER[UserContext]
        INTERVIEW[InterviewContext]
        CONFIG[ConfigurationContext]
        CAMERA[CameraContext]
        COMPANY[CompanyContext]
        CC[CompanyCandidateContext]
    end
    
    subgraph "Pages"
        HOME[Home]
        CAND_LOGIN[Candidate Login]
        COMP_LOGIN[Company Login]
        CC_LOGIN[Company Candidate Login]
        CAND_DASH[Candidate Dashboard]
        COMP_DASH[Company Dashboard]
        CONFIG_WIZ[Configuration Wizard]
        INTERVIEW_LAYOUT[Interview Layout]
        RESULTS[Results]
    end
    
    subgraph "Interview Components"
        HEADER[Header]
        VIDEO[Video Participants]
        CHAT[Chat Panel]
        MEDIA[Media Controls]
        CODING[Live Coding Layout]
        PROBLEM[Problem Statement]
        PROGRESS[Progress Tracker]
    end
    
    subgraph "Configuration Components"
        JOB_DETAILS[Job Details Step]
        RESUME[Resume Upload]
        REVIEW[Review & Generate]
        RESULTS_PANEL[Configuration Results]
    end
    
    subgraph "Services Layer"
        WS[WebSocket Service]
        API[API Client]
        CAND_SVC[Candidate Service]
        COMP_SVC[Company Service]
        CONFIG_SVC[Config Service]
        EVAL_SVC[Evaluation Service]
        AUDIO[Audio Streaming]
    end
    
    subgraph "Hooks"
        USE_INTERVIEW[useInterviewState]
        USE_AUDIO[useAudioStreaming]
        USE_CAMERA[useCameraStream]
        USE_ERROR[useErrorHandler]
    end
    
    subgraph "UI Components"
        SHADCN[shadcn/ui Components]
        NAV[Navigation]
    end
    
    MAIN --> APP
    APP --> WS
    APP --> ROUTER
    
    ROUTER --> PROTECTED
    ROUTER --> MODE_LOGIN
    ROUTER --> USER
    ROUTER --> INTERVIEW
    ROUTER --> CONFIG
    ROUTER --> CAMERA
    
    PROTECTED --> CAND_LOGIN
    PROTECTED --> COMP_LOGIN
    PROTECTED --> CC_LOGIN
    PROTECTED --> CAND_DASH
    PROTECTED --> COMP_DASH
    PROTECTED --> CONFIG_WIZ
    PROTECTED --> INTERVIEW_LAYOUT
    PROTECTED --> RESULTS
    
    INTERVIEW_LAYOUT --> HEADER
    INTERVIEW_LAYOUT --> VIDEO
    INTERVIEW_LAYOUT --> CHAT
    INTERVIEW_LAYOUT --> MEDIA
    INTERVIEW_LAYOUT --> CODING
    INTERVIEW_LAYOUT --> PROBLEM
    INTERVIEW_LAYOUT --> PROGRESS
    
    CONFIG_WIZ --> JOB_DETAILS
    CONFIG_WIZ --> RESUME
    CONFIG_WIZ --> REVIEW
    CONFIG_WIZ --> RESULTS_PANEL
    
    INTERVIEW_LAYOUT --> WS
    CAND_DASH --> API
    COMP_DASH --> API
    CONFIG_WIZ --> API
    
    WS --> USE_INTERVIEW
    VIDEO --> USE_CAMERA
    MEDIA --> USE_AUDIO
    
    API --> CAND_SVC
    API --> COMP_SVC
    API --> CONFIG_SVC
    API --> EVAL_SVC
    
    INTERVIEW_LAYOUT --> SHADCN
    CAND_DASH --> SHADCN
    COMP_DASH --> SHADCN
    
    style ROUTER fill:#ff6b6b
    style WS fill:#4ecdc4
    style INTERVIEW_LAYOUT fill:#95e1d3
    style USER fill:#fce38a
    style INTERVIEW fill:#f38181
```

### Frontend Component Details

#### **Three-Mode Architecture**
1. **Candidate Practice Mode** (`candidate-practice`)
   - Full signup and registration
   - Practice interview scenarios
   - Skill development features
   - Resume upload and profile management

2. **Company Interviewing Mode** (`company-interviewing`)
   - Company dashboard
   - Interview configuration
   - Candidate management
   - Analytics and reporting

3. **Company Candidate Interview Mode** (`company-candidate-interview`)
   - Streamlined interview experience
   - Interview code login (no signup required)
   - Focused interview interface

#### **State Management**
- **Context API**: Global state management
  - `UserContext`: Current user and authentication
  - `InterviewContext`: Interview state and participants
  - `ConfigurationContext`: Interview configuration data
  - `CameraContext`: Camera/media state
  - `CompanyContext`: Company-specific data
  - `CompanyCandidateContext`: Company candidate flow

#### **Real-Time Communication**
- **WebSocket Service**: Bidirectional communication
  - Interview messages
  - Speech transcription
  - Real-time updates
  - Activity monitoring

#### **Key Features**
- Mode-aware routing with feature flags
- Protected routes with authentication
- Real-time video/audio streaming
- Live coding environment integration
- Responsive UI with Tailwind CSS
- shadcn/ui component library

### Data Flow

#### **Interview Flow**
```
1. User Login → UserContext
2. Load Configuration → ConfigurationContext
3. Start Interview → InterviewContext
4. WebSocket Connection → Real-time updates
5. Video/Audio Stream → CameraContext
6. Messages → Chat Panel
7. Evaluation → Results Page
```

#### **Configuration Flow**
```
1. Job Details Input
2. Resume Upload
3. Configuration Generation (API)
4. Review & Generate
5. Save Configuration
6. Start Interview
```

## Technology Stack

### Backend
- **Framework**: FastAPI
- **Language**: Python 3.9+
- **Database**: Firebase / PostgreSQL / SQLite
- **Real-time**: WebSocket
- **AI**: OpenAI, DeepSeek, Gemini, Grok
- **Speech**: OpenAI, ElevenLabs, Google, Groq
- **Testing**: pytest

### Frontend
- **Framework**: React 18
- **Language**: TypeScript
- **Build Tool**: Vite
- **Styling**: Tailwind CSS
- **Components**: shadcn/ui
- **Routing**: Wouter
- **State**: React Context API
- **Real-time**: WebSocket

## Communication Patterns

### WebSocket Message Types

**From Client:**
- User Login/Logout
- Speech Data (STT)
- Text Messages
- Interview Start/End
- Configuration Requests

**To Client:**
- Interview Messages
- Speaker Changes
- Topic Updates
- Activity Info
- Evaluation Results
- Speech Audio (TTS)

### REST API Endpoints

- `/api/configurations/*` - Interview configuration CRUD
- `/api/company/*` - Company management
- `/api/candidates/*` - Candidate management
- `/api/job-postings/*` - Job posting management
- `/api/applications/*` - Application tracking
- `/api/evaluation/*` - Evaluation data
- `/api/upload/*` - File uploads

