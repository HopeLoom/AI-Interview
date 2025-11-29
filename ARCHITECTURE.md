# Architecture Documentation

This document describes the architecture of the AI Interview Simulation Platform, including both backend and frontend components.

## System Overview

```mermaid
flowchart LR
    subgraph Frontend["🌐 Frontend (React + TypeScript)"]
        A[User Interface]
        B[WebSocket Client]
        C[REST API Client]
    end
    
    subgraph Backend["⚙️ Backend (FastAPI + Python)"]
        D[WebSocket Handler]
        E[REST API Routes]
        F[Master Agent]
        G[Specialized Agents]
        H[LLM Providers]
        I[(Database)]
    end
    
    A --> B
    A --> C
    B --> D
    C --> E
    D --> F
    E --> I
    F --> G
    G --> H
    F --> I
    G --> I
    
    style Frontend fill:#e1f5ff
    style Backend fill:#fff4e1
    style F fill:#ff6b6b
    style H fill:#4ecdc4
```

## Backend Architecture

The backend is built with Python FastAPI and follows an agent-based architecture with a master agent orchestrating multiple specialized agents.

### High-Level Architecture

```mermaid
flowchart LR
    A[Frontend] -->|WebSocket| B[WebSocket Handler]
    A -->|HTTP REST| C[API Routes]
    
    B --> D[Connection Manager]
    D --> E[Master Agent]
    
    E --> F[Panelist Agents]
    E --> G[Activity Agent]
    E --> H[Evaluation Agent]
    
    F --> I[LLM Providers]
    G --> I
    H --> I
    E --> I
    
    E --> J[(Database)]
    F --> K[Memory System]
    E --> K
    
    C --> L[Configuration Service]
    C --> M[Company APIs]
    C --> J
    
    style E fill:#ff6b6b
    style I fill:#4ecdc4
    style J fill:#95e1d3
```

### Agent Communication Flow

```mermaid
flowchart TD
    A[Frontend Client] -->|Step 1: Send Message| B[Connection Manager]
    B -->|Step 2: Route| C[Master Agent]
    
    C -->|Step 3: Forward| E[Panelist Agent]
    C -->|Step 3: Forward| F[Activity Agent]
    C -->|Step 3: Forward| G[Evaluation Agent]
    
    E -->|Step 4: Process| H[LLM Provider]
    F -->|Step 4: Analyze| H
    G -->|Step 4: Evaluate| H
    
    H -->|Step 5: Response| E
    H -->|Step 5: Response| F
    H -->|Step 5: Response| G
    
    E -->|Step 6: Update| I[Memory System]
    F -->|Step 6: Update| I
    G -->|Step 6: Update| I
    C -->|Step 6: Track| I
    
    E -->|Step 7: Return| C
    F -->|Step 7: Return| C
    G -->|Step 7: Return| C
    
    C -->|Step 8: Send Response| B
    B -->|Step 9: Update UI| A
    
    style C fill:#ff6b6b
    style H fill:#4ecdc4
    style I fill:#fce38a
```

### API Routes Structure

```mermaid
flowchart TD
    A[FastAPI App] --> B[WebSocket /ws]
    A --> C[REST API /api]
    
    C --> D[Configuration]
    C --> E[Company]
    C --> F[Candidates]
    C --> G[Job Postings]
    C --> H[Applications]
    C --> I[Evaluation]
    C --> J[Upload]
    
    D --> K[Interview Config Service]
    E --> L[(Database)]
    F --> L
    G --> L
    H --> L
    I --> M[Evaluation Agent]
    
    style A fill:#ff6b6b
    style L fill:#95e1d3
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

```mermaid
sequenceDiagram
    participant F as Frontend
    participant W as WebSocket Handler
    participant M as Master Agent
    participant P as Panelist Agent
    participant A as Activity Agent
    participant L as LLM Provider
    participant D as Database
    
    F->>W: Send Message
    W->>M: Route Message
    M->>M: Determine Action
    
    alt Interview Message
        M->>P: Forward to Panelist
        P->>L: Generate Response
        L->>P: Return Response
        P->>M: Send Back
    else Code Activity
        M->>A: Monitor Activity
        A->>L: Analyze Code
        L->>A: Return Analysis
        A->>M: Send Results
    end
    
    M->>D: Save State
    M->>W: Send Response
    W->>F: Update UI
```

## Frontend Architecture

The frontend is a React TypeScript application with mode-aware routing and real-time WebSocket communication.

### Component Hierarchy

```mermaid
flowchart TD
    A[App.tsx] --> B[ModeAwareRouter]
    B --> C[Context Providers]
    
    C --> D[UserContext]
    C --> E[InterviewContext]
    C --> F[ConfigurationContext]
    C --> G[CameraContext]
    
    B --> H[Pages]
    
    H --> I[Login Pages]
    H --> J[Dashboard Pages]
    H --> K[Interview Layout]
    H --> L[Configuration Wizard]
    
    K --> M[Video Participants]
    K --> N[Chat Panel]
    K --> O[Live Coding]
    K --> P[Media Controls]
    
    L --> Q[Job Details]
    L --> R[Resume Upload]
    L --> S[Review & Generate]
    
    B --> T[WebSocket Service]
    J --> U[API Services]
    L --> U
    
    style B fill:#ff6b6b
    style T fill:#4ecdc4
    style K fill:#95e1d3
```

### State Management Flow

```mermaid
flowchart LR
    A[User Actions] --> B[Context Providers]
    
    B --> C[UserContext]
    B --> D[InterviewContext]
    B --> E[ConfigurationContext]
    
    C --> F[WebSocket Service]
    D --> F
    E --> G[API Client]
    
    F --> H[Backend WebSocket]
    G --> I[Backend REST API]
    
    H --> J[Update Context]
    I --> J
    
    J --> K[UI Re-render]
    
    style B fill:#ff6b6b
    style F fill:#4ecdc4
    style G fill:#4ecdc4
```

### Interview Page Structure

```mermaid
flowchart TD
    A[Interview Layout] --> B[Header]
    A --> C[Video Participants]
    A --> D[Chat Panel]
    A --> E[Problem Statement]
    A --> F[Live Coding Editor]
    A --> G[Media Controls]
    
    C --> H[useCameraStream Hook]
    D --> I[WebSocket Service]
    F --> I
    G --> J[useAudioStreaming Hook]
    
    I --> K[Backend]
    H --> K
    J --> K
    
    style A fill:#ff6b6b
    style I fill:#4ecdc4
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

