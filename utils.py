import base64
import os
import json
import boto3
from io import BytesIO
from PIL import Image, ImageDraw
from dotenv import load_dotenv

load_dotenv()

bedrock_client = boto3.client(
    "bedrock-runtime",
    region_name=os.getenv("AWS_REGION", "eu-central-1"),
)

DB_FILE = "db.json"

def load_db() -> dict:
    try:
        with open(DB_FILE, 'r') as f:
            return json.load(f)
    except:
        return {"steps": {}}

def save_db(data: dict):
    with open(DB_FILE, 'w') as f:
        json.dump(data, f, indent=2)

def get_step_by_element_id(element_id: str) -> dict:
    db = load_db()
    step = db["steps"].get(element_id)
    if step:
        step["counter"] = step.get("counter", 0) + 1
        db["steps"][element_id] = step
        save_db(db)
    return step

def read_step_by_element_id(element_id: str) -> dict:
    db = load_db()
    step = db["steps"].get(element_id)
    return step

def save_step_description(element_id: str, description: str, name: str, counter: int):
    db = load_db()
    db["steps"][element_id] = {"element_id": element_id, "description": description, "name": name, "counter": counter}
    save_db(db)

def get_clicked_element_id(json_data: dict) -> str:
    return json_data['elementIds'][-1]

def get_clicked_element_position(json_data: dict) -> dict:
    clicked_element = json_data['elementIds'][-1]
    return json_data['attributes'][clicked_element]['metadata']['domRect']

def get_image_from_payload(json_data: dict) -> Image.Image:
    image_string = json_data['image']
    
    if ',' in image_string:
        image_string = image_string.split(',')[1]
    
    image_bytes = base64.b64decode(image_string)
    return Image.open(BytesIO(image_bytes))

def highlight_clicked_element_on_image(image: Image.Image, json_data: dict, element_position: dict) -> Image.Image:
    scale_x = 1.0
    scale_y = 1.0
    
    # Find first element with non-zero dimensions to calculate scale (handles modals)
    for element_id in json_data['elementIds']:
        rect = json_data['attributes'][element_id]['metadata']['domRect']
        if rect['width'] > 0 and rect['height'] > 0:
            scale_x = image.width / rect['width']
            scale_y = image.height / rect['height']
            print(f"Using element {element_id} for scale calculation")
            print(f"Element rect: {rect['width']}x{rect['height']}")
            break
    
    print(f"Image size: {image.width}x{image.height}")
    print(f"Scale factor: {scale_x}, {scale_y}")
    
    draw = ImageDraw.Draw(image)
    
    x = element_position['x'] * scale_x
    y = element_position['y'] * scale_y
    width = element_position['width'] * scale_x
    height = element_position['height'] * scale_y
    
    draw.rectangle(
        [x, y, x + width, y + height],
        outline="red",
        width=5
    )
    
    return image

def resize_image_for_api(image: Image.Image, max_size: int = 1024) -> Image.Image:
    width, height = image.size
    
    if width <= max_size and height <= max_size:
        return image
    
    if width > height:
        new_width = max_size
        new_height = int(height * (max_size / width))
    else:
        new_height = max_size
        new_width = int(width * (max_size / height))
    
    resized = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
    print(f"Resized image from {width}x{height} to {new_width}x{new_height}")
    return resized

async def get_element_description(image: Image.Image) -> str:
    resized_image = resize_image_for_api(image, max_size=1024)
    
    buffer = BytesIO()
    resized_image.save(buffer, format="PNG", optimize=True)
    image_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
    
    print(f"Image size for API: {len(image_base64) // 1024} KB")
    
    payload = {
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": 300,
        "messages": [{
            "role": "user",
            "content": [
                {"type": "image", "source": {"type": "base64", "media_type": "image/png", "data": image_base64}},
                {"type": "text", "text": "Describe the UI element highlighted with a red rectangle in this screenshot. Make no reference to element itself only reply with description which starts with \"Click here to\" and then a one liner what will happen. also send me a name of this step which should be max 2 words format should be json string like this: {\"name\": \"Step Name\", description: \"Step Description\"}"}
            ]
        }]
    }
    
    response = bedrock_client.invoke_model(
        modelId="anthropic.claude-3-haiku-20240307-v1:0",
        contentType="application/json",
        accept="application/json",
        body=json.dumps(payload)
    )
    
    result = json.loads(response['body'].read())
    json_result = json.loads(result['content'][0]['text'])
    print(f"JSON Result: {json_result}")
    name = json_result['name']
    description = json_result['description']
    print(f"Name: {name}, Description: {description}")
    return {"name": name, "description": description}

async def generate_journey_summary(steps: list) -> dict:
    steps_text = "\n".join([f"Step {i+1}: {step}" for i, step in enumerate(steps)])
    
    payload = {
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": 200,
        "messages": [{
            "role": "user",
            "content": f"Given these steps of a user journey:\n{steps_text}\n\nProvide a JSON response with:\n1. \"name\": A short name (2-4 words)\n2. \"description\": A one-liner\n\nRespond ONLY with valid JSON, no markdown."
        }]
    }
    
    response = bedrock_client.invoke_model(
        modelId="anthropic.claude-3-haiku-20240307-v1:0",
        contentType="application/json",
        accept="application/json",
        body=json.dumps(payload)
    )
    
    result = json.loads(response['body'].read())
    
    try:
        content = result['content'][0]['text']
        content = content.strip()
        if content.startswith('```json'):
            content = content[7:]
        if content.startswith('```'):
            content = content[3:]
        if content.endswith('```'):
            content = content[:-3]
        content = content.strip()
        return json.loads(content)
    except Exception as e:
        print(f"JSON parse error: {e}")
        return {"name": "User Journey", "description": content}

async def generate_graph_summary(json_data: dict) -> dict:

    graph_data = [
        {"from": "Create Button", "to": "Create Issue", "flow": 9},
        {"from": "Create Issue", "to": "Select Bug", "flow": 7},
        {"from": "Select Bug", "to": "Select Design", "flow": 4},
        {"from": "Select Bug", "to": "Task", "flow": 3},
        {"from": "Select Design", "to": "Create Issue", "flow": 2},
        {"from": "Create Button", "to": "Close Window", "flow": 2},
        {"from": "Recent Spaces", "to": "View all", "flow": 1},
        {"from": "View all", "to": "Create Item", "flow": 1},
        {"from": "Create Item", "to": "Learn more", "flow": 1},
        {"from": "Starred Items", "to": "Access Apps", "flow": 1},
    ] 
    return graph_data