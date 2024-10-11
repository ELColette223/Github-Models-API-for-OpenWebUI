API Proxy for OpenWebUI to GitHub Models API
============================================

This project provides an API proxy that converts requests for model inference from [OpenWebUI](https://github.com/open-webui/open-webui) into requests compatible with the GitHub models API. It enables the use of models provided by GitHub in OpenWebUI by mimicking the OpenAI API format.

How It Works
------------

The API receives requests in the same format used by OpenWebUI (compatible with OpenAI's API), translates the requests into the GitHub models API format, and returns the results in a format that OpenWebUI can use.  

You need to have access to [Github Models](https://github.com/marketplace/models) and an personal API.

Running the API
---------------

### Using Docker

1.  **Build the Docker image:**
    
        docker build -t openwebui-proxy-api .
    
2.  **Run the Docker container:**
    
        docker run -d -p 8000:80 --name openwebui-proxy openwebui-proxy-api
    
3.  **Access the API:**
    
    The API will be available at [http://localhost:8000](http://localhost:8000).
    

### Using Docker Compose

1.  **Run Docker Compose:**
    
        docker-compose up --build
    
2.  **Access the API:**
    
    The API will be available at [http://localhost:8000](http://localhost:8000).
    

### Running Locally

1.  **Install dependencies:**
    
        pip install -r requirements.txt
    
2.  **Run the API:**
    
        python3 -m uvicorn main:app --host 0.0.0.0 --port 80 --reload --log-level debug
    
3.  **Access the API:**
    
    The API will be available at [http://localhost:80](http://localhost:80).

Disclaimer
----------

This project was developed for testing and learning purposes only. Use of this proxy API must be done responsibly, and I am not responsible for any misuse or any consequences resulting from its use, including, but not limited to, blocks or restrictions imposed by GitHub or any other external service.

The user of this project must be aware that inappropriate use may violate the terms of service of the platforms involved. Make sure you understand and follow the terms of use for each service before using this api. This project offers no guarantee of operation and is distributed "as is".