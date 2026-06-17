from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi


def custom_openapi(app: FastAPI):
    if app.openapi_schema:
        return app.openapi_schema
    
    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )
    
    if "components" not in openapi_schema:
        openapi_schema["components"] = {}
    
    if "securitySchemes" not in openapi_schema["components"]:
        openapi_schema["components"]["securitySchemes"] = {}
    
    existing_schemes = openapi_schema["components"]["securitySchemes"]
    
    bearer_scheme_found = False
    for scheme_name in existing_schemes:
        scheme = existing_schemes[scheme_name]
        if isinstance(scheme, dict) and scheme.get("type") == "http" and scheme.get("scheme") == "bearer":
            scheme["bearerFormat"] = "JWT"
            scheme["description"] = "Enter JWT token obtained from /v1/authentication endpoint. Click 'Authorize' button above and paste your token."
            bearer_scheme_found = True
            break
    
    if not bearer_scheme_found:
        openapi_schema["components"]["securitySchemes"]["HTTPBearer"] = {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
            "description": "Enter JWT token obtained from /v1/authentication endpoint. Click 'Authorize' button above and paste your token."
        }
    
    # Replace auto-generated Body schema references with inline schema
    body_schemas = {}
    if "components" in openapi_schema and "schemas" in openapi_schema["components"]:
        schemas = openapi_schema["components"]["schemas"]
        body_schemas = {
            key: value for key, value in schemas.items() 
            if key.startswith("Body_")
        }
    
    if "paths" in openapi_schema:
        for path, methods in openapi_schema["paths"].items():
            for method, details in methods.items():
                if "requestBody" in details:
                    request_body = details["requestBody"]
                    if "content" in request_body:
                        for content_type, content_details in request_body["content"].items():
                            if "schema" in content_details and "$ref" in content_details["schema"]:
                                ref = content_details["schema"]["$ref"]
                                # If it is a Body_ reference, replace with inline schema from components
                                if "Body_" in ref:
                                    schema_name = ref.split("/")[-1]
                                    if schema_name in body_schemas:
                                        content_details["schema"] = body_schemas[schema_name]
                                    else:
                                        content_details["schema"] = {
                                            "type": "object",
                                            "properties": {
                                                "file": {
                                                    "type": "string",
                                                    "format": "binary",
                                                    "description": "CSV file from Falcon to be uploaded and parsed"
                                                }
                                            },
                                            "required": ["file"]
                                        }
    
    # Filter out auto-generated Body schemas after using them
    if "components" in openapi_schema and "schemas" in openapi_schema["components"]:
        schemas = openapi_schema["components"]["schemas"]
        filtered_schemas = {
            key: value for key, value in schemas.items() 
            if not key.startswith("Body_")
        }
        openapi_schema["components"]["schemas"] = filtered_schemas
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema