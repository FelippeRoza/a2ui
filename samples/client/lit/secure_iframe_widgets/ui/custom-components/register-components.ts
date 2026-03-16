import { componentRegistry } from "@a2ui/lit/ui";
import { SecureIframe } from "./secure-iframe.js";

export function registerContactComponents() {
  componentRegistry.register("SecureIframe", SecureIframe, "a2ui-secure-iframe", {
    type: "object",
    properties: {
      htmlContent: {
        type: "string"
      },
      url: {
        type: "string"
      },
      widgetType: {
        type: "string",
        description: "A unique key representing this widget's UI layout (e.g. 'stock_ticker', 'weather_widget')."
      },
      widgetData: {
        type: "object",
        description: "The JSON data to inject into the widget's template."
      }
    }
  });

  console.log("Registered SecureIframe App Custom Components");
}
