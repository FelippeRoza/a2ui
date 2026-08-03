# Copyright 2025 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import json
import jsonschema
import logging
import os
from collections.abc import AsyncIterable
from typing import Any

from a2a.types import (
    AgentCapabilities,
    AgentCard,
    AgentSkill,
    DataPart,
    Part,
    TextPart,
)
from google.adk.agents.llm_agent import LlmAgent
from google.adk.artifacts import InMemoryArtifactService
from google.adk.memory.in_memory_memory_service import InMemoryMemoryService
from google.adk.models import Gemini
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types
from prompt_builder import (
    get_text_prompt,
    ROLE_DESCRIPTION,
    WORKFLOW_DESCRIPTION,
    UI_DESCRIPTION,
)
# Tools removed to enable generic open-ended reasoning
from a2ui.core.schema.constants import VERSION_0_8, A2UI_OPEN_TAG, A2UI_CLOSE_TAG
from a2ui.core.schema.manager import A2uiSchemaManager
from a2ui.core.parser.parser import parse_response, ResponsePart
from a2ui.basic_catalog.provider import BasicCatalog
from a2ui.core.schema.common_modifiers import remove_strict_validation
from a2ui.a2a import create_a2ui_part, get_a2ui_agent_extension, parse_response_to_parts

from canned_widgets import CANNED_WIDGETS

logger = logging.getLogger(__name__)


class SecureWidgetAgent:
  """An agent that generates A2UI widgets for weather and restaurants."""

  SUPPORTED_CONTENT_TYPES = ["text", "text/plain"]

  def __init__(self, base_url: str, use_ui: bool = False):
    self.base_url = base_url
    self.use_ui = use_ui
    self.schema_manager = (
        A2uiSchemaManager(
            VERSION_0_8,
            catalogs=[
                BasicCatalog.get_config(version=VERSION_0_8, examples_path="examples")
            ],
            schema_modifiers=[remove_strict_validation],
            accepts_inline_catalogs=True,
        )
        if use_ui
        else None
    )
    self._agent = self._build_agent(use_ui)
    self.widget_cache = {**CANNED_WIDGETS}
    self._user_id = "remote_agent"
    self._runner = Runner(
        app_name=self._agent.name,
        agent=self._agent,
        artifact_service=InMemoryArtifactService(),
        session_service=InMemorySessionService(),
        memory_service=InMemoryMemoryService(),
    )

  def get_agent_card(self) -> AgentCard:
    capabilities = AgentCapabilities(
        streaming=True,
        extensions=[
            get_a2ui_agent_extension(
                self.schema_manager.accepts_inline_catalogs,
                self.schema_manager.supported_catalog_ids,
            )
        ],
    )
    skill = AgentSkill(
        id="find_contact",
        name="Find Contact Tool",
        description=(
            "Helps find contact information for colleagues (e.g., email, location,"
            " team)."
        ),
        tags=["contact", "directory", "people", "finder"],
        examples=[
            "Who is David Chen in marketing?",
            "Find Sarah Lee from engineering",
        ],
    )

    return AgentCard(
        name="Contact Lookup Agent",
        description=(
            "This agent helps find contact info for people in your organization."
        ),
        url=self.base_url,
        version="1.0.0",
        default_input_modes=SecureWidgetAgent.SUPPORTED_CONTENT_TYPES,
        default_output_modes=SecureWidgetAgent.SUPPORTED_CONTENT_TYPES,
        capabilities=capabilities,
        skills=[skill],
    )

  def get_processing_message(self) -> str:
    return "Looking up contact information..."

  def _build_agent(self, use_ui: bool) -> LlmAgent:
    """Builds the LLM agent for the contact agent."""
    LITELLM_MODEL = os.getenv("LITELLM_MODEL", "gemini-2.5-flash").replace("gemini/", "")

    instruction = (
        self.schema_manager.generate_system_prompt(
            role_description=ROLE_DESCRIPTION,
            workflow_description=WORKFLOW_DESCRIPTION,
            ui_description=UI_DESCRIPTION,
            include_examples=True,
            include_schema=True,
            validate_examples=False,  # Missing inline_catalogs for OrgChart and WebFrame validation
        )
        if use_ui
        else get_text_prompt()
    )

    return LlmAgent(
        model=Gemini(model=LITELLM_MODEL),
        name="secure_widget_agent",
        description="An agent that builds UI widgets.",
        instruction=instruction,
        tools=[],
    )

  async def _handle_action(self, query: str) -> dict[str, Any] | None:
    return None

  async def stream(
      self, query, session_id, client_ui_capabilities: dict[str, Any] | None = None
  ) -> AsyncIterable[dict[str, Any]]:
    session_state = {"base_url": self.base_url}

    session = await self._runner.session_service.get_session(
        app_name=self._agent.name,
        user_id=self._user_id,
        session_id=session_id,
    )
    if session is None:
      session = await self._runner.session_service.create_session(
          app_name=self._agent.name,
          user_id=self._user_id,
          state=session_state,
          session_id=session_id,
      )
    elif "base_url" not in session.state:
      session.state["base_url"] = self.base_url

    # --- Begin: UI Validation and Retry Logic ---
    max_retries = 1  # Total 2 attempts
    attempt = 0
    current_query_text = query

    # Ensure schema was loaded
    selected_catalog = self.schema_manager.get_selected_catalog(client_ui_capabilities)
    if self.use_ui and not selected_catalog.catalog_schema:
      logger.error(
          "--- ContactAgent.stream: A2UI_SCHEMA is not loaded. "
          "Cannot perform UI validation. ---"
      )
      yield {
          "is_task_complete": True,
          "content": (
              "I'm sorry, I'm facing an internal configuration error with my UI"
              " components. Please contact support."
          ),
      }
      return

    while attempt <= max_retries:
      attempt += 1
      logger.info(
          f"--- ContactAgent.stream: Attempt {attempt}/{max_retries + 1} "
          f"for session {session_id} ---"
      )
      logger.info(f"--- ContactAgent.stream: Received query: '{query}' ---")

      # --- Check for User Action ---
      action_response = await self._handle_action(query)
      if action_response:
        yield action_response
        return

      # --- Fast-Path Demo Queries for Zero Latency ---
      # The query might contain a system suffix injected by agent_executor.py
      # We extract just the actual user query for accurate pattern matching.
      user_query = query.split("\n\n[SYSTEM:")[0]
      query_lower = user_query.lower().strip()
      
      # We must ensure we don't accidentally intercept internal ACTION translation payloads
      is_mtv_weather = query_lower in [
          "weather in mountain view", "mountain view weather", "weather mountain view", "what is the weather in mountain view", "weather in mtv"
      ]
      is_goog_stock = query_lower == "goog" or query_lower == "goog stock" or query_lower == "stock price for goog"
      is_restaurant = "restaurant" in query_lower or "places to eat" in query_lower
      is_weather_details = query_lower.startswith("show me an interactive detailed weather forecast widget for")

      if is_mtv_weather:
        logger.info("--- Fast-path triggered for Mountain View weather ---")
        yield {
            "is_task_complete": True,
            "parts": [
                Part(root=TextPart(text="Here is the current weather for Mountain View, CA:")),
                create_a2ui_part({
                    "beginRendering": {"surfaceId": "weather_mtv_fast", "root": "root_frame"}
                }),
                create_a2ui_part({
                    "surfaceUpdate": {
                        "surfaceId": "weather_mtv_fast",
                        "components": [{
                            "id": "root_frame",
                            "component": {"SecureIframe": {
                                "widgetType": "weather",
                                "widgetData": {
                                    "location": "Mountain View, CA",
                                    "temperature": "73°",
                                    "condition": "Sunny",
                                    "icon": "sun",
                                    "humidity": "42%",
                                    "wind": "4 mph",
                                    "forecast": [
                                        {"day": "Mon", "high": "73°", "icon": "sun"},
                                        {"day": "Tue", "high": "75°", "icon": "sun"},
                                        {"day": "Wed", "high": "74°", "icon": "cloud"},
                                        {"day": "Thu", "high": "68°", "icon": "rain"}
                                    ]
                                },
                                "htmlContent": self.widget_cache.get("weather", {}).get("htmlContent")
                            }}
                        }]
                    }
                })
            ]
        }
        return

      if is_weather_details:
        logger.info("--- Fast-path triggered for Weather Details Action ---")
        yield {
            "is_task_complete": True,
            "parts": [
                Part(root=TextPart(text="I received your click! Here is the detailed forecast you requested:\n" + user_query)),
            ]
        }
        return

      if is_restaurant:
        logger.info("--- Fast-path triggered for Local Restaurants ---")
        yield {
            "is_task_complete": True,
            "parts": [
                Part(root=TextPart(text="Here are some great places to eat nearby. You can search or filter by category directly in the widget!")),
                create_a2ui_part({
                    "beginRendering": {"surfaceId": "restaurants_fast_1", "root": "root_frame"}
                }),
                create_a2ui_part({
                    "surfaceUpdate": {
                        "surfaceId": "restaurants_fast_1",
                        "components": [{
                            "id": "root_frame",
                            "component": {"SecureIframe": {
                                "widgetType": "restaurants",
                                "widgetData": {
                                    "location": "Mountain View, CA",
                                    "restaurants": [
                                        {"id": "r1", "name": "Castro St Sushi", "cuisine": "Sushi", "category": "Casual", "rating": 4.8, "priceRange": "$$", "imageUrl": "http://localhost:10004/static/news.jpg"},
                                        {"id": "r2", "name": "La Trattoria", "cuisine": "Italian", "category": "Fine Dining", "rating": 4.6, "priceRange": "$$$", "imageUrl": "http://localhost:10004/static/weather.jpg"},
                                        {"id": "r3", "name": "Burger Joint", "cuisine": "American", "category": "Fast Food", "rating": 4.2, "priceRange": "$", "imageUrl": "http://localhost:10004/static/news.jpg"},
                                        {"id": "r4", "name": "Spicy Thai Fast", "cuisine": "Thai", "category": "Casual", "rating": 4.5, "priceRange": "$$", "imageUrl": "http://localhost:10004/static/weather.jpg"},
                                        {"id": "r5", "name": "Steakhouse Prime", "cuisine": "Steakhouse", "category": "Fine Dining", "rating": 4.9, "priceRange": "$$$$", "imageUrl": "http://localhost:10004/static/news.jpg"}
                                    ]
                                },
                                "htmlContent": self.widget_cache.get("restaurants", {}).get("htmlContent")
                            }}
                        }]
                    }
                })
            ]
        }
        return

      if is_goog_stock:
        logger.info("--- Fast-path triggered for GOOG stock ---")
        yield {
            "is_task_complete": True,
            "parts": [
                Part(root=TextPart(text="Here is the latest stock data for Alphabet Inc:")),
                create_a2ui_part({
                    "beginRendering": {"surfaceId": "stock_goog_fast", "root": "root_frame"}
                }),
                create_a2ui_part({
                    "surfaceUpdate": {
                        "surfaceId": "stock_goog_fast",
                        "components": [{
                            "id": "root_frame",
                            "component": {"SecureIframe": {
                                "widgetType": "stocks",
                                "widgetData": {
                                    "symbol": "GOOGL",
                                    "company": "Alphabet Inc.",
                                    "price": "178.52",
                                    "change": "1.28",
                                    "changePercent": "0.72%",
                                    "high": "180.00",
                                    "low": "175.00",
                                    "volume": "24.5M",
                                    "marketCap": "2.2T",
                                    "news": [
                                        "Google I/O Announces New AI Capabilities",
                                        "Alphabet surpasses earnings estimates for Q1"
                                    ]
                                },
                                "htmlContent": self.widget_cache.get("stocks", {}).get("htmlContent")
                            }}
                        }]
                    }
                })
            ]
        }
        return

      # Inject cache info into the prompt for Phase 2 optimizations
      query_with_cache = current_query_text
      if self.widget_cache:
        cached_details = []
        for k, v in self.widget_cache.items():
            schema_str = json.dumps(v.get("schema", {}))
            cached_details.append(f"- WidgetType: '{k}'\n  Schema: {schema_str}")
        
        cache_info = f"\n\n[System Note: Cached Widgets available. If using one, your widgetData MUST match its schema exactly:\n" + "\n".join(cached_details) + "]"
        query_with_cache += cache_info

      current_message = types.Content(
          role="user", parts=[types.Part.from_text(text=query_with_cache)]
      )
      final_response_content = None

      async for event in self._runner.run_async(
          user_id=self._user_id,
          session_id=session.id,
          new_message=current_message,
      ):
        logger.info(f"Event from runner: {event}")
        if event.is_final_response():
          if event.content and event.content.parts and event.content.parts[0].text:
            final_response_content = "\n".join(
                [p.text for p in event.content.parts if p.text]
            )
          break  # Got the final response, stop consuming events
        else:
          logger.info(f"Intermediate event: {event}")
          # Yield intermediate updates on every attempt
          yield {
              "is_task_complete": False,
              "updates": self.get_processing_message(),
          }

      if final_response_content is None:
        logger.warning(
            "--- ContactAgent.stream: Received no final response content from runner "
            f"(Attempt {attempt}). ---"
        )
        if attempt <= max_retries:
          current_query_text = (
              "I received no response. Please try again."
              f"Please retry the original request: '{query}'"
          )
          continue  # Go to next retry
        else:
          # Retries exhausted on no-response
          final_response_content = (
              "I'm sorry, I encountered an error and couldn't process your request."
          )
          # Fall through to send this as a text-only error

      is_valid = False
      error_message = ""

      if self.use_ui:
        logger.info(
            "--- ContactAgent.stream: Validating UI response (Attempt"
            f" {attempt})... ---"
        )
        try:
          if A2UI_OPEN_TAG not in final_response_content:
            logger.info("--- ContactAgent.stream: No A2UI tags found. Treating as text-only response. ---")
            is_valid = True
          else:
            response_parts = parse_response(final_response_content)

            for part in response_parts:
              if not part.a2ui_json:
                continue

              parsed_json_data = part.a2ui_json

              # Handle the "no results found" or empty JSON case
              if parsed_json_data == []:
                logger.info(
                    "--- ContactAgent.stream: Empty JSON list found. "
                    "Assuming valid (e.g., 'no results'). ---"
                )
                is_valid = True
              else:
                logger.info(
                    "--- ContactAgent.stream: Validating against A2UI_SCHEMA... ---"
                )
                selected_catalog.validator.validate(parsed_json_data)

                logger.info(
                    "--- ContactAgent.stream: UI JSON successfully parsed AND validated"
                    f" against schema. Validation OK (Attempt {attempt}). ---"
                )
                is_valid = True

        except (
            ValueError,
            json.JSONDecodeError,
            jsonschema.exceptions.ValidationError,
        ) as e:
          logger.warning(
              f"--- ContactAgent.stream: A2UI validation failed: {e} (Attempt"
              f" {attempt}) ---"
          )
          logger.warning(
              f"--- Failed response content: {final_response_content[:500]}... ---"
          )
          error_message = f"Validation failed: {e}."

      else:  # Not using UI, so text is always "valid"
        is_valid = True

      if is_valid:
        logger.info(
            "--- ContactAgent.stream: Response is valid. Sending final response"
            f" (Attempt {attempt}). ---"
        )

        if A2UI_OPEN_TAG not in final_response_content:
            final_parts = [Part(root=TextPart(text=final_response_content))]
        else:
            # Cache SecureIframe layouts and inject data into placeholders
            if self.use_ui:
                response_parts = parse_response(final_response_content)
                for part in response_parts:
                    if not part.a2ui_json:
                        continue
                    for msg in part.a2ui_json:
                        if "surfaceUpdate" in msg and "components" in msg["surfaceUpdate"]:
                            for comp in msg["surfaceUpdate"]["components"]:
                                if "SecureIframe" in comp.get("component", {}):
                                    iframe = comp["component"]["SecureIframe"]
                                    w_type = iframe.get("widgetType")
                                    w_data = iframe.get("widgetData", {})
                                    
                                    # If it's a new template, cache it
                                    if "htmlContent" in iframe and w_type:
                                        # Infer a basic schema to pass back in future turns
                                        inferred_schema = {key: str(type(val).__name__) for key, val in w_data.items()}
                                        self.widget_cache[w_type] = {
                                            "htmlContent": iframe["htmlContent"],
                                            "schema": inferred_schema
                                        }
                                        logger.info(f"--- Cached new A2UI layout for '{w_type}' with schema ---")
                                    
                                    # If it's a cached template being reused
                                    elif "htmlContent" not in iframe and w_type in self.widget_cache:
                                        iframe["htmlContent"] = self.widget_cache[w_type].get("htmlContent")
                                        logger.info(f"--- Reusing cached A2UI layout for '{w_type}' ---")

            # Generate final Part objects directly to avoid string re-serialization issues
            final_parts = []
            for part in response_parts:
                if part.text:
                    final_parts.append(Part(root=TextPart(text=part.text)))
                if part.a2ui_json is not None:
                    if isinstance(part.a2ui_json, list):
                        for message in part.a2ui_json:
                            final_parts.append(create_a2ui_part(message))
                    else:
                        final_parts.append(create_a2ui_part(part.a2ui_json))
            
            with open("dump.txt", "w") as f:
                f.write(json.dumps([p.root.model_dump() for p in final_parts], indent=2))

        yield {
            "is_task_complete": True,
            "parts": final_parts,
        }
        return  # We're done, exit the generator

      # --- If we're here, it means validation failed ---

      if attempt <= max_retries:
        logger.warning(
            f"--- ContactAgent.stream: Retrying... ({attempt}/{max_retries + 1}) ---"
        )
        # Prepare the query for the retry
        current_query_text = (
            f"Your previous response was invalid. {error_message} You MUST generate a"
            " valid response that strictly follows the A2UI JSON SCHEMA. The response"
            " MUST be a JSON list of A2UI messages. Ensure each JSON part is wrapped in"
            f" '{A2UI_OPEN_TAG}' and '{A2UI_CLOSE_TAG}' tags. Please retry the"
            f" original request: '{query}'"
        )
        # Loop continues...

    # --- If we're here, it means we've exhausted retries ---
    logger.error(
        "--- ContactAgent.stream: Max retries exhausted. Sending text-only error. ---"
    )
    yield {
        "is_task_complete": True,
        "parts": [
            Part(
                root=TextPart(
                    text=(
                        "I'm sorry, I'm having trouble generating the interface for"
                        " that request right now. Please try again in a moment."
                    )
                )
            )
        ],
    }
    # --- End: UI Validation and Retry Logic ---
