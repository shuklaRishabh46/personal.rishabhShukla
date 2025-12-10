from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from utils import (
    get_element_description, 
    get_clicked_element_position, 
    get_image_from_payload, 
    highlight_clicked_element_on_image, 
    generate_journey_summary,
    get_step_by_element_id,
    save_step_description,
    get_clicked_element_id
)

load_dotenv()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/step-description")
async def step_description(request: Request):
    try:
        json_data = await request.json()
        clicked_element_id = get_clicked_element_id(json_data)
        
        existing_step = get_step_by_element_id(clicked_element_id)
        if existing_step:
            return {"result": True, "description": existing_step["description"], "element_id": clicked_element_id, "cached": True}
        
        clickedElementDataPosition = get_clicked_element_position(json_data)
        image = get_image_from_payload(json_data)
        image = highlight_clicked_element_on_image(image, json_data, clickedElementDataPosition)
        description = await get_element_description(image)
        
        save_step_description(clicked_element_id, description, 1)
        
        return {"result": True, "description": description, "element_id": clicked_element_id}
    except Exception as e:
        print(f"Error: {e}")
        return {"result": False, "error": str(e)}

@app.get("/step-description/{element_id}")
async def get_step_description(element_id: str):
    try:
        step = get_step_by_element_id(element_id)
        
        if not step:
            return {"result": False, "error": "Step not found"}
        
        return {"result": True, "element_id": step["element_id"], "description": step["description"]}
    except Exception as e:
        print(f"Error: {e}")
        return {"result": False, "error": str(e)}

@app.post("/journey-summary")
async def journey_summary(request: Request):
    try:
        json_data = await request.json()
        steps = json_data.get("steps", [])
        
        if not steps:
            return {"result": False, "error": "No steps provided"}
        
        summary = await generate_journey_summary(steps)
        print(summary)
        return {"result": True, "name": summary.get("name"), "description": summary.get("description")}
    except Exception as e:
        print(f"Error: {e}")
        return {"result": False, "error": str(e)}
