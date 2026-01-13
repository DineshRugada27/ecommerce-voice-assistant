# E-commerce Voice Bot

A real-time voice-powered e-commerce shopping assistant built with LiveKit, OpenAI, Deepgram, and ElevenLabs. This application enables customers to interact with an AI assistant through natural voice conversations to search for products, get product information, check order status, and receive shopping assistance.

## 📋 Table of Contents

- [Quick Start - Configuration & Running](#quick-start---configuration--running)
- [Overview](#overview)
- [Architecture & Workflow](#architecture--workflow)
- [Project Structure](#project-structure)
- [API Keys & Services](#api-keys--services)
- [Backend Components](#backend-components)
- [Frontend Components](#frontend-components)
- [Backend File Overview](#backend-file-overview)
- [Additional Notes](#additional-notes)
- [Troubleshooting](#troubleshooting)
- [Additional Resources](#additional-resources)
- [License](#license)

---

## 🚀 Quick Start - Configuration & Running

### Prerequisites

- **Python 3.11+** (recommended 3.11 or 3.12)
- **Node.js 18+** and **pnpm** (or npm)
- **Virtual environment** (venv, conda, or virtualenv)

### Step 1: Create Virtual Environment

```bash
# Navigate to project root
cd ecommerce_voicebot

# Option A: Using venv (Recommended)
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Option B: Using conda
conda create -n voicebot python=3.11 -y
conda activate voicebot
```

### Step 2: Install Backend Dependencies

```bash
# Navigate to backend directory
cd ecommerce_voicebot/backend

# Install all Python dependencies
pip install -r requirements.txt
pip install "livekit-agents[openai,deepgram,elevenlabs,silero,turn-detector]~=1.0"
pip install "livekit-plugins-noise-cancellation~=0.2"
pip install python-dotenv
```

### Step 3: Install Frontend Dependencies

```bash
# Navigate to frontend directory
cd ../frontend

# Install dependencies (using pnpm)
pnpm install

# Or using npm
npm install
```

### Step 4: Download Required Model Files (Optional)

```bash
# Navigate back to backend
cd ../backend

# Download required model files for VAD and other components
python agent.py download-files
```

### Step 5: Configure Environment Variables

Create a `.env` file in the root `ecommerce_voicebot/` directory:

```bash
# From the root directory
cd ecommerce_voicebot
cp .env.example .env
```

Edit `.env` and add your API keys:

```env
# LiveKit Configuration
LIVEKIT_API_KEY="your_livekit_api_key_here"
LIVEKIT_API_SECRET="your_livekit_api_secret_here"
LIVEKIT_URL="wss://your-project.livekit.cloud"

# OpenAI Configuration
OPENAI_API_KEY="your_openai_api_key_here"

# Deepgram Configuration
DEEPGRAM_API_KEY="your_deepgram_api_key_here"

# ElevenLabs Configuration
ELEVENLABS_API_KEY="your_elevenlabs_api_key_here"

# Optional: Backend API URL
BACKEND_API_URL="http://localhost:5000"
```

**Note**: 
- The backend Python files automatically load from the root `.env` file
- The frontend will automatically sync the root `.env` file when you run `pnpm run dev`
- Never commit `.env` files to version control

### Step 6: Run the Application

#### Option A: Full Stack (Recommended)

**Terminal 1 - Start Backend Agent:**
```bash
# Make sure virtual environment is activated
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# Navigate to backend
cd ecommerce_voicebot/backend

# Start the voice agent (development mode)
python agent.py dev
```

**Expected Output**: 
- Agent worker starting
- RAG system initializing
- Agent registered with LiveKit
- Waiting for connections

**Terminal 2 - Start Flask Token Server (Optional but Recommended):**
```bash
# Make sure virtual environment is activated
# Navigate to backend
cd ecommerce_voicebot/backend
python api.py
```

**Expected Output**: 
- `* Running on http://0.0.0.0:5000`
- Server is ready to generate tokens

**Terminal 3 - Start Frontend:**
```bash
# Navigate to frontend
cd ecommerce_voicebot/frontend

# Start development server
pnpm run dev
# Or: npm run dev
```

**Expected Output**: 
- Next.js server starting
- `✓ Ready in X.Xs`
- `Local: http://localhost:3000`

**Access the Application:**
1. Open your browser and navigate to `http://localhost:3000`
2. The frontend will automatically connect to LiveKit
3. Once connected, you can start speaking to the voice assistant

#### Option B: Standalone HTML Demo

**Terminal 1 - Start Flask Server:**
```bash
cd ecommerce_voicebot/backend
python api.py
```

**Terminal 2 - Start Backend Agent:**
```bash
cd ecommerce_voicebot/backend
python agent.py start
```

**Terminal 3 - Start Frontend:**
```bash
cd ecommerce_voicebot/frontend
pnpm run dev
```


## 🎯 Overview

This project consists of two main parts:

1. **Backend**: Python-based voice AI agent using LiveKit Agents SDK
2. **Frontend**: Next.js React application with LiveKit integration

The system provides:
- **Real-time voice interaction** using LiveKit infrastructure
- **Speech-to-Text (STT)** via Deepgram Nova-3
- **Natural Language Processing** via OpenAI GPT-4o-mini
- **Text-to-Speech (TTS)** via ElevenLabs Eleven Turbo v2.5
- **RAG (Retrieval Augmented Generation)** for product catalog queries
- **Voice Activity Detection (VAD)** and turn detection
- **Noise cancellation** for better audio quality

---

## 🏗️ Architecture & Workflow

### System Flow

```
┌──────────────┐         ┌──────────────┐         ┌─────────────────┐
│   Frontend   │────────▶│  Next.js API │         │  LiveKit Cloud  │
│  (Next.js)   │         │  /connection │         │  (WebSocket)    │
│              │         │   -details   │         │                 │
└──────┬───────┘         └──────┬───────┘         └────────┬────────┘
       │                        │                          │
       │  1. Request Token      │                          │
       │────────────────────────▶                          │
       │                        │                          │
       │  2. Get JWT Token      │                          │
       │◀────────────────────────                          │
       │                        │                          │
       │  3. Connect to Room   │                          │
       │──────────────────────────────────────────────────▶│
       │                        │                          │
       │  4. Audio Stream       │                          │
       │◀──────────────────────┼──────────────────────────│
       │                        │                          │
       │                        │         ┌───────────────┴──────┐
       │                        │         │   agent.py            │
       │                        │         │   (Voice AI Agent)    │
       │                        │         │   - STT (Deepgram)     │
       │                        │         │   - LLM (GPT-4o-mini) │
       │                        │         │   - TTS (ElevenLabs)  │
       │                        │         │   - RAG System        │
       │                        │         └───────────────────────┘
       │                        │
       │  5. Fallback Token      │
       │     (if needed)         │
       │────────────────────────▶│
       │                        │
       │   Flask API             │
       │   /getToken             │
       │                        │
```

### Detailed Workflow

1. **User opens frontend** → Next.js application loads
2. **Frontend requests connection** → Calls `/api/connection-details` endpoint
3. **Token generation**:
   - First attempt: Tries Flask backend `/getToken` endpoint (if available)
   - Fallback: Generates token locally using LiveKit Server SDK
4. **Connection established** → Frontend connects to LiveKit room via WebSocket
5. **Agent joins room** → Backend agent (`agent.py`) automatically joins when user connects
6. **Voice interaction**:
   - User speaks → Audio captured by frontend
   - STT converts speech to text (Deepgram Nova-3)
   - RAG system retrieves relevant product information (if query is product-related)
   - LLM generates response (GPT-4o-mini with context)
   - TTS converts response to speech (ElevenLabs Eleven Turbo v2.5)
   - Audio streamed back to user
7. **Real-time conversation** continues with turn detection and VAD

---

## 📁 Project Structure

```
ecommerce_voicebot/
├── backend/                    # Python backend
│   ├── agent.py               # Main voice AI agent
│   ├── api.py                 # Flask token server
│   ├── rag_system.py          # RAG system for product queries
│   ├── get_voices.py          # Utility to fetch Cartesia voices
│   ├── ecommerce_voicebot_knowledge_base.json  # Product catalog data
│   ├── chroma_db/             # ChromaDB vector database
│   ├── requirements.txt        # Python dependencies
│   └── .env_example           # Environment variables template
│
├── frontend/                   # Next.js frontend
│   ├── app/
│   │   ├── api/
│   │   │   └── connection-details/
│   │   │       └── route.ts   # Next.js API route for tokens
│   │   ├── (app)/             # App routes
│   │   └── layout.tsx         # Root layout
│   ├── components/
│   │   ├── app/               # App-specific components
│   │   └── livekit/           # LiveKit UI components
│   ├── hooks/                 # React hooks
│   ├── lib/                   # Utility functions
│   └── package.json           # Node.js dependencies
│
├── index.html                 # Standalone HTML demo (alternative UI)
├── .env                       # Environment variables (create from .env.example)
└── README.md                  # This file
```

---

## 🔑 API Keys & Services

### Required API Keys

You need to obtain API keys from the following services:

#### 1. **LiveKit** (Required)
- **What it is**: Real-time communication infrastructure for audio/video
- **Where to get it**: 
  - Sign up at [https://livekit.io](https://livekit.io)
  - Create a project in the LiveKit Cloud dashboard
  - Get your API Key, API Secret, and WebSocket URL
- **Environment variables**:
  - `LIVEKIT_API_KEY` - Your LiveKit API key
  - `LIVEKIT_API_SECRET` - Your LiveKit API secret
  - `LIVEKIT_URL` - Your LiveKit WebSocket URL (e.g., `wss://your-project.livekit.cloud`)

#### 2. **OpenAI** (Required)
- **What it is**: Provides GPT-4o-mini for Language Model (LLM)
- **Where to get it**: 
  - Sign up at [https://platform.openai.com](https://platform.openai.com)
  - Go to API Keys section
  - Create a new API key
- **Environment variable**:
  - `OPENAI_API_KEY` - Your OpenAI API key
- **Usage**: 
  - Language Model (GPT-4o-mini)

#### 3. **Deepgram** (Required)
- **What it is**: High-accuracy speech-to-text service
- **Where to get it**: 
  - Sign up at [https://deepgram.com](https://deepgram.com)
  - Get your API key from the dashboard
- **Environment variable**:
  - `DEEPGRAM_API_KEY` - Your Deepgram API key
- **Usage**: 
  - Speech-to-Text (Nova-3 model)
  - Model: `deepgram/nova-3:en`

#### 4. **ElevenLabs** (Required)
- **What it is**: High-quality text-to-speech service
- **Where to get it**: 
  - Sign up at [https://elevenlabs.io](https://elevenlabs.io)
  - Get your API key from the dashboard
- **Environment variable**:
  - `ELEVENLABS_API_KEY` - Your ElevenLabs API key
- **Usage**: 
  - Text-to-Speech (Eleven Turbo v2.5 model)
  - Voice ID: `Xb7hH8MSUJpSbSDYk0k2`

### Optional Environment Variables

- `BACKEND_API_URL` - Flask backend URL (default: `http://localhost:5000`)

---

## 🔧 Backend Components

### Core Technologies

- **LiveKit Agents SDK**: Framework for building voice AI agents
- **OpenAI**: GPT-4o-mini for Language Model (LLM)
- **Deepgram**: Nova-3 model for Speech-to-Text (STT)
- **ElevenLabs**: Eleven Turbo v2.5 model for Text-to-Speech (TTS)
- **ChromaDB**: Vector database for RAG
- **Sentence Transformers**: Embeddings for semantic search
- **Flask**: Lightweight web server for token generation
- **Silero VAD**: Voice activity detection
- **Noise Cancellation**: Background noise filtering

---

## 🎨 Frontend Components

### Core Technologies

- **Next.js 15**: React framework with App Router
- **LiveKit Client SDK**: Real-time communication client
- **LiveKit Components React**: Pre-built UI components
- **TypeScript**: Type-safe JavaScript
- **Tailwind CSS**: Utility-first CSS framework

### Key Features

- Real-time voice interaction UI
- Chat transcript display
- Audio controls (mute/unmute, device selection)
- Responsive design
- Dark/light theme support

---

## 📄 Backend File Overview

### 1. `agent.py` (188 lines)

**Purpose**: Main voice AI agent that handles real-time voice interactions.

**Key Components**:
- **Assistant Class**: Extends `Agent` class with RAG integration
  - Initializes RAG system on startup
  - Defines agent instructions and capabilities
  - Intercepts user messages to add product context via RAG
- **on_user_turn_completed()**: 
  - Extracts user text from messages
  - Checks if query is product-related using RAG
  - Retrieves relevant product chunks from knowledge base
  - Injects context into LLM conversation
  - Handles general shopping questions with e-commerce knowledge
- **entrypoint()**: 
  - Sets up AgentSession with STT, LLM, TTS, VAD, and turn detection
  - Configures noise cancellation
  - Starts session and generates welcome message

**Technologies Used**:
- LiveKit Agents SDK
- OpenAI (GPT-4o-mini LLM)
- Deepgram (Nova-3 STT)
- ElevenLabs (Eleven Turbo v2.5 TTS)
- Silero VAD
- Noise cancellation plugin

**Dependencies**: 

---

### 2. `api.py` (64 lines)

**Purpose**: Flask web server that generates LiveKit JWT tokens for authentication.

**Endpoints**:
- `GET /`: Health check endpoint
- `GET /getToken?name=<name>&room=<room>`: Generates JWT token for LiveKit access
  - Parameters:
    - `name` (optional): Participant name (default: "guest")
    - `room` (optional): Room name (default: auto-generated)

**Functionality**:
- Loads LiveKit credentials from environment variables
- Generates secure JWT tokens using LiveKit SDK
- Creates room grants for joining LiveKit rooms
- Returns token, room name, and identity

**Technologies Used**:
- Flask web framework
- Flask-CORS for cross-origin requests
- LiveKit Server SDK
- python-dotenv for environment variables

**Port**: 5000 (default)

---

### 3. `rag_system.py` (355 lines)

**Purpose**: Retrieval Augmented Generation system for product catalog queries.

**Key Components**:
- **RAGSystem Class**: Main RAG implementation
  - **__init__()**: 
    - Initializes ChromaDB vector database
    - Loads SentenceTransformer model (`all-MiniLM-L6-v2`)
    - Creates or loads collection for embeddings
    - Builds index from JSON knowledge base
  - **_load_json_data()**: Loads product catalog JSON file
  - **_extract_chunks_from_json()**: 
    - Extracts product information (name, price, specs, reviews)
    - Extracts order information (status, tracking, items)
    - Extracts policies (shipping, returns, etc.)
    - Extracts FAQs
    - Formats data into searchable text chunks
  - **_initialize_index()**: 
    - Checks if index exists
    - Builds index if needed
    - Embeds chunks using SentenceTransformer
    - Stores in ChromaDB
  - **is_relevant_query()**: 
    - Determines if user query is product-related
    - Uses keyword matching and semantic similarity
    - Returns boolean
  - **retrieve()**: 
    - Performs semantic search on knowledge base
    - Returns top-k most relevant chunks
    - Uses cosine similarity in ChromaDB

**Data Sources**:
- `ecommerce_voicebot_knowledge_base.json`: Product catalog, orders, policies, FAQs

**Technologies Used**:
- ChromaDB (vector database)
- Sentence Transformers (embeddings)
- JSON parsing

**Storage**: `./chroma_db/` directory (persistent vector database)

---

### 4. `get_voices.py`

**Purpose**: Legacy utility script (not currently used). The project now uses ElevenLabs for TTS.

**Note**: This file is kept for reference but is not part of the active voice agent configuration.

---

### 5. `ecommerce_voicebot_knowledge_base.json`

**Purpose**: Structured knowledge base containing:
- **Products**: Product catalog with details, specs, prices, reviews
- **Orders**: Order history, status, tracking information
- **Policies**: Shipping, returns, refunds, privacy policies
- **FAQs**: Frequently asked questions and answers

**Format**: JSON structure with nested objects and arrays

**Used by**: `rag_system.py` for RAG context retrieval

---

### 6. `requirements.txt`

**Purpose**: Python package dependencies.

**Key Dependencies**:
- `livekit-agents`: LiveKit Agents SDK
- `livekit`: LiveKit core SDK
- `openai`: OpenAI API client
- `flask`: Web framework
- `flask-cors`: CORS support
- `chromadb`: Vector database
- `sentence-transformers`: Embedding models
- `python-dotenv`: Environment variable management
- `livekit-plugins-deepgram`: Deepgram STT plugin
- `livekit-plugins-elevenlabs`: ElevenLabs TTS plugin

---

### 7. `.env_example`

**Purpose**: Template for environment variables.

**Contains**: Placeholder values for all required API keys and configuration

**Usage**: Copy to `.env` and fill in your actual API keys

---

## 🔍 Additional Notes

### RAG System Behavior

- **Product Queries**: When user asks about products, RAG retrieves relevant information from the knowledge base
- **General Queries**: For non-product questions, the system uses general e-commerce knowledge
- **Context Injection**: Retrieved context is injected as system messages before user queries

### Token Generation Flow

1. Frontend requests token from Next.js API route
2. API route first tries Flask backend `/getToken` (if available)
3. If Flask backend unavailable, generates token locally
4. Token includes room configuration for agent assignment

### Development vs Production

#### Backend

- **Development**: 
  ```bash
  python agent.py dev
  ```
  - Hot-reload enabled
  - Watches for file changes
  - More verbose logging

- **Production**: 
  ```bash
  python agent.py start
  ```
  - Optimized for production
  - No file watching
  - Production logging

#### Frontend

- **Development**: 
  ```bash
  pnpm run dev
  ```
  - Hot module replacement
  - Development optimizations
  - Source maps enabled

- **Production**: 
  ```bash
  pnpm run build
  pnpm start
  ```
  - Optimized bundle
  - Production build
  - Runs on port 3000 by default

---

## 🐛 Troubleshooting

### Common Issues

1. **Import errors**: Make sure all dependencies are installed
   ```bash
   pip install -r requirements.txt
   pip install "livekit-agents[openai,deepgram,elevenlabs,silero,turn-detector]~=1.0"
   pip install "livekit-plugins-noise-cancellation~=0.2"
   ```

2. **API key errors**: Verify `.env` file has correct keys and is in the root directory

3. **Connection issues**: Check LiveKit URL and network connectivity

4. **RAG not working**: Ensure `ecommerce_voicebot_knowledge_base.json` exists and is valid JSON

5. **Port conflicts**: Change Flask port in `api.py` if 5000 is in use

6. **Virtual environment not activated**: Make sure to activate venv before running Python scripts

7. **Frontend not connecting**: Check that backend agent is running and registered with LiveKit

---

## 📚 Additional Resources

- [LiveKit Documentation](https://docs.livekit.io/)
- [LiveKit Agents SDK](https://github.com/livekit/agents)
- [OpenAI API Documentation](https://platform.openai.com/docs)
- [Deepgram Documentation](https://developers.deepgram.com/)
- [ElevenLabs Documentation](https://elevenlabs.io/docs)
- [Next.js Documentation](https://nextjs.org/docs)

---

## 📝 License

See individual component licenses in their respective directories.

---

**Built with ❤️ Dinesh Rugada**
