const API = "http://127.0.0.1:8000/api";
let eventQueue = Promise.resolve();

async function post(path, body = {}) {
  const response = await fetch(`${API}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  const result = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(result.detail || `Threadline API returned ${response.status}`);
  return result;
}

async function get(path) {
  const response = await fetch(`${API}${path}`);
  const result = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(result.detail || `Threadline API returned ${response.status}`);
  return result;
}

async function sendToTab(tabId, message) {
  try {
    return await chrome.tabs.sendMessage(tabId, message);
  } catch {
    await chrome.scripting.executeScript({ target: { tabId }, files: ["content.js"] });
    return chrome.tabs.sendMessage(tabId, message);
  }
}

async function setAllTabsRecording(recording) {
  const tabs = await chrome.tabs.query({});
  const results = await Promise.all(tabs.map(async (tab) => {
    if (!tab.id || !/^https?:/.test(tab.url || "") || /^(http:\/\/localhost|http:\/\/127\.0\.0\.1):(?:5173|8000)\//.test(tab.url || "")) return null;
    try {
      await sendToTab(tab.id, { type: "THREADLINE_SET_RECORDING", recording });
      return { accessible: true, url: tab.url };
    } catch (error) {
      return { accessible: false, url: tab.url, error: error.message };
    }
  }));
  return results.filter(Boolean);
}

async function beginRecording(command) {
  const current = (await chrome.storage.local.get("threadlineState")).threadlineState;
  if (current?.recording) throw new Error("A browser task is already recording. Stop it before starting another.");
  const tab = (await chrome.tabs.query({ active: true, lastFocusedWindow: true }))[0];
  const started = await post("/apprenticeship/start", {
    title: command.title || "Browser task",
    process_name: "Chrome",
    window_title: tab?.title || "Chrome tab",
  });
  await chrome.storage.local.set({ threadlineState: { recording: true, traceId: started.trace_id, title: command.title || "Browser task", lastError: null } });
  const tabResults = await setAllTabsRecording(true);
  const failures = tabResults.filter((result) => !result.accessible);
  if (tabResults.length && !tabResults.some((result) => result.accessible)) {
    await chrome.storage.local.set({ threadlineState: { recording: false, traceId: started.trace_id, title: command.title, lastError: failures[0]?.error } });
    await post("/apprenticeship/stop", { trace_id: started.trace_id });
    throw new Error("Chrome has not allowed the extension to access your task page. Set Site access to On all sites, reload that website tab, then try again.");
  }
  return { recording: true, trace_id: started.trace_id };
}

async function stopRecording() {
  const state = (await chrome.storage.local.get("threadlineState")).threadlineState;
  if (!state?.recording) throw new Error("No browser task is recording.");
  await chrome.storage.local.set({ threadlineState: { ...state, recording: false } });
  await setAllTabsRecording(false);
  await eventQueue;
  const stopped = await post("/apprenticeship/stop", { trace_id: state.traceId });
  if (!stopped.total_events) {
    const detail = state.lastError ? ` Chrome could not access the task page: ${state.lastError}` : " Start from the Threadline tab, switch to a separate normal website tab, perform clicks or finish a text field, then stop from Threadline.";
    throw new Error(`No page actions were captured.${detail} Check the extension's Site access setting if needed.`);
  }
  return { recording: false, trace_id: state.traceId, event_count: stopped.total_events };
}

function waitForTab(tabId, timeoutMs = 20000) {
  return new Promise((resolve, reject) => {
    let timer;
    const listener = (updatedId, info) => {
      if (updatedId === tabId && info.status === "complete") {
        cleanup();
        resolve();
      }
    };
    const cleanup = () => {
      chrome.tabs.onUpdated.removeListener(listener);
      clearTimeout(timer);
    };
    timer = setTimeout(() => { cleanup(); reject(new Error("Timed out waiting for the page to load.")); }, timeoutMs);
    chrome.tabs.onUpdated.addListener(listener);
    chrome.tabs.get(tabId).then((tab) => {
      if (tab.status === "complete") { cleanup(); resolve(); }
    }).catch(() => { cleanup(); reject(new Error("The replay tab was closed.")); });
  });
}

async function navigate(tabId, url) {
  const target = new URL(url);
  if (!/^https?:$/.test(target.protocol)) throw new Error("Replay is limited to ordinary web pages.");
  const tab = await chrome.tabs.get(tabId);
  const current = tab.url ? new URL(tab.url) : null;
  if (current?.origin === target.origin && current.pathname === target.pathname) {
    if (tab.status !== "complete") await waitForTab(tabId);
    return;
  }
  await chrome.tabs.update(tabId, { url: target.href });
  await waitForTab(tabId);
  await new Promise((resolve) => setTimeout(resolve, 400));
}

async function runTrace(traceId) {
  const trace = await get(`/apprenticeship/traces/${encodeURIComponent(traceId)}`);
  if (!trace.events?.length) throw new Error("This recorded task has no replayable steps.");
  const firstUrl = trace.events.find((event) => event.metadata?.url)?.metadata.url;
  if (!firstUrl) throw new Error("This task does not contain browser page locations.");
  const tab = await chrome.tabs.create({ url: firstUrl, active: true });
  await waitForTab(tab.id);
  let completed = 0;

  for (const step of trace.events) {
    const stepUrl = step.metadata?.url;
    if (stepUrl) await navigate(tab.id, stepUrl);
    await new Promise((resolve) => setTimeout(resolve, 350));
    let result;
    try {
      result = await sendToTab(tab.id, { type: "THREADLINE_REPLAY_STEP", step });
    } catch (error) {
      if (step.type !== "click") throw new Error(`Step ${completed + 1} failed: ${error.message}`);
      // A successful click can navigate away before Chrome returns its reply.
      await new Promise((resolve) => setTimeout(resolve, 700));
    }
    if (result && !result.ok) throw new Error(`Step ${completed + 1} failed: ${result.error}`);
    completed += 1;
    await new Promise((resolve) => setTimeout(resolve, 600));
  }
  return { ran: true, title: trace.title, completed_steps: completed, tab_id: tab.id };
}

async function handleCommand(message) {
  switch (message.type) {
    case "THREADLINE_EXTENSION_STATUS": {
      const state = (await chrome.storage.local.get("threadlineState")).threadlineState;
      return { installed: true, recording: Boolean(state?.recording), trace_id: state?.traceId || null, last_error: state?.lastError || null };
    }
    case "THREADLINE_CAPTURE_START":
      return beginRecording(message);
    case "THREADLINE_CAPTURE_STOP":
      return stopRecording();
    case "THREADLINE_RUN_TRACE":
      return runTrace(message.trace_id);
    case "THREADLINE_RECORD_EVENT": {
      const state = (await chrome.storage.local.get("threadlineState")).threadlineState;
      if (!state?.recording) return { ignored: true };
      eventQueue = eventQueue.then(() => post("/apprenticeship/record_event", {
        trace_id: state.traceId,
        event_type: message.payload.event_type,
        target_role: message.payload.target_role,
        target_name: message.payload.target_name,
        value: message.payload.value ?? null,
        coordinates: message.payload.coordinates ?? null,
        metadata: message.payload.metadata ?? {},
      }));
      await eventQueue;
      return { recorded: true };
    }
    default:
      return { error: "Unknown Threadline extension command." };
  }
}

chrome.runtime.onMessage.addListener((message, _sender, sendResponse) => {
  handleCommand(message).then(sendResponse).catch((error) => sendResponse({ error: error.message }));
  return true;
});

chrome.runtime.onStartup.addListener(async () => {
  const state = (await chrome.storage.local.get("threadlineState")).threadlineState;
  if (state?.recording) {
    await chrome.storage.local.set({ threadlineState: { ...state, recording: false } });
    try { await post("/apprenticeship/stop", { trace_id: state.traceId }); } catch {}
  }
});

chrome.tabs.onUpdated.addListener(async (tabId, changeInfo, tab) => {
  if (changeInfo.status !== "complete" || !/^https?:/.test(tab.url || "")) return;
  const state = (await chrome.storage.local.get("threadlineState")).threadlineState;
  if (!state?.recording) return;
  try {
    await sendToTab(tabId, { type: "THREADLINE_SET_RECORDING", recording: true });
  } catch (error) {
    await chrome.storage.local.set({ threadlineState: { ...state, lastError: error.message } });
  }
});
