from fastapi import FastAPI, Request
from dotenv import load_dotenv
from utils import describe_element_with_groq, get_clicked_element_position, get_image_from_payload, highlight_clicked_element_on_image, generate_journey_summary

load_dotenv()

app = FastAPI()

@app.post("/step-description")
async def step_description(request: Request):
    try:
        json_data = await request.json()
        
        clickedElementDataPosition = get_clicked_element_position(json_data)
        image = get_image_from_payload(json_data)
        image = highlight_clicked_element_on_image(image, json_data, clickedElementDataPosition)
        image.save("output_image.png")
        description = await describe_element_with_groq(image)
        
        return {"result": True, "description": description}
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
        
        return {"result": True, "name": summary.get("name"), "description": summary.get("description")}
    except Exception as e:
        print(f"Error: {e}")
        return {"result": False, "error": str(e)}
