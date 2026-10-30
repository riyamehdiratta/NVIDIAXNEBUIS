(() => {
  if (window.__threadlineBrowserAgentInstalled) return;
  window.__threadlineBrowserAgentInstalled = true;

  const isThreadline = ["localhost", "127.0.0.1"].includes(location.hostname)
    && ["5173", "8000"].includes(location.port);
  let recording = false;
  let keyBuffer = "";
  let keyTarget = null;
  let keyTimer = null;

  function safeUrl() {
    return `${location.origin}${location.pathname}`;
  }

  function cssEscape(value) {
    return window.CSS?.escape ? CSS.escape(value) : String(value).replace(/[^a-zA-Z0-9_-]/g, "\\$&");
  }

  function selectorFor(node) {
    if (!(node instanceof Element)) return "";
    if (node.id) return `#${cssEscape(node.id)}`;
    const testId = node.getAttribute("data-testid");
    if (testId) return `[data-testid="${testId.replaceAll('"', '\\"')}"]`;
    const name = node.getAttribute("name");
    if (name) return `${node.tagName.toLowerCase()}[name="${name.replaceAll('"', '\\"')}"]`;
    const aria = node.getAttribute("aria-label");
    if (aria) return `${node.tagName.toLowerCase()}[aria-label="${aria.replaceAll('"', '\\"')}"]`;

    const parts = [];
    let current = node;
    while (current && current !== document.documentElement && parts.length < 6) {
      let part = current.tagName.toLowerCase();
      const parent = current.parentElement;
      if (parent) {
        const peers = [...parent.children].filter((child) => child.tagName === current.tagName);
        if (peers.length > 1) part += `:nth-of-type(${peers.indexOf(current) + 1})`;
      }
      parts.unshift(part);
      current = parent;
    }
    return parts.join(" > ");
  }

  function sendEvent(payload) {
    if (!recording || isThreadline) return Promise.resolve();
    return chrome.runtime.sendMessage({ type: "THREADLINE_RECORD_EVENT", payload }).catch(() => {});
  }

  function isPrivateTarget(target) {
    if (!(target instanceof Element)) return false;
    const privateHint = `${target.getAttribute("name") || ""} ${target.id || ""} ${target.getAttribute("autocomplete") || ""} ${target.getAttribute("aria-label") || ""}`;
    const normalizedHint = privateHint.toLowerCase().replace(/[^a-z0-9]/g, "");
    const privateField = ["password", "passcode", "secret", "token", "onetime", "otp", "creditcard", "cvc"].some((word) => normalizedHint.includes(word));
    return target.matches('input[type="password"],input[type="hidden"],input[type="file"]') || privateField;
  }

  function flushKeys() {
    if (keyTimer) clearTimeout(keyTimer);
    keyTimer = null;
    if (!keyBuffer || !keyTarget) return;
    const pending = sendEvent({
      event_type: "type",
      target_role: keyTarget.tag,
      target_name: keyTarget.name,
      value: keyBuffer,
      metadata: { url: safeUrl(), selector: keyTarget.selector, tag: keyTarget.tag, input_type: "editor", frame_url: location.href },
    });
    keyBuffer = "";
    keyTarget = null;
    return pending;
  }

  // Bridge commands from the Threadline page into the extension service worker.
  // The page itself cannot access chrome.runtime, so this listener is required
  // for the connection check, recording controls, and Run Agent command.
  window.addEventListener("message", (event) => {
    if (!isThreadline || event.source !== window || event.origin !== location.origin) return;
    const message = event.data;
    if (message?.type !== "THREADLINE_APP_COMMAND" || !message.request_id || !message.command) return;
    chrome.runtime.sendMessage(message.command).then((response) => {
      window.postMessage({ threadlineExtensionResponse: true, request_id: message.request_id, response }, location.origin);
    }).catch((error) => {
      window.postMessage({ threadlineExtensionResponse: true, request_id: message.request_id, error: error.message }, location.origin);
    });
  });

  document.addEventListener("click", (event) => {
    const raw = event.target instanceof Element ? event.target : event.target?.parentElement;
    if (!raw) return;
    const target = raw.closest("button,a,input[type=button],input[type=submit],[role=button],[role=link]") || raw;
    const selector = selectorFor(target);
    if (!selector) return;
    sendEvent({
      event_type: "click",
      target_role: target.getAttribute("role") || target.tagName.toLowerCase(),
      target_name: (target.getAttribute("aria-label") || target.innerText || target.value || target.getAttribute("name") || target.tagName).trim().slice(0, 120),
      coordinates: { x: Math.round(event.clientX), y: Math.round(event.clientY) },
      metadata: { url: safeUrl(), selector, tag: target.tagName.toLowerCase() },
    });
  }, true);

  document.addEventListener("change", (event) => {
    const target = event.target;
    if (!(target instanceof HTMLInputElement || target instanceof HTMLTextAreaElement || target instanceof HTMLSelectElement)) return;
    if (["password", "hidden", "file"].includes(target.type)) return;
    const privateHint = `${target.name} ${target.id} ${target.autocomplete} ${target.getAttribute("aria-label") || ""}`;
    if (/password|passcode|secret|token|one-time|otp|credit.?card|cvc/i.test(privateHint)) return;
    const selector = selectorFor(target);
    if (!selector) return;
    sendEvent({
      event_type: "type",
      target_role: target.tagName.toLowerCase(),
      target_name: (target.getAttribute("aria-label") || target.name || target.id || target.placeholder || "input").slice(0, 120),
      value: ["checkbox", "radio"].includes(target.type) ? String(target.checked) : target.value,
      metadata: { url: safeUrl(), selector, tag: target.tagName.toLowerCase(), input_type: target.type || "text" },
    });
  }, true);

  // Google Docs and other canvas based editors receive typing in an iframe or
  // hidden editor surface rather than a normal input. Capture completed text
  // bursts there so a recording contains useful steps instead of only clicks.
  document.addEventListener("keydown", (event) => {
    if (!recording || isThreadline || event.defaultPrevented || event.isComposing || event.ctrlKey || event.metaKey || event.altKey) return;
    const target = event.target instanceof Element ? event.target : document.body;
    if (!target || isPrivateTarget(target)) return;
    const ordinaryField = target instanceof HTMLInputElement || target instanceof HTMLTextAreaElement || target instanceof HTMLSelectElement;
    const docsEditor = location.hostname === "docs.google.com";
    const editorSurface = target.isContentEditable || target.getAttribute("role") === "textbox"
      || target.closest('[contenteditable="true"],[role="textbox"],.kix-appview-editor,.docs-texteventtarget-iframe');
    if (ordinaryField || (!docsEditor && !editorSurface)) return;

    if (event.key === "Backspace") keyBuffer = keyBuffer.slice(0, -1);
    else if (event.key === "Enter") keyBuffer += "\n";
    else if (event.key.length === 1) keyBuffer += event.key;
    else return;
    const element = target.closest('[contenteditable="true"],[role="textbox"]') || target;
    keyTarget = {
      selector: selectorFor(element) || "body",
      tag: element.tagName?.toLowerCase() || "body",
      name: (element.getAttribute?.("aria-label") || element.getAttribute?.("role") || "document editor").slice(0, 120),
    };
    if (keyTimer) clearTimeout(keyTimer);
    keyTimer = setTimeout(flushKeys, 700);
  }, true);

  document.addEventListener("visibilitychange", () => { if (document.visibilityState === "hidden") flushKeys(); });

  chrome.runtime.onMessage.addListener((message, _sender, sendResponse) => {
    if (message.type === "THREADLINE_SET_RECORDING") {
      const pending = message.recording ? Promise.resolve() : flushKeys();
      pending.finally(() => {
        recording = Boolean(message.recording);
        sendResponse({ ok: true });
      });
      return true;
    }
    if (message.type === "THREADLINE_REPLAY_STEP") {
      try {
        const step = message.step;
        const element = document.querySelector(step.metadata?.selector || "");
        if (!element) throw new Error(`Could not find “${step.name || "recorded control"}” on ${location.pathname}`);
        if (step.type === "click") {
          element.scrollIntoView({ block: "center", inline: "center" });
          element.click();
        } else if (step.type === "type") {
          if (element instanceof HTMLInputElement && ["checkbox", "radio"].includes(element.type)) {
            const checked = String(step.value) === "true";
            if (element.checked !== checked) element.click();
          } else if (element instanceof HTMLSelectElement) {
            element.value = step.value;
          } else {
            const proto = element instanceof HTMLTextAreaElement ? HTMLTextAreaElement.prototype : HTMLInputElement.prototype;
            const setter = Object.getOwnPropertyDescriptor(proto, "value")?.set;
            if (setter) setter.call(element, step.value ?? "");
            else element.value = step.value ?? "";
          }
          element.dispatchEvent(new Event("input", { bubbles: true }));
          element.dispatchEvent(new Event("change", { bubbles: true }));
        }
        sendResponse({ ok: true });
      } catch (error) {
        sendResponse({ ok: false, error: error.message });
      }
      return true;
    }
    return false;
  });

  if (isThreadline) {
    window.postMessage({ threadlineExtensionReady: true }, location.origin);
  }
})();
