// test_agent.js
async function run() {
  const payload = {
    "request": "Weather today",
    "metadata": {
      "a2uiClientCapabilities": {
        "inlineCatalogs": [
          {
            "components": {
              "SecureIframe": {
                "type": "object",
                "properties": {
                  "payload": {
                    "type": "object"
                  }
                },
                "required": ["payload"]
              }
            }
          }
        ]
      }
    }
  };

  const response = await fetch("http://localhost:10004/", {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify(payload)
  });

  const text = await response.text();
  console.log("RESPONSE:", text);
}

run();
