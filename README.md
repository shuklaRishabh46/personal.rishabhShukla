# Attribute Processor

A FastAPI service that analyzes UI screenshots and generates descriptions for clicked elements and user journeys using Amazon Bedrock (Claude 3).

## Features

- **Step Description API** - Analyzes a screenshot with a highlighted element and generates a description
- **Step Retrieval API** - Retrieve saved step descriptions by element ID
- **Journey Summary API** - Takes a list of step descriptions and generates a journey name and summary
- **JSON Database** - Stores step descriptions for quick retrieval

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
AWS_ACCESS_KEY_ID=your_aws_access_key
AWS_SECRET_ACCESS_KEY=your_aws_secret_key
AWS_REGION=eu-central-1
```

**Note:** Requires AWS account with Bedrock access and Claude 3 Sonnet model enabled.

### 5. Run the server (for local development)

```bash
uvicorn main:app --reload --port 8123
```

## API Endpoints

### POST /step-description

Analyzes a screenshot and returns a description of the clicked element. Also saves to database.

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
  "description": "Click here to enter your email address and password to log into the system.",
  "element_id": "id,6ec1a1d.ix,1.tg,c96c6d5.cl,7fc0999.1303c06,3b9c358"
}
```

### GET /step-description/{element_id}

Retrieves a saved step description by element ID.

**Request:**
```bash
curl "http://localhost:8123/step-description/id%2C6ec1a1d.ix%2C1.tg%2Cc96c6d5.cl%2C7fc0999.1303c06%2C3b9c358"
```

**Note:** Special characters in element_id must be URL-encoded (`,` becomes `%2C`).

**Response:**
```json
{
  "result": true,
  "element_id": "id,6ec1a1d.ix,1.tg,c96c6d5.cl,7fc0999.1303c06,3b9c358",
  "description": "Click here to enter your email address and password to log into the system."
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
├── db.json           # JSON database for storing step descriptions
├── requirements.txt  # Python dependencies
├── payload.json      # Sample payload for step-description
├── steps.json        # Sample payload for journey-summary
└── .env              # Environment variables (not in git)
```

## Database Schema

`db.json` stores step descriptions:

```json
{
  "steps": {
    "element_id_here": {
      "element_id": "element_id_here",
      "description": "Click here to..."
    }
  }
}
```
