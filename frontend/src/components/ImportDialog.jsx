import { Check, FileText, LoaderCircle, Play, Square, Upload, Video, X } from 'lucide-react';
import { useCallback, useEffect, useRef, useState } from 'react';
import { api } from '../api';

function extensionCommand(type, extra = {}, timeoutMs = 10000) {
  return new Promise((resolve, reject) => {
    const requestId = crypto.randomUUID();
    const timeout = window.setTimeout(() => {
      window.removeEventListener('message', onMessage);
      reject(new Error('Threadline Browser Actions is not connected. Load browser-extension in Chrome and reload this page.'));
    }, timeoutMs);
    function onMessage(event) {
      if (event.source !== window || event.origin !== window.location.origin) return;
      if (!event.data?.threadlineExtensionResponse || event.data.request_id !== requestId) return;
      window.clearTimeout(timeout);
      window.removeEventListener('message', onMessage);
      if (event.data.error) reject(new Error(event.data.error));
      else if (event.data.response?.error) reject(new Error(event.data.response.error));
      else resolve(event.data.response);
    }
    window.addEventListener('message', onMessage);
    window.postMessage({
      type: 'THREADLINE_APP_COMMAND',
      request_id: requestId,
      command: { type, ...extra },
    }, window.location.origin);
  });
}

export function ImportDialog({ onClose, onText, onFiles, setToast }) {
  const [activeTab, setActiveTab] = useState('record');
  const [text, setText] = useState('');
  const [taskName, setTaskName] = useState('My browser task');
  const [extension, setExtension] = useState({ installed: false, recording: false });
  const [capturedStepCount, setCapturedStepCount] = useState(0);
  const [traces, setTraces] = useState([]);
  const [busy, setBusy] = useState('');
  const [message, setMessage] = useState('');
  const [reviewTrace, setReviewTrace] = useState(null);
  const fileInputRef = useRef(null);

  const refresh = useCallback(async () => {
    try { setTraces(await api('/apprenticeship/traces')); } catch {}
  }, []);

  useEffect(() => {
    let alive = true;
    const checkExtension = async () => {
      try {
        const status = await extensionCommand('THREADLINE_EXTENSION_STATUS');
        if (alive) {
          setExtension(status);
          if (status.last_error) setMessage(`Chrome could not access a task page: ${status.last_error}. Set the extension's Site access to On all sites and reload that tab.`);
        }
      } catch {
        if (alive) setExtension({ installed: false, recording: false });
      }
    };
    checkExtension();
    refresh();
    const id = window.setInterval(() => {
      checkExtension();
      refresh();
    }, 5000);
    return () => { alive = false; window.clearInterval(id); };
  }, [refresh]);

  useEffect(() => {
    if (!extension.recording || !extension.trace_id) return undefined;
    let alive = true;
    const readCount = async () => {
      try {
        const trace = await api(`/apprenticeship/traces/${extension.trace_id}`);
        if (alive) setCapturedStepCount(trace.event_count || 0);
      } catch {}
    };
    readCount();
    const id = window.setInterval(readCount, 1000);
    return () => { alive = false; window.clearInterval(id); };
  }, [extension.recording, extension.trace_id]);

  const startRecording = async () => {
    setBusy('start');
    setMessage('');
    try {
      const result = await extensionCommand('THREADLINE_CAPTURE_START', { title: taskName.trim() || 'Browser task' }, 30000);
      setExtension({ installed: true, recording: true, trace_id: result.trace_id });
      setCapturedStepCount(0);
      setMessage('Recording browser clicks and completed text fields. Switch to a Chrome page and perform the task.');
    } catch (error) {
      setMessage(error.message);
    } finally { setBusy(''); }
  };

  const stopRecording = async () => {
    setBusy('stop');
    setMessage('Saving action steps…');
    try {
      const result = await extensionCommand('THREADLINE_CAPTURE_STOP', {}, 120000);
      setExtension({ installed: true, recording: false });
      setCapturedStepCount(result.event_count || 0);
      setMessage(`Saved “${taskName}” as ${result.event_count} browser action steps.`);
      await refresh();
    } catch (error) {
      setExtension((current) => ({ ...current, recording: false }));
      setMessage(error.message);
      await refresh();
    } finally { setBusy(''); }
  };

  const reviewTask = async (trace) => {
    setBusy(`run:${trace.id}`);
    try {
      const detail = await api(`/apprenticeship/traces/${trace.id}`);
      setReviewTrace({ trace, events: detail.events });
    } catch (error) {
      setMessage(`Could not load the saved steps: ${error.message}`);
    } finally { setBusy(''); }
  };

  const runTask = async () => {
    if (!reviewTrace) return;
    const trace = reviewTrace.trace;
    setBusy(`run:${trace.id}`);
    setMessage(`Running “${trace.title}” in a new Chrome tab…`);
    try {
      const result = await extensionCommand('THREADLINE_RUN_TRACE', { trace_id: trace.id }, 10 * 60 * 1000);
      setMessage(`Finished ${result.completed_steps} steps for “${result.title}”.`);
      setReviewTrace(null);
    } catch (error) {
      setMessage(`Run stopped: ${error.message}`);
    } finally { setBusy(''); }
  };

  return (
    <div className="modal-backdrop" onMouseDown={(event) => event.target === event.currentTarget && !extension.recording && onClose()}>
      <section className="dialog import-dialog" style={{ maxWidth: 680 }}>
        <header className="dialog-header">
          <div><div className="eyebrow">THREADLINE CAPTURE</div><h2>Record a browser task</h2></div>
          <button className="icon-button" onClick={onClose} disabled={extension.recording}><X size={18} /></button>
        </header>

        <div style={{ display: 'flex', gap: 6, margin: '14px 0 16px', borderBottom: '1px solid #1f2c22', paddingBottom: 10 }}>
          <button className={`button ${activeTab === 'record' ? 'button-primary' : 'button-soft'}`} onClick={() => setActiveTab('record')} disabled={extension.recording}><Video size={13} /> Record & run</button>
          <button className={`button ${activeTab === 'files' ? 'button-primary' : 'button-soft'}`} onClick={() => setActiveTab('files')} disabled={extension.recording}><Upload size={13} /> Import files</button>
          <button className={`button ${activeTab === 'text' ? 'button-primary' : 'button-soft'}`} onClick={() => setActiveTab('text')} disabled={extension.recording}><FileText size={13} /> Paste note</button>
        </div>

        {activeTab === 'record' && <div>
          <p className="dialog-intro">Threadline Browser Actions records clicks and typed text on Chrome pages, including editor frames such as Google Docs, then saves the steps for review and replay. Start here, switch to a separate website tab, do the task, then return here to stop. Chrome’s address bar and other desktop apps are outside the recording.</p>
          {!extension.installed && <div className="local-caveat" style={{ marginBottom: 12 }}><span><b>Threadline can’t reach the extension yet.</b> In <code>chrome://extensions</code>, confirm Threadline Browser Actions is enabled, set its Site access to <b>On all sites</b>, click its <b>Reload</b> icon, then reload this Threadline tab. If it is not installed, enable Developer mode and choose Load unpacked → this project’s <code>browser-extension</code> folder. If it still does not connect, open the extension’s <b>Errors</b> panel there and check for a service-worker error.</span></div>}
          <div style={{ background: '#0e1610', border: '1px solid #1e2c21', borderRadius: 8, padding: 14 }}>
            <label style={{ display: 'block', marginBottom: 5, color: '#88ab8d', font: '600 9px var(--mono)' }}>TASK NAME</label>
            <input value={taskName} onChange={(event) => setTaskName(event.target.value)} disabled={extension.recording} maxLength={120} style={{ width: '100%', padding: '8px 10px', background: '#162219', border: '1px solid #273b2c', borderRadius: 5, color: '#e0ece2', fontSize: 12 }} />
            <div style={{ marginTop: 10, padding: 10, color: '#a6b4a7', background: '#101812', borderRadius: 6, fontSize: 10, lineHeight: 1.6 }}>
              Recorded page text stays in this local Threadline database. Password, file, and fields labeled as secrets are skipped. Typed document text is captured so it can be reviewed and replayed; avoid private content.
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: 12, marginTop: 12 }}>
              <span style={{ color: '#799a7d', fontSize: 10 }}>{extension.recording ? `RECORDING · ${capturedStepCount} action${capturedStepCount === 1 ? '' : 's'} captured` : 'Record a task, stop, then run it from your saved list.'}</span>
              {extension.recording ? <button className="button button-primary" disabled={busy !== ''} onClick={stopRecording}><Square size={13} /> Stop & save</button> : <button className="button button-primary" disabled={!extension.installed || busy !== ''} onClick={startRecording}>{busy === 'start' ? <LoaderCircle size={14} className="spin" /> : <Video size={14} />} Start recording</button>}
            </div>
          </div>
          {message && <div className="quiet-empty" style={{ marginTop: 10 }}><span className="quiet-check"><Check size={15} /></span><div>{message}</div></div>}
          <section style={{ marginTop: 16 }}>
            <div className="panel-head"><div><div className="eyebrow">SAVED BROWSER TASKS</div><h2>Run Agent <span className="small-count">{traces.filter((trace) => trace.replayable).length}</span></h2></div><button className="text-button" onClick={refresh}>Refresh</button></div>
            {traces.filter((trace) => trace.replayable).length ? <div className="source-list">{traces.filter((trace) => trace.replayable).map((trace) => <div className="source-row" key={trace.id}><div className="source-file-icon source-note"><Play size={15} /></div><div className="source-info"><strong>{trace.title}</strong><span>{trace.event_count} recorded steps · {new Date(trace.created_at).toLocaleString()}</span></div><button className="button button-primary" disabled={!extension.installed || busy !== '' || extension.recording} onClick={() => reviewTask(trace)}>{busy === `run:${trace.id}` ? <LoaderCircle size={14} className="spin" /> : <Play size={14} />} Review</button></div>)}</div> : <div className="quiet-empty"><span className="quiet-check"><Video size={15} /></span><div><strong>No replayable browser tasks saved yet.</strong><p>Install the extension, record a task in Chrome, then it will appear here.</p></div></div>}
          </section>
          {reviewTrace && <div className="modal-backdrop" style={{ zIndex: 40 }} onMouseDown={(event) => event.target === event.currentTarget && setReviewTrace(null)}><section className="dialog" style={{ maxWidth: 620 }}><header className="dialog-header"><div><div className="eyebrow">REVIEW BEFORE REPLAY</div><h2>{reviewTrace.trace.title}</h2></div><button className="icon-button" onClick={() => setReviewTrace(null)}><X size={18} /></button></header><p className="dialog-intro">Run Agent repeats these browser actions in a new tab. It can submit forms or send messages. Check every text field before you run it.</p><ol style={{ maxHeight: 320, overflow: 'auto', paddingLeft: 22 }}>{reviewTrace.events.map((step, index) => <li key={`${step.step}-${index}`} style={{ margin: '8px 0', color: '#637064', fontSize: 11 }}><b>{step.type === 'type' ? (['checkbox', 'radio'].includes(step.metadata?.input_type) ? `${step.value === 'true' ? 'Check' : 'Uncheck'} ${step.name || 'option'}` : `Enter in ${step.name || 'field'}`) : `Click ${step.name || 'page control'}`}</b>{step.type === 'type' && !['checkbox', 'radio'].includes(step.metadata?.input_type) && <pre style={{ margin: '4px 0', padding: 8, whiteSpace: 'pre-wrap', overflowWrap: 'anywhere', background: '#f5f7f3', borderRadius: 5 }}>{step.value}</pre>}<small style={{ display: 'block', color: '#9aa39a' }}>{step.metadata?.url}</small></li>)}</ol><footer className="dialog-footer"><button className="button button-soft" onClick={() => setReviewTrace(null)} disabled={busy !== ''}>Cancel</button><button className="button button-primary" onClick={runTask} disabled={busy !== ''}><Play size={14} /> {busy === `run:${reviewTrace.trace.id}` ? 'Running Agent…' : 'Run Agent'}</button></footer></section></div>}
        </div>}

        {activeTab === 'files' && <div><p className="dialog-intro">Drop an email, calendar file, or note into your private workspace.</p><button className="dropzone" onClick={() => fileInputRef.current?.click()}><span className="drop-icon"><Upload size={20} /></span><strong>Choose files to import</strong><small>.eml, .ics, .txt, .md, .csv · up to 2 MB</small><input ref={fileInputRef} hidden multiple type="file" accept=".eml,.ics,.txt,.md,.csv,.log" onChange={(event) => event.target.files?.length && onFiles(event.target.files)} /></button></div>}

        {activeTab === 'text' && <div><p className="dialog-intro">Paste an email, a thought, or an open commitment. Threadline extracts tasks and saves them locally.</p><textarea value={text} onChange={(event) => setText(event.target.value)} className="capture-text" placeholder="Paste an email, notes, or a commitment you want to track…" rows={6} /><footer className="dialog-footer" style={{ marginTop: 12 }}><span><FileText size={14} /> Saved locally</span><button className="button button-primary" disabled={!text.trim()} onClick={() => onText(text)}>Add to Threadline</button></footer></div>}
      </section>
    </div>
  );
}
