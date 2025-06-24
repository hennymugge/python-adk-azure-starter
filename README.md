````markdown
# Azure Weather and Time Agent

This repository contains a Python-based agent designed to provide weather and time information for cities using Azure OpenAI services via LiteLLM.

## Environment Variables

Ensure the following environment variables are set in your `.env` file:

```plaintext
AZURE_API_KEY=
AZURE_API_BASE=
AZURE_API_VERSION=
AZURE_API_DEPLOYMENT_NAME=
```
````

## Installation

1. Clone the repository.
2. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

3. Create a `.env` file in the root directory and populate it with the required environment variables.

## Features

- **Weather Information**: Retrieves the current weather for a specified city.
- **Time Information**: Provides the current time for a specified city using timezone data.

## Code Overview

### Tools

#### `get_weather(city: str) -> dict`

Retrieves weather information for a city. Currently supports **New York**.

#### `get_current_time(city: str) -> dict`

Gets the current time for a city. Currently supports **New York**.

### Agent

The `Agent` is powered by Azure OpenAI via LiteLLM and is configured to:

- Answer user queries about weather and time.
- Execute both tools when asked about weather and time for the same city.

### Initialization

The agent is initialized with:

- **Model**: `azure/gpt-4.1-nano` via LiteLLM.
- **Description**: Provides weather and time information for cities.
- **Tools**: `get_weather`, `get_current_time`.

## Usage

Run the agent using ADK commands:

- **Web Interface**:

  ```bash
  adk web
  ```

- **Command-line Interface**:

  ```bash
  adk run
  ```

## Debugging

Ensure all required environment variables are set. Missing variables will raise a `ValueError`.

## Example Output

```plaintext
ADK Agent 'azure_weather_time_agent_litellm' initialized using LiteLLM for Azure deployment 'gpt-4.1-nano'.
Model string for LiteLLM: azure/gpt-4.1-nano
Ready to be used with 'adk web' or 'adk run'.
```

## Dependencies

- **Python**: 3.9+
- **LiteLLM**: For Azure OpenAI integration.
- **ADK**: For agent deployment.

```

```
