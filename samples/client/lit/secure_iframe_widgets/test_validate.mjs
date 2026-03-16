import { v0_8 } from "@a2ui/lit";
import { componentRegistry } from "@a2ui/lit/ui";

componentRegistry.register("SecureIframe", class {}, "a2ui-secure-iframe", {
  type: "object",
  properties: {
    htmlContent: { type: "string" },
    url: { type: "string" }
  },
  required: ["htmlContent"]
});

const processor = v0_8.Data.createSignalA2uiMessageProcessor();

const payload = [
  {
    "beginRendering": {
      "surfaceId": "weather_widget_123",
      "root": "weather_iframe"
    }
  },
  {
    "surfaceUpdate": {
      "surfaceId": "weather_widget_123",
      "components": [
        {
          "id": "weather_iframe",
          "component": {
            "SecureIframe": {
              "url": "http://localhost:10004/widgets/weather_widget",
              "payload": {
                "dataModelUpdate": {
                  "surfaceId": "weather_widget_123",
                  "contents": [
                    {
                      "key": "/weather/location",
                      "valueString": "Sunnyvale"
                    }
                  ]
                }
              }
            }
          }
        }
      ]
    }
  }
];

try {
  processor.processMessages(payload);
  console.log("Surfaces map size:", processor.getSurfaces().size);
} catch (e) {
  console.error("VALIDATION ERROR:", e);
}
