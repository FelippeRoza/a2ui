/*
 * Copyright 2025 Google LLC
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *      https://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

import { SignalWatcher } from "@lit-labs/signals";
import { provide } from "@lit/context";
import {
  LitElement,
  html,
  css,
  nothing,
  HTMLTemplateResult,
  unsafeCSS,
} from "lit";
import { customElement, state } from "lit/decorators.js";
import { theme as uiTheme } from "./theme/theme.js";
import { A2UIClient, A2DataPayload, A2TextPayload } from "./client.js";
import {
  SnackbarAction,
  SnackbarMessage,
  SnackbarUUID,
  SnackType,
} from "./types/types.js";
import { type Snackbar } from "./ui/snackbar.js";
import { repeat } from "lit/directives/repeat.js";
import { v0_8 } from "@a2ui/lit";
import * as UI from "@a2ui/lit/ui";

// Demo elements.
import "./ui/ui.js";
import { registerContactComponents } from "./ui/custom-components/register-components.js";
import { Context } from "@a2ui/lit/ui";
// @ts-ignore
import { renderMarkdown } from "@a2ui/markdown-it";

// Register custom components for the contact app
registerContactComponents();

const BASE_METADATA = {
  a2uiClientCapabilities: {
    inlineCatalogs: [
      {
        id: "contact_widgets",
        components: {
          SecureIframe: {
            description: "Renders an isolated React component or arbitrary HTML inside a sandboxed iframe. Crucially, the widgetData is reactively forwarded to the iframe.",
            type: "object",
            properties: {
              widgetType: {
                type: "string",
                description: "A unique key representing this widget's UI layout."
              },
              widgetData: {
                type: "object",
                description: "The JSON data to inject into the widget's template."
              },
              htmlContent: {
                type: "string",
                description: "A complete HTML document containing external script tags (e.g. React/Babel) and the UI logic. Omit this field entirely if you are reusing a widgetType you have already defined in this session."
              }
            }
          }
        }
      }
    ]
  }
};

@customElement("secure-iframe-app")
export class SecureIframeApp extends SignalWatcher(LitElement) {
  connectedCallback() {
    super.connectedCallback();
  }

  protected updated(changedProperties: Map<string | number | symbol, unknown>) {
    super.updated(changedProperties);
    
    // Auto-scroll to bottom of chat history when properties change 
    // (e.g., new messages, requesting state changes, etc.)
    const surfacesContainer = this.shadowRoot?.querySelector('#surfaces');
    if (surfacesContainer) {
      surfacesContainer.scrollTop = surfacesContainer.scrollHeight;
    }
  }

  @provide({ context: UI.Context.themeContext })
  accessor theme: v0_8.Types.Theme = uiTheme;

  @provide({ context: UI.Context.markdown })
  accessor markdownRenderer: v0_8.Types.MarkdownRenderer = async (text, options) => {
    return renderMarkdown(text, options);
  };

  @state()
  accessor #requesting = false;

  @state()
  accessor #error: string | null = null;

  @state()
  accessor renderVersion = 0;

  #chatHistory: Array<{ role: 'user' | 'agent' | 'action', text?: string, surfaceId?: string, duration?: string }> = [];

  static styles = [
    unsafeCSS(v0_8.Styles.structuralStyles),
    css`
      :host {
        display: flex;
        flex-direction: column;
        max-width: 640px;
        margin: 0 auto;
        height: 100vh;
      }

      #surfaces {
        display: flex;
        flex-direction: row;
        gap: 16px;
        width: 100%;
        padding: var(--bb-grid-size-3) 0;
        animation: fadeIn 1s cubic-bezier(0, 0, 0.3, 1) 0.3s backwards;
        align-items: flex-start;

        & a2ui-surface {
          width: 100%;
          flex: 1;
        }
      }

      form {
        display: flex;
        flex-direction: column;
        flex-shrink: 0;
        gap: 16px;
        align-items: center;
        padding: 16px 0 32px 0;
        animation: fadeIn 1s cubic-bezier(0, 0, 0.3, 1) 1s backwards;
        background: var(--background);
        position: sticky;
        bottom: 0;
        z-index: 10;

        & > div {
          display: flex;
          flex: 1;
          gap: 16px;
          align-items: center;
          width: 100%;

          & > input {
            display: block;
            flex: 1;
            border-radius: 32px;
            padding: 16px 24px;
            border: 1px solid var(--p-60);
            font-size: 16px;
          }

          & > button {
            display: flex;
            align-items: center;
            background: var(--p-40);
            color: var(--n-100);
            border: none;
            padding: 8px 16px;
            border-radius: 32px;
            opacity: 0.5;

            &:not([disabled]) {
              cursor: pointer;
              opacity: 1;
            }
          }
        }
      }

      .rotate {
        animation: spin 1s linear infinite;
      }

      .pending {
        width: 100%;
        min-height: 200px;
        display: flex;
        align-items: center;
        justify-content: center;
        animation: fadeIn 1s cubic-bezier(0, 0, 0.3, 1) 0.3s backwards;

        & .g-icon {
          margin-right: 8px;
        }
      }

      .error {
        color: var(--e-40);
        background-color: var(--e-95);
        border: 1px solid var(--e-80);
        padding: 16px;
        border-radius: 8px;
      }

      @keyframes fadeIn {
        from {
          opacity: 0;
        }

        to {
          opacity: 1;
        }
      }

      .spinner {
        width: 48px;
        height: 48px;
        border: 4px solid rgba(255, 255, 255, 0.1);
        border-left-color: var(--p-60);
        border-radius: 50%;
        animation: spin 1s linear infinite;
      }

      @keyframes spin {
        to {
          transform: rotate(360deg);
        }
      }

      @keyframes pulse {
        0% {
          opacity: 0.6;
        }
        50% {
          opacity: 1;
        }
        100% {
          opacity: 0.6;
        }
      }
    `,
  ];

  #processor = v0_8.Data.createSignalA2uiMessageProcessor();
  #a2uiClient = new A2UIClient();
  #snackbar: Snackbar | undefined = undefined;
  #pendingSnackbarMessages: Array<{
    message: SnackbarMessage;
    replaceAll: boolean;
  }> = [];

  render() {
    return [
      this.#maybeRenderData(),
      this.#maybeRenderError(),
      this.#maybeRenderForm(),
    ];
  }

  #maybeRenderError() {
    if (!this.#error) return nothing;

    return html`<div class="error">${this.#error}</div>`;
  }

  #maybeRenderForm() {
    if (this.#requesting) return nothing;
    return html`<form
      @submit=${async (evt: Event) => {
        evt.preventDefault();
        if (!(evt.target instanceof HTMLFormElement)) {
          return;
        }
        const data = new FormData(evt.target);
        const body = data.get("body") ?? null;
        const message: v0_8.Types.A2UIClientEventMessage = {
          request: body,
          metadata: BASE_METADATA
        } as any;
        await this.#sendAndProcessMessage(message);
      }}
    >
      <div style="width: 100%; display: flex; gap: 16px;">
        <input
          required
          placeholder="Ask me about the weather or restaurants..."
          autocomplete="off"
          id="body"
          name="body"
          type="text"
          ?disabled=${this.#requesting}
        />
        <button type="submit" ?disabled=${this.#requesting}>
          <span class="g-icon filled-heavy">send</span>
        </button>
      </div>
    </form>`;
  }

  #maybeRenderData() {
    return html`<section id="surfaces" style="flex-direction: column; overflow-y: auto; flex: 1; margin-bottom: 24px;">
      ${this.#chatHistory.map((msg) => {
      if (msg.role === 'user') {
        return html`
            <div style="align-self: flex-end; background: var(--p-90); padding: 12px 16px; border-radius: 16px; border-bottom-right-radius: 4px; max-width: 80%; margin-bottom: 12px;">
              ${msg.text}
            </div>
          `;
      }
      
      if (msg.role === 'action') {
        return html`
            <div style="font-size: 13px; color: var(--n-50); align-self: flex-end; margin-bottom: 12px; padding-right: 8px;">
              ${msg.text}
            </div>
          `;
      }

      if (msg.text) {
        return html`
            <div style="align-self: flex-start; display: flex; flex-direction: column; max-width: 80%; margin-bottom: 12px;">
              <div style="background: var(--n-100); border: 1px solid var(--n-90); padding: 12px 16px; border-radius: 16px; border-bottom-left-radius: 4px;">
                ${msg.text}
              </div>
              ${msg.duration ? html`<div style="font-size: 12px; color: var(--n-60); align-self: flex-start; margin-top: 4px; padding-left: 8px;">⏱️ ${msg.duration}</div>` : nothing}
            </div>
          `;
      }

      if (msg.surfaceId) {
        const surfaceId = msg.surfaceId;
        const surface = this.#processor.getSurfaces().get(surfaceId);
        if (!surface) {
          console.error(`[A2UI Error] Surface ${surfaceId} not found in processor!`);
          return html`<div class="error" style="margin-bottom: 12px;">Agent generated an empty or missing surface (${surfaceId}). Is the component registry missing a definition?</div>`;
        }

        return html`
            <div style="position: relative; align-self: flex-start; max-width: 80%; width: 100%; display: flex; flex-direction: column; align-items: stretch; margin-bottom: 16px;">
              <a2ui-surface
                  .surfaceId=${surfaceId}
                  .surface=${surface}
                  @a2uiaction=${async (
          evt: v0_8.Events.StateEvent<"a2ui.action">
        ) => {
            const [target] = evt.composedPath();
            if (!(target instanceof HTMLElement)) {
              return;
            }

            const context: v0_8.Types.A2UIClientEventMessage["userAction"]["context"] =
              {};
            if (evt.detail.action.context) {
              const srcContext = evt.detail.action.context;
              for (const item of srcContext) {
                if (item.value.literalBoolean) {
                  context[item.key] = item.value.literalBoolean;
                } else if (item.value.literalNumber) {
                  context[item.key] = item.value.literalNumber;
                } else if (item.value.literalString) {
                  context[item.key] = item.value.literalString;
                } else if (item.value.path) {
                  const path = this.#processor.resolvePath(
                    item.value.path,
                    evt.detail.dataContextPath
                  );
                  const value = this.#processor.getData(
                    evt.detail.sourceComponent,
                    path,
                    surfaceId
                  );
                  context[item.key] = value;
                }
              }
            }

            const message: v0_8.Types.A2UIClientEventMessage = {
              userAction: {
                surfaceId: surfaceId,
                name: "ACTION: " + evt.detail.action.name,
                sourceComponentId: target.id,
                timestamp: new Date().toISOString(),
                context,
              },
              metadata: BASE_METADATA
            } as any;



            await this.#sendAndProcessMessage(message);
          }}
                .processor=${this.#processor}
                .enableCustomElements=${true}
              ></a2ui-surface>
              ${msg.duration ? html`<div style="font-size: 12px; color: var(--n-60); margin-top: 8px;">⏱️ ${msg.duration}</div>` : nothing}
            </div>
          `;
      }
      return nothing;
    })}
      
      ${this.#requesting ? html`
        <div style="align-self: flex-start; padding: 12px; margin-top: 8px;">
           <span class="g-icon filled-heavy rotate" style="font-size: 24px; color: var(--p-40);">progress_activity</span>
        </div>
      ` : nothing}
    </section>`;
  }

  async #sendAndProcessMessage(request: v0_8.Types.A2UIClientEventMessage) {
    if (request.request) {
      this.#chatHistory = [...this.#chatHistory, { role: 'user', text: request.request as string }];
    } else if (request.userAction) {
      this.#chatHistory = [...this.#chatHistory, { role: 'action', text: `[Action: ${request.userAction.name.replace('ACTION: ', '')}]` }];
    }
    this.#requesting = true;
    const startTime = performance.now();
    const payloads = await this.#sendMessage(request);
    const endTime = performance.now();
    const durationMs = (endTime - startTime).toFixed(0);

    // Filter A2UI payloads and pass them to the processor
    const a2uiMessages = payloads
      .filter((p) => p.kind === "data")
      .flatMap((p) => Array.isArray(p.data) ? p.data : [p.data]);
    
    console.log("Calling processMessages with:", a2uiMessages);
    
    try {
      this.#processor.processMessages(a2uiMessages);
      console.log("processMessages completed successfully.");
    } catch (e) {
      console.error("processMessages THREW AN ERROR:", e);
    }

    // Process text messages and widget chat bubbles
    for (const p of payloads) {
      if (p.kind === "text") {
        this.#chatHistory = [...this.#chatHistory, { role: 'agent', text: p.text as string, duration: `${durationMs}ms` }];
      } else if (p.kind === "data") {
        let surfaceId: string | undefined;

        // Handle both single objects and arrays of messages
        const dataArr = Array.isArray(p.data) ? p.data : [p.data];

        for (const msg of dataArr) {
          if (msg && typeof msg === "object") {
            if ("beginRendering" in msg && msg.beginRendering) {
              surfaceId = msg.beginRendering.surfaceId;
              break; // found it
            } else if ("surfaceUpdate" in msg && msg.surfaceUpdate) {
              surfaceId = msg.surfaceUpdate.surfaceId;
              break; // found it
            }
          }
        }

        console.log("Found surfaceId in payload:", surfaceId);
        if (surfaceId && !this.#chatHistory.some(m => m.surfaceId === surfaceId)) {
          this.#chatHistory = [...this.#chatHistory, { role: 'agent', surfaceId, duration: `${durationMs}ms` }];
          console.log("Added surfaceId to chatHistory:", this.#chatHistory);
        }
      }
    }

    console.log("Final chat history before render:", this.#chatHistory);
    this.renderVersion++; // Force re-render of surfaces
    this.requestUpdate();
  }

  async #sendMessage(
    message: v0_8.Types.A2UIClientEventMessage
  ): Promise<Array<A2DataPayload | A2TextPayload>> {
    try {
      this.#requesting = true;
      const response = await this.#a2uiClient.send(message);

      this.#requesting = false;

      return response;
    } catch (err) {
      console.error("SendMessage Error:", err);
      this.snackbar(err as string, SnackType.ERROR);
    } finally {
      this.#requesting = false;
    }

    return [];
  }

  snackbar(
    message: string | HTMLTemplateResult,
    type: SnackType,
    actions: SnackbarAction[] = [],
    persistent = false,
    id = globalThis.crypto.randomUUID(),
    replaceAll = false
  ) {
    if (!this.#snackbar) {
      this.#pendingSnackbarMessages.push({
        message: {
          id,
          message,
          type,
          persistent,
          actions,
        },
        replaceAll,
      });
      return;
    }

    return this.#snackbar.show(
      {
        id,
        message,
        type,
        persistent,
        actions,
      },
      replaceAll
    );
  }

  unsnackbar(id?: SnackbarUUID) {
    if (!this.#snackbar) {
      return;
    }

    this.#snackbar.hide(id);
  }
}
