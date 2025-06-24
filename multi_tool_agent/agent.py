import datetime
import os
from zoneinfo import ZoneInfo
from google.adk.models.lite_llm import LiteLlm 
from google.adk.agents import Agent

from dotenv import load_dotenv

load_dotenv()


def get_weather(city: str) -> dict:
    """Retrieves the current weather report for a specified city."""
    print(f"Tool 'get_weather' called with city: {city}")
    if city.lower() == "new york":
        return {
            "status": "success",
            "report": (
                "The weather in New York is sunny with a temperature of 25 degrees"
                " Celsius (77 degrees Fahrenheit)."
            ),
        }
    else:
        return {
            "status": "error",
            "error_message": f"Weather information for '{city}' is not available.",
        }

def get_current_time(city: str) -> dict:
    """Returns the current time in a specified city."""
    print(f"Tool 'get_current_time' called with city: {city}")
    if city.lower() == "new york":
        tz_identifier = "America/New_York"
    else:
        return {
            "status": "error",
            "error_message": (
                f"Sorry, I don't have timezone information for {city}."
            ),
        }

    try:
        tz = ZoneInfo(tz_identifier)
        now = datetime.datetime.now(tz)
        report = (
            f'The current time in {city} is {now.strftime("%Y-%m-%d %H:%M:%S %Z%z")}'
        )
        return {"status": "success", "report": report}
    except Exception as e:
        return {
            "status": "error",
            "error_message": f"Error getting time for {city}: {str(e)}"
        }

azure_deployment_name = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME")

if not azure_deployment_name:
    raise ValueError(
        "AZURE_OPENAI_DEPLOYMENT_NAME environment variable must be set in the .env file."
    )
if not os.getenv("AZURE_API_KEY") or not os.getenv("AZURE_API_BASE") or not os.getenv("AZURE_API_VERSION"):
    raise ValueError(
        "AZURE_API_KEY, AZURE_API_BASE, and AZURE_API_VERSION must be set for LiteLLM Azure integration."
    )


lite_llm_azure_model_string = f"azure/{azure_deployment_name}"
azure_via_litellm = LiteLlm(model=lite_llm_azure_model_string)


root_agent = Agent(
    name="azure_weather_time_agent_litellm",
    model=azure_via_litellm, 
    description=(
        "Agent to answer questions about the time and weather in a city, powered by Azure OpenAI via LiteLLM."
    ),
    instruction=(
        "You are a helpful agent who can answer user questions about the time and weather in a city. "
        "If asked about both weather and time for the same city, call both tools."
    ),
    tools=[get_weather, get_current_time],
)

print(f"ADK Agent '{root_agent.name}' initialized using LiteLLM for Azure deployment '{azure_deployment_name}'.")
print("Model string for LiteLLM:", lite_llm_azure_model_string)
print("Ready to be used with 'adk web' or 'adk run'.")