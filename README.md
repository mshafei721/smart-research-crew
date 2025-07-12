# Smart Research Crew (SRC)

An AI-powered research report generator that enables knowledge workers to generate publication-grade research reports in minutes using autonomous agents.

## 🚀 Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Start backend server
python main.py --server

# In another terminal, start frontend
cd frontend && npm install && npm run dev

# Or run CLI mode directly
python main.py
```

## 📁 Project Structure

```
smart-research-crew/
├── main.py               # ✨ Main entry point (CLI & Server)
├── backend/              # FastAPI backend with BeeAI agents
│   ├── src/
│   │   ├── agents/       # Agent implementations (SectionResearcher, ReportAssembler)
│   │   ├── api/          # FastAPI routes (/sse endpoint)
│   │   ├── cache/        # Redis caching layer
│   │   ├── config/       # Settings and logging
│   │   └── utils/        # Utility functions
│   └── tests/            # Unit and integration tests
├── frontend/             # React + Vite + Tailwind CSS
├── tests/                # Testing infrastructure
├── examples/             # Demo scripts and usage examples
└── requirements.txt      # Python dependencies
```

## 💻 Usage

### CLI Mode
```bash
python main.py
```
Interactive research mode where you can specify topics and sections.

### Server Mode
```bash
python main.py --server
```
Starts the FastAPI backend server on port 8000.

### Web Interface
After starting the server, launch the frontend:
```bash
cd frontend
npm run dev
```
Access the web interface at http://localhost:5173

## 🏗️ Architecture

- **Frontend**: React + Vite + Tailwind CSS
- **Backend**: FastAPI + BeeAI ReActAgents
- **Streaming**: Server-Sent Events (SSE) for real-time updates
- **Research**: DuckDuckGo search integration

## 📋 Features

- Interactive wizard for research configuration
- Section-level autonomous agents
- Real-time streaming of research progress
- Publication-grade markdown output with citations
- Both CLI and web interfaces

## 🔧 Configuration

Set your OpenAI API key:
```bash
echo "OPENAI_API_KEY=your_key_here" > .env
```

## 📄 License

MIT License - see LICENSE file for details.
