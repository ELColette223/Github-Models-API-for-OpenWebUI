import os
import json
import time
from fastapi import FastAPI, Request, HTTPException
import requests
from fastapi.responses import StreamingResponse, JSONResponse

app = FastAPI()

# Settings for the target API
GITHUB_API_URL = os.getenv("GITHUB_API_URL", 'https://models.inference.ai.azure.com')

# Cache file for models
CACHE_FILE = "/tmp/models_cache.json"
CACHE_DURATION = 1 * 60 * 60  # 1 hour in seconds

# Debug level
def debug_print(*args):
    if os.getenv("LOG_LEVEL", False):
        print(*args)

# Function to fetch models from the API
def fetch_models_from_api():
    try:
        response = requests.get(f"{GITHUB_API_URL}/models")
        response.raise_for_status()
        models = response.json()
        # Save the models to cache (JSON file)
        with open(CACHE_FILE, 'w') as cache_file:
            json.dump(models, cache_file)
        return models
    except requests.RequestException as e:
        raise HTTPException(status_code=502, detail=f"Error fetching models from API: {str(e)}")

# Function to load models from cache or API if the cache is expired
def load_models():
    if os.path.exists(CACHE_FILE):
        # Check if the cache file is older than 12 hours
        last_modified = os.path.getmtime(CACHE_FILE)
        current_time = time.time()
        if (current_time - last_modified) < CACHE_DURATION:
            # Load models from cache
            with open(CACHE_FILE, 'r') as cache_file:
                return json.load(cache_file)
    # If the cache is expired or doesn't exist, fetch models from the API
    return fetch_models_from_api()

# Global variable to store models, loaded on demand
models = load_models()

# Function to get the model name using either the friendly_name or the name
def get_model_name(model_id_or_friendly_name):
    global models
    for model in models:
        # Check if model is 'id'
        if model['id'] == model_id_or_friendly_name:
            debug_print("Model found:", model['name'])
            return model['name']
        
        # Check if model is 'friendly_name' or 'name'
        if model['friendly_name'] == model_id_or_friendly_name or model['name'] == model_id_or_friendly_name:
            debug_print("Model found:", model['name'])
            return model['name']  # Always return the 'name', not 'friendly_name'
    return None

# Função para streaming de resposta
async def stream_response(response):
    try:
        for chunk in response.iter_content(chunk_size=1024):
            if chunk:
                yield chunk.decode(errors="ignore")  # Evita que caracteres corrompidos quebrem o stream
    except requests.exceptions.ChunkedEncodingError:
        debug_print("Erro: Resposta interrompida pelo servidor.")
        yield "Error: Response was interrupted."

# Função para streaming de eventos
async def event_stream_response(response):
    for chunk in response.iter_content(chunk_size=1024):
        if chunk:
            yield chunk  # Não decodifica, pois o formato `event-stream` deve ser transmitido diretamente

# Route for proxy
@app.api_route("/{path:path}", methods=["GET", "POST"])
async def proxy_all_requests(request: Request, path: str):
    global models
    MODEL_NAME = None
    model = None
    method = request.method

    # Extract the request body, if it exists
    try:
        body = await request.json()
    except:
        body = None

    original_headers = dict(request.headers)

    # Get the model from the body (Open WebUI standard)
    if body:
        model = body.get('model', None)  # Modelo especificado no corpo

    debug_print("MODEL:", model)

    if model:
        # Now the function checks if the provided name is a 'name' or 'friendly_name'
        model_name = get_model_name(model)
        if model_name:
            MODEL_NAME = model_name
        else:
            return JSONResponse(
                status_code=400,
                content=[{
                    "error": {
                        "code": "no_model_name",
                        "message": "No model specified in request. Please provide a model name in the request body or as a x-ms-model-mesh-model-name header.",
                        "details": None
                    }
                }]
            )

    # Debugging: print the headers and request body
    debug_print("HEADERS RECEIVED:", original_headers)
    debug_print("BODY RECEIVED:", body)
    debug_print("MODEL_NAME:", MODEL_NAME)

    # Extract the authorization token from the original request
    auth_header = original_headers.get('authorization', original_headers.get('Authorization', None))
    if not method == "GET":
        if not auth_header:
            raise HTTPException(status_code=401, detail="Authorization header is missing")

    # Build the headers for the request that will be sent to the target API
    headers = {
        'Connection': 'keep-alive',  # Keep the connection alive
        'Authorization': auth_header,  # Use the client's authorization token
        'Content-Type': original_headers.get('content-type', 'application/json')
    }

    # Include 'x-ms-model-mesh-model-name' only if MODEL_NAME is defined
    if MODEL_NAME:
        headers['x-ms-model-mesh-model-name'] = MODEL_NAME

    # Build the URL for the target API, replicating the path of the original request
    target_url = f"{GITHUB_API_URL}/{path}"

    # Decide the HTTP method and send the corresponding request
    try:
        if method == "GET":
            response = requests.get(target_url, headers=headers, stream=True)
        elif method == "POST":
            response = requests.post(target_url, json=body, headers=headers, stream=True)
        else:
            raise HTTPException(status_code=405, detail="Unsupported method")

        # Checking the content type and handling the response appropriately
        content_type = response.headers.get('Content-Type', '')

        if 'application/json' in content_type:
            # Return the JSON response correctly
            return JSONResponse(content=response.json(), status_code=response.status_code)

        elif 'text/event-stream' in content_type:
            # Explicitly set the content type for StreamingResponse
            return StreamingResponse(event_stream_response(response), media_type="text/event-stream")

        elif 'text' in content_type:
            # Return the response as text
            return JSONResponse(content=response.text, status_code=response.status_code)

        elif 'application/octet-stream' in content_type or 'stream' in content_type:
            # Return a streaming response if the content is a stream
            return StreamingResponse(stream_response(response), media_type=content_type)

        else:
            # Return a default response if the content type is unknown
            return JSONResponse(content={"message": "Unknown response type from target"}, status_code=response.status_code)

    except requests.RequestException as e:
        raise HTTPException(status_code=502, detail=f"Error forwarding request: {str(e)}")
