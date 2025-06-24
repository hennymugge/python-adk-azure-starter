import os
import json
import requests
from typing import Optional

from google.adk.models.lite_llm import LiteLlm
from google.adk.agents import Agent
from google.adk.tools.openapi_tool.openapi_spec_parser.openapi_toolset import OpenAPIToolset

try:
    from google.adk.tools.openapi_tool.auth.auth_helpers import token_to_scheme_credential
    HELPER_AVAILABLE = True
except ImportError:
    HELPER_AVAILABLE = False
    print("WARNING: 'token_to_scheme_credential' helper not found. Using dummy fallback.")
    def token_to_scheme_credential(auth_method_type, location, name, token_value): 
        return {"type": auth_method_type, "name": name, "in": location}, {"value": token_value}

from dotenv import load_dotenv

load_dotenv()

def fetch_openapi_spec_from_url(spec_url: str) -> Optional[str]:
    try:
        print(f"Attempting to fetch OpenAPI spec from: {spec_url}")
        response = requests.get(spec_url, timeout=15)
        response.raise_for_status()
        print(f"Successfully fetched spec from {spec_url}. Status: {response.status_code}")
        return response.text
    except requests.exceptions.Timeout:
        print(f"Error: Timeout while fetching OpenAPI spec from {spec_url}")
        return None
    except requests.exceptions.RequestException as e:
        print(f"Error fetching OpenAPI spec from {spec_url}: {e}")
        return None

PETSTORE_SPEC_URL = "https://petstore3.swagger.io/api/v3/openapi.json"

ACTUAL_PETSTORE_BASE_URL = "https://petstore3.swagger.io" 

petstore_openapi_spec_str = fetch_openapi_spec_from_url(PETSTORE_SPEC_URL)
petstore_toolset = None

dummy_api_key_value = "DUMMY_KEY_FOR_PUBLIC_PETSTORE"
auth_scheme_config = None
auth_credential_config = None

if HELPER_AVAILABLE:
    try:
        auth_scheme_config, auth_credential_config = token_to_scheme_credential(
            auth_method_type="apikey", location="header",
            name="api_key", token_value=dummy_api_key_value
        )
        print("Auth scheme and credential configured using token_to_scheme_credential for dummy API key.")
    except Exception as e_helper:
        print(f"Error using token_to_scheme_credential: {e_helper}.")
        auth_scheme_config, auth_credential_config = None, None
else: 
    auth_scheme_config, auth_credential_config = None, None


if petstore_openapi_spec_str:
    try:
        spec_dict = json.loads(petstore_openapi_spec_str)
        
        if 'servers' in spec_dict and isinstance(spec_dict['servers'], list) and spec_dict['servers']:
            print(f"Original server URLs: {[s.get('url') for s in spec_dict['servers']]}")
            
            for server_entry in spec_dict['servers']:
                if 'url' in server_entry and server_entry['url'].startswith('/'):
                    original_relative_url = server_entry['url']
                    server_entry['url'] = ACTUAL_PETSTORE_BASE_URL + original_relative_url 
                    print(f"  Modified relative server URL '{original_relative_url}' to absolute: '{server_entry['url']}'")
            print(f"Final server URLs after modification: {[s.get('url') for s in spec_dict['servers']]}")
        elif 'servers' not in spec_dict or not spec_dict['servers']:
             
            print(f"No 'servers' array in spec or it's empty. Adding default server: {ACTUAL_PETSTORE_BASE_URL}/api/v3")
            spec_dict['servers'] = [{"url": ACTUAL_PETSTORE_BASE_URL + "/api/v3"}] 

        
        endpoints_to_adjust_security = {
            "/pet/findByStatus": "get",
            "/pet/findByTags": "get",
            "/pet/{petId}": "get",
            "/store/inventory": "get"
        }
        for path, method in endpoints_to_adjust_security.items():
            try:
                operation = spec_dict.get('paths', {}).get(path, {}).get(method, {})
                if 'security' in operation:
                    original_security = operation['security']
                    
                    new_security = [s for s in original_security if "api_key" in s and "petstore_auth" not in s]
                    if not new_security and original_security : 
                        print(f"Removing 'security' entirely from spec for: {method.upper()} {path} (was {original_security})")
                        del operation['security']
                    elif new_security != original_security:
                        print(f"Modified 'security' for {method.upper()} {path}: from {original_security} to {new_security}")
                        operation['security'] = new_security
            except Exception as e_mod:
                print(f"  Error modifying spec security for {method.upper()} {path}: {e_mod}")
        
        modified_spec_str = json.dumps(spec_dict)

        petstore_toolset = OpenAPIToolset(
            spec_str=modified_spec_str,
            spec_str_type='json',
            auth_scheme=auth_scheme_config,
            auth_credential=auth_credential_config
        )
        print("Petstore OpenAPIToolset created.")
        if auth_scheme_config: print("  Attempted to configure with dummy API key auth.")

    except Exception as e:
        print(f"Error creating OpenAPIToolset from fetched spec: {e}")
        import traceback
        traceback.print_exc()
else:
    print(f"Failed to fetch OpenAPI spec from {PETSTORE_SPEC_URL}, no API tools will be available.")



azure_api_key_env = os.getenv("AZURE_API_KEY")
azure_api_base = os.getenv("AZURE_API_BASE")
azure_api_version = os.getenv("AZURE_API_VERSION")
azure_deployment_name = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME")
required_azure_vars = {
    "AZURE_API_KEY": azure_api_key_env, "AZURE_API_BASE": azure_api_base,
    "AZURE_API_VERSION": azure_api_version, "AZURE_OPENAI_DEPLOYMENT_NAME": azure_deployment_name,
}
for var_name, var_value in required_azure_vars.items():
    if not var_value:
        raise ValueError(f"{var_name} must be set for LiteLLM Azure integration.")
lite_llm_azure_model_string = f"azure/{azure_deployment_name}"
azure_model_via_litellm = LiteLlm(model=lite_llm_azure_model_string)
print(f"LiteLLM configured for Azure deployment: {lite_llm_azure_model_string}")



root_agent = Agent(
    name="petstore_openapi_agent_baseurl",
    model=azure_model_via_litellm,
    description="Agent that interacts with the Petstore API, attempting to use API key auth via helper and corrected base URL.",
    instruction=(
        "You are a Petstore assistant. Your goal is to help users interact with the Petstore API. "
        "Use the available API tools to manage pets, orders, and users. "
        "The API may require an API key for some operations, which should be handled automatically. "
        "Example tool names: 'findPetsByStatus', 'addPet', 'getPetById', 'getOrderById', 'createUser'."
    ),
    tools=[petstore_toolset] if petstore_toolset else [],
)

print(f"ADK Agent '{root_agent.name}' initialized.")
print(f"\nAgent '{root_agent.name}' setup complete. Ready for 'adk web' or 'adk run'.")