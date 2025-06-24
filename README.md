# Azure Petstore API Agent (via OpenAPI)

This repository contains a Python-based agent built with the Google Agent Development Kit (ADK). The agent is designed to interact with the Petstore API (using its OpenAPI v3 specification) and is powered by Azure OpenAI services accessed via LiteLLM.

## Environment Variables

Ensure the following environment variables are set in a `.env` file in the `multi_tool_agent` directory (or the root, adjust `load_dotenv()` path if needed):

```plaintext
# For LiteLLM to connect to Azure OpenAI
AZURE_API_KEY="YOUR_AZURE_OPENAI_API_KEY"
AZURE_API_BASE="YOUR_AZURE_OPENAI_ENDPOINT_URL" # e.g., https://your-resource.openai.azure.com/
AZURE_API_VERSION="YOUR_AZURE_API_VERSION" # e.g., 2024-02-01

# Your specific Azure OpenAI deployment name for the model
AZURE_OPENAI_DEPLOYMENT_NAME="YOUR_AZURE_MODEL_DEPLOYMENT_NAME" # e.g., gpt-4o, my-gpt35-deployment
```

_Replace placeholder values with your actual Azure credentials and deployment name._

## Setup and Installation

1.  **Clone the Repository (if applicable):**

    ```bash
    # git clone <your-repo-url>
    # cd <your-repo-name>
    ```

2.  **Create and Activate a Virtual Environment (Recommended):**

    ```bash
    python3 -m venv .venv
    source .venv/bin/activate  # On Windows: .venv\Scripts\activate
    ```

3.  **Install Dependencies:**
    Create a `requirements.txt` file with the following content:

    ```txt
    google-adk~=1.2.0  # Or a version known to work without circular imports (e.g., 1.0.0 - 1.3.x)
    litellm
    openai
    python-dotenv
    requests
    # zoneinfo is standard in Python 3.9+
    # PyYAML might be needed by OpenAPIToolset if spec is YAML, though Petstore is JSON
    # PyYAML
    ```

    Then install:

    ```bash
    pip install -r requirements.txt
    ```

    _Note on `google-adk` version: Version `1.4.2` was observed to have a circular import issue. Versions around `1.0.0` to `1.3.x` might be more stable for this setup._

4.  **Create `.env` File:**
    Place a `.env` file inside your agent's module directory (e.g., `multi_tool_agent/.env`) or in the project root (if `load_dotenv()` is called from there) and populate it with your Azure OpenAI credentials as specified above.

## Project Structure

It's assumed your agent code resides in a structure similar to the ADK quickstart, for example:

```
parent_project_folder/
└── multi_tool_agent/
    ├── __init__.py
    ├── agent.py      # Main agent logic
    └── .env          # Environment variables
```

## Features

- **Petstore API Interaction**: Leverages an OpenAPI v3 specification (fetched from `https://petstore3.swagger.io/api/v3/openapi.json`) to dynamically create tools for interacting with the Petstore API.
- **Azure OpenAI Powered**: Uses an Azure OpenAI model (e.g., your deployment of GPT-4o, GPT-3.5-Turbo) via the LiteLLM library for its reasoning capabilities.
- **Dynamic Tool Generation**: Employs ADK's `OpenAPIToolset` to parse the Petstore spec and make its various endpoints (like finding pets, adding pets, managing orders) available as tools to the agent.

## Code Overview

### Key Components in `multi_tool_agent/agent.py`

1.  **OpenAPI Specification Fetching**:

    - The script fetches the Petstore OpenAPI v3 specification from `https://petstore3.swagger.io/api/v3/openapi.json`.
    - It programmatically modifies the fetched spec to:
      - Ensure server URLs are absolute (to prevent "No scheme supplied" errors).
      - Adjust or remove `security` definitions for certain public GET endpoints (like `/pet/findByStatus`) to simplify interaction, as the public demo API often doesn't enforce the stricter OAuth2 declared in its spec.

2.  **`OpenAPIToolset` Initialization**:

    - An `OpenAPIToolset` instance is created using the modified Petstore specification.
    - It's configured with a dummy API key using ADK's `token_to_scheme_credential` helper. This is to satisfy potential `AuthConfig` validation for operations that might still list `api_key` as a security option in the (modified) spec, even though the public Petstore GETs usually ignore the key's value.

3.  **LiteLLM Configuration**:

    - Sets up LiteLLM to use your specified Azure OpenAI deployment, reading credentials from the `.env` file.

4.  **ADK `Agent` Definition**:
    - The `root_agent` is initialized with:
      - **Name**: e.g., `petstore_openapi_agent_baseurl`
      - **Model**: The LiteLLM-configured Azure OpenAI model instance.
      - **Description**: Indicates its role as a Petstore API assistant.
      - **Instruction**: Guides the LLM on how to use the Petstore API tools (derived from `operationId`s in the spec) to fulfill user requests.
      - **Tools**: The `petstore_toolset` instance, providing access to all Petstore API operations as callable tools.

## Usage

Ensure your virtual environment is activated and you are in the `parent_project_folder`.

1.  **Run with ADK Web UI:**

    ```bash
    adk web
    ```

    Navigate to `http://localhost:8000` in your browser, select the `multi_tool_agent` (or the name of your agent module), and start interacting.

2.  **Run with ADK Command-Line Interface:**
    To send a single query:
    ```bash
    adk run multi_tool_agent "Your query about the Petstore"
    ```
    Example:
    ```bash
    adk run multi_tool_agent "Find all pets that are available"
    adk run multi_tool_agent "Show me details for pet with ID 1"
    ```
    To start an interactive CLI session:
    ```bash
    adk run multi_tool_agent
    ```

## Debugging Notes

- **Environment Variables**: The most common issue is missing or incorrect Azure OpenAI credentials in your `.env` file. The script includes checks and will raise a `ValueError` if they are not found.
- **`google-adk` Version**: Circular import errors or missing classes like `LiteLlm` or auth helpers can be due to the ADK version. Experiment with versions like `1.2.0` or `1.3.0` if issues arise with the latest.
- **OpenAPI Spec Fetching/Parsing**: Check console logs for errors during fetching or `OpenAPIToolset` creation. Network issues or changes to the Petstore spec URL could cause problems.
- **URL Scheme Error**: If you see "Invalid URL... No scheme supplied," ensure the code that makes server URLs in the spec absolute is working correctly.
- **`AuthConfig` Errors**: Errors like "validation error for AuthConfig" mean the `OpenAPIToolset` expected an authentication configuration for a tool that wasn't adequately provided or bypassed (e.g., by modifying the spec to remove the security requirement for that tool). The current code attempts to handle this by modifying the spec for public GETs and providing a dummy global API key.
- **Tool Call Failures**: If the agent tries to call a tool and it fails, check the ADK logs and the console output from the Petstore API (if any). This could be due to incorrect arguments formed by the LLM, or the Petstore API itself being temporarily unavailable or rate-limiting.

## Example Initialization Output (Console)

```plaintext
Attempting to fetch OpenAPI spec from: https://petstore3.swagger.io/api/v3/openapi.json
Successfully fetched spec from https://petstore3.swagger.io/api/v3/openapi.json. Status: 200
Original server URLs: ['/api/v3']
  Modified relative server URL '/api/v3' to absolute: 'https://petstore3.swagger.io/api/v3'
Final server URLs after modification: ['https://petstore3.swagger.io/api/v3']
Attempting to remove 'security' from spec for: GET /pet/findByStatus
  Removed 'security' for GET /pet/findByStatus
# ... (other spec modification logs) ...
Auth scheme and credential configured using token_to_scheme_credential for dummy API key.
Petstore OpenAPIToolset created.
  Attempted to configure with dummy API key auth.
LiteLLM configured for Azure deployment: azure/YOUR_AZURE_MODEL_DEPLOYMENT_NAME
ADK Agent 'petstore_openapi_agent_baseurl' initialized.

Agent 'petstore_openapi_agent_baseurl' setup complete. Ready for 'adk web' or 'adk run'.
```
