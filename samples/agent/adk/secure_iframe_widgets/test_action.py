import asyncio
from agent import SecureWidgetAgent

async def main():
    agent = SecureWidgetAgent(base_url="http://localhost:8000", use_ui=True)
    query = "User submitted an event: ACTION: show_news with data: {'symbol': 'NVDA', 'headline': 'Analysts Raise Price Targets on NVIDIA Ahead of GTC Conference'}"
    client_caps = {
        "inlineCatalogs": [{
            "id": "contact_widgets",
            "components": {
                "SecureIframe": {
                    "type": "object",
                    "properties": {
                        "widgetType": {"type": "string"},
                        "widgetData": {"type": "object"},
                        "htmlContent": {"type": "string"}
                    }
                }
            }
        }]
    }
    
    try:
        async for resp in agent.stream(
            query=query,
            session_id="session123",
            client_ui_capabilities=client_caps
        ):
            print("AGENT RESPONSE:", resp)
    except Exception as e:
        print("AGENT EXCEPTION:", e)

asyncio.run(main())
