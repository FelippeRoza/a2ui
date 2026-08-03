import { LitElement, html, css } from "lit";
import { customElement, property, query, state } from "lit/decorators.js";
import { keyed } from "lit/directives/keyed.js";

@customElement("a2ui-secure-iframe")
export class SecureIframe extends LitElement {
  @property({ type: String })
  accessor htmlContent: string | undefined;

  @property({ type: String })
  accessor url: string | undefined;

  @property({ type: Object })
  accessor widgetData: Record<string, any> | undefined;

  @query("iframe")
  accessor iframe!: HTMLIFrameElement;

  @state()
  accessor #isReady = false;

  @state()
  accessor #iframeKey = 0;

  static styles = css`
    :host {
      display: block;
      width: 100%;
      height: 100%;
      min-height: 400px;
      max-height: 750px;
    }
    iframe {
      width: 100%;
      height: 100%;
      border: none;
      border-radius: 8px;
    }
  `;

  render() {
    return keyed(
      this.#iframeKey,
      html`<iframe sandbox="allow-scripts allow-popups allow-forms" src="${this.url || '/sandbox.html'}"></iframe>`
    );
  }


  #sendPayload() {
    if (this.#isReady && this.htmlContent && this.iframe?.contentWindow) {
      this.iframe.contentWindow.postMessage({
        type: 'render-html',
        htmlContent: this.htmlContent
      }, "*"); // Send to sandbox origin
    }
    this.#sendDataUpdate();
  }

  #sendDataUpdate() {
    if (this.#isReady && this.widgetData && this.iframe?.contentWindow) {
      // Deep clone the data to stringify/parse to strip out any Mobx/Lit proxies 
      // or non-serializable objects that cause DataCloneError in postMessage.
      const cleanData = JSON.parse(JSON.stringify(this.widgetData));
      this.iframe.contentWindow.postMessage({
        type: 'UPDATE_DATA',
        widgetData: cleanData
      }, "*");
    }
  }

  updated(changedProperties: Map<string, any>) {
    if (changedProperties.has('htmlContent')) {
      this.#isReady = false;
      this.#iframeKey++;
    } else if (changedProperties.has('url')) {
      this.#sendPayload();
    } else if (changedProperties.has('widgetData')) {
      // Fast path: Don't remount iframe, just push new data natively!
      this.#sendDataUpdate();
    }
  }

  connectedCallback() {
    super.connectedCallback();
    window.addEventListener("message", this.#handleMessage);
  }

  disconnectedCallback() {
    super.disconnectedCallback();
    window.removeEventListener("message", this.#handleMessage);
  }

  #handleMessage = (event: MessageEvent) => {
    // Basic structural check
    if (event.source === this.iframe?.contentWindow) {
      if (event.data?.type === "sandbox-ready") {
        this.#isReady = true;
        this.#sendPayload();
      } else if (event.data?.type === "REQUEST_DATA") {
        // The React component inside has mounted and is now explicitly asking for it!
        this.#sendDataUpdate();
      } else if (event.data?.type === "a2ui-action") {
        this.dispatchEvent(new CustomEvent("a2uiaction", {
          detail: event.data.detail,
          bubbles: true,
          composed: true
        }));
      } else if (event.data?.type === "resize" && typeof event.data.height === "number") {
        const minH = Math.max(400, event.data.height);
        this.style.height = `${minH}px`;
        // Let the iframe inherit height: 100% from its host.
        // If host is capped at 600px, iframe is 600px.
        // Content inside iframe can internally scroll!
      }
    }
  }
}
