# Attribute Processor

A FastAPI service that analyzes UI screenshots and generates descriptions for clicked elements and user journeys.

## Features

- **Step Description API** - Analyzes a screenshot with a highlighted element and generates a description
- **Journey Summary API** - Takes a list of step descriptions and generates a journey name and summary

## Setup

### 1. Clone the repository

```bash
git clone <repository-url>
cd attributeProcessor
```

### 2. Create virtual environment

```bash
python -m venv .venv
source .venv/bin/activate  # On macOS/Linux
# or
.venv\Scripts\activate  # On Windows
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

Create a `.env` file in the project root:

```
GROQ_API_KEY=your_groq_api_key_here
```

Get your free Groq API key at: https://console.groq.com/keys

### 5. Run the server(for local development)

```bash
uvicorn main:app --reload --port 8123
```

## API Endpoints

### POST /step-description

Analyzes a screenshot and returns a description of the clicked element.

**Request:** (to test locally)
```bash
curl -X POST http://localhost:8123/step-description \
  -H "Content-Type: application/json" \
  --data-binary @payload.json
```

**Response:**
```json
{
  "result": true,
  "description": "Click here to access Dashboard v3, an alternative dashboard layout option."
}
```

### POST /journey-summary

Generates a journey name and description from a list of steps.

**Request:**
```bash
curl -X POST http://localhost:8123/journey-summary \
  -H "Content-Type: application/json" \
  -d '{"steps": ["Click here to open settings", "Click here to change password", "Click here to save changes"]}'
```

**Response:**
```json
{
  "result": true,
  "name": "Password Update",
  "description": "User updates their account password through settings"
}
```

## Project Structure

```
attributeProcessor/
├── main.py           # FastAPI application and endpoints
├── utils.py          # Utility functions for image processing and LLM calls
├── requirements.txt  # Python dependencies
├── payload.json      # Sample payload for step-description
├── steps.json        # Sample payload for journey-summary
└── .env              # Environment variables (not in git)
```
