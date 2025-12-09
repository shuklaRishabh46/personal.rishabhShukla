import base64
import os
import json
import boto3
from io import BytesIO
from PIL import Image, ImageDraw

bedrock_client = boto3.client(
    "bedrock-runtime",
    region_name=os.getenv("AWS_REGION", "eu-central-1"),
)

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
    root_element = json_data['elementIds'][0]
    root_rect = json_data['attributes'][root_element]['metadata']['domRect']
    
    scale_x = image.width / root_rect['width']
    scale_y = image.height / root_rect['height']
    
    print(f"Image size: {image.width}x{image.height}")
    print(f"Root rect: {root_rect['width']}x{root_rect['height']}")
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
                {"type": "text", "text": "Describe the UI element highlighted with a red rectangle in this screenshot. Make no reference to element itself only reply with description which starts with \"Click here to\" and then a one liner what will happen."}
            ]
        }]
    }
    
    response = bedrock_client.invoke_model(
        modelId="anthropic.claude-3-sonnet-20240229-v1:0",
        contentType="application/json",
        accept="application/json",
        body=json.dumps(payload)
    )
    
    result = json.loads(response['body'].read())
    print(result)
    
    return result['content'][0]['text']

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
        modelId="anthropic.claude-3-sonnet-20240229-v1:0",
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
