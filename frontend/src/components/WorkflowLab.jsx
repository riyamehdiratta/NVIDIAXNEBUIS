import { useEffect, useMemo, useState } from 'react';
import { AlertTriangle, ArrowRight, Check, ChevronDown, Clock, GitBranch, LoaderCircle, LockKeyhole, Play, Plus, RefreshCw, RotateCcw, ShieldCheck, Sparkles, Trash2, WandSparkles, X, Zap } from 'lucide-react';
import { api, post } from '../api';
import './WorkflowLab.css';

export function WorkflowLab({ apiKeyConfigured, demoMode, setToast }) {
  const [workflows, setWorkflows] = useState([]);
  const [schedules, setSchedules] = useState([]);
  const [requestText, setRequestText] = useState('');
  const [name, setName] = useState('');
  const [baseId, setBaseId] = useState('');
  const [saveAsSkill, setSaveAsSkill] = useState(true);
  const [compilePreview, setCompilePreview] = useState(null);
  const [compileConsent, setCompileConsent] = useState(false);
  const [busy, setBusy] = useState('');
  const [inputTexts, setInputTexts] = useState({});
  const [runPreview, setRunPreview] = useState(null);
  const [runReceipt, setRunReceipt] = useState(null);
  const [promotionInfo, setPromotionInfo] = useState(null);

  const refresh = async () => {
    const [wfs, schs] = await Promise.all([
      api('/workflows/templates'),
      api('/workflows/schedules').catch(() => [])
    ]);
    setWorkflows(wfs);
    setSchedules(schs);
  };

  useEffect(() => { refresh().catch(e => setToast(e.message)); }, []);
  const custom = useMemo(() => workflows.filter(w => w.id.startsWith('wf_')), [workflows]);

  const createPreview = async event => {
    event.preventDefault();
    setBusy('compile');
    if (compilePreview?.preview_id) {
      try { await api(`/workflows/compile/previews/${compilePreview.preview_id}`, { method: 'DELETE' }); } catch { /* Old previews expire automatically. */ }
    }
    setCompilePreview(null);
    setRunPreview(null);
    setRunReceipt(null);
    try {
      const result = await post('/workflows/compile/preview', {
        request: requestText,
        name: name || 'My workflow',
        save_as_skill: saveAsSkill,
        update_workflow_id: baseId || null,
      });
      setCompilePreview(result);
      setCompileConsent(false);
    } catch (e) { setToast(e.message); }
    finally { setBusy(''); }
  };

  const confirmCompile = async () => {
    if (!compilePreview || !compileConsent) return;
    setBusy('confirm-compile');
    try {
      const result = await post('/workflows/compile/confirm', { preview_id: compilePreview.preview_id, confirmed: true });
      if (!result.compiled) { setToast(result.message || 'The generated workflow did not pass validation'); return; }
      const initial = Object.fromEntries(Object.entries(result.workflow.inputs || {}).map(([key, def]) => [key, def.type === 'string_list' ? [] : def.type === 'integer' ? 0 : '']));
      setInputTexts(current => ({ ...current, [result.workflow.id]: JSON.stringify(initial, null, 2) }));
      await refresh();
      setToast('Workflow saved. Review its execution plan before running it.');
    } catch (e) { setToast(e.message); }
    finally { setBusy(''); setCompilePreview(null); setCompileConsent(false); }
  };

  const cancelPreview = async () => {
    if (compilePreview?.preview_id) {
      try { await api(`/workflows/compile/previews/${compilePreview.preview_id}`, { method: 'DELETE' }); } catch { /* A stale preview expires automatically. */ }
    }
    setCompilePreview(null);
    setCompileConsent(false);
  };

  const inspectRun = async workflow => {
    setBusy(`simulate:${workflow.id}`);
    setRunReceipt(null);
    try {
      const inputs = JSON.parse(inputTexts[workflow.id] || '{}');
      const preview = await post('/workflows/simulate', { workflow_id: workflow.id, inputs });
      setRunPreview({ workflow, inputs, plan: preview });
    } catch (e) { setToast(typeof e.message === 'string' ? e.message : JSON.stringify(e.message)); }
    finally { setBusy(''); }
  };

  const execute = async () => {
    if (!runPreview) return;
    setBusy('run');
    try {
      const receipt = await post('/workflows/runs', {
        workflow_id: runPreview.workflow.id,
        inputs: runPreview.inputs,
        approved: true,
        idempotency_key: `ui-${crypto.randomUUID()}`,
      });
      setRunReceipt(receipt);
      setToast(receipt.status === 'completed' ? 'Workflow finished and saved locally' : `Workflow ${receipt.status}`);
    } catch (e) { setToast(e.message); }
    finally { setBusy(''); }
  };

  const repairRun = async runId => {
    setBusy('repair');
    try {
      const updated = await post(`/workflows/runs/${runId}/repair`);
      setRunReceipt(updated);
      setToast(`Repaired node and completed run (attempt ${updated.repair_attempts}/2)`);
    } catch (e) { setToast(e.message); }
    finally { setBusy(''); }
  };

  const rollbackRun = async runId => {
    setBusy('rollback');
    try {
      const result = await post(`/workflows/runs/${runId}/rollback`);
      setRunReceipt(result.run);
      setToast(`Side effects rolled back (${result.compensation.status})`);
    } catch (e) { setToast(e.message); }
    finally { setBusy(''); }
  };

  const checkPromotion = async workflowId => {
    try {
      const info = await api(`/workflows/definitions/${workflowId}/promotion`);
      setPromotionInfo(info);
    } catch (e) { setToast(e.message); }
  };

  const promoteSkill = async workflowId => {
    try {
      await post(`/workflows/definitions/${workflowId}/promote`);
      await refresh();
      setPromotionInfo(null);
      setToast('Workflow successfully promoted to published skill');
    } catch (e) { setToast(e.message); }
  };

  const scheduleHourly = async workflowId => {
    try {
      await post('/workflows/schedules', { workflow_id: workflowId, cron_expression: '0 * * * *' });
      await refresh();
      setToast('Scheduled hourly execution for workflow');
    } catch (e) { setToast(e.message); }
  };

  const toggleSchedule = async scheduleId => {
    try {
      await post(`/workflows/schedules/${scheduleId}/toggle`);
      await refresh();
    } catch (e) { setToast(e.message); }
  };

  const deleteSchedule = async scheduleId => {
    try {
      await api(`/workflows/schedules/${scheduleId}`, { method: 'DELETE' });
      await refresh();
      setToast('Schedule removed');
    } catch (e) { setToast(e.message); }
  };

  const removeWorkflow = async id => {
    if (!window.confirm('Delete this workflow and its run history?')) return;
    try {
      await api(`/workflows/definitions/${id}`, { method: 'DELETE' });
      await refresh();
      setRunPreview(null);
      setRunReceipt(null);
      setToast('Workflow and run history deleted');
    } catch (e) { setToast(e.message); }
  };

  return <div className="workflow-lab">
    <section className="panel workflow-builder">
      <div className="panel-head"><div><div className="eyebrow">AGENT WORKFLOW COMPILER</div><h2>Describe the workflow you want.</h2></div><span className="local-tag"><GitBranch size={13} /> Guarded execution</span></div>
      <p className="section-intro">Nemotron turns your request into a versioned workflow DAG using registered local tools, dynamic map/branch control flow, and independent verification. It cannot invent a connector or escape the sandbox.</p>
      <form className="workflow-form" onSubmit={createPreview}>
        <div className="workflow-form-row">
          <label>WORKFLOW / SKILL NAME<input required maxLength={100} value={name} onChange={e => setName(e.target.value)} placeholder="e.g. Batch scan and review sources" /></label>
          <label>START FROM OR REVISE<select value={baseId} onChange={e => { setBaseId(e.target.value); const selected = workflows.find(w => w.id === e.target.value); if (selected?.id.startsWith('wf_') && saveAsSkill) setName(selected.name); }}><option value="">Start from the tool catalog</option>{workflows.map(w => <option key={w.id} value={w.id}>{w.id.startsWith('wf_') ? 'Revise skill' : 'Copy built-in'} · {w.name} · v{w.version}</option>)}</select></label>
        </div>
        <label className="workflow-request-label">WHAT SHOULD IT DO?<textarea required minLength={8} maxLength={3000} rows={5} value={requestText} onChange={e => setRequestText(e.target.value)} placeholder="Example: List all unread sources, map over them to inspect summaries, branch on findings, and run an independent verification check. Never change external state without asking." /></label>
        <label className="workflow-save-skill"><input type="checkbox" checked={saveAsSkill} onChange={e => setSaveAsSkill(e.target.checked)} /> Save this as a reusable skill. You can promote it to published status once verified.</label>
        <div className="workflow-form-footer"><span><LockKeyhole size={13} /> Your sources and memory are not sent to the planner. The redacted task request is previewed before any model call.</span><button className="button button-primary" disabled={!apiKeyConfigured || demoMode || busy === 'compile'}>{busy === 'compile' ? <LoaderCircle size={14} className="spin" /> : <WandSparkles size={14} />} {demoMode ? 'Disabled in public demo' : apiKeyConfigured ? 'Build workflow preview' : 'Nebius key required'}</button></div>
      </form>
      {!apiKeyConfigured && !demoMode && <div className="workflow-warning"><AlertTriangle size={14} />Add <code>NEBIUS_API_KEY</code> to compile a new workflow. Existing local workflows continue to work.</div>}
      {demoMode && <div className="workflow-warning"><AlertTriangle size={14} />Workflow compilation is disabled in the public synthetic-data demo to protect the hosted API key. Run Threadline locally to compile custom workflows.</div>}
    </section>

    {compilePreview && <section className="panel workflow-egress-preview">
      <div className="panel-head"><div><div className="eyebrow">MODEL PREFLIGHT</div><h2>Review exactly what leaves this device.</h2></div><button className="icon-button" disabled={busy === 'confirm-compile'} onClick={cancelPreview}><X size={17} /></button></div>
      <div className="workflow-privacy-note"><ShieldCheck size={15} /><span>The request includes the redacted task, tool manifests, and spec schema{compilePreview.base_spec_included ? ', plus the selected workflow spec being revised' : ''}. Personal sources and memory are excluded.</span></div>
      <div className="workflow-meta"><span>MODEL <b>{compilePreview.model}</b></span><span>REDACTIONS <b>{compilePreview.redacted_fields}</b></span></div>
      <pre className="workflow-payload">{compilePreview.payload}</pre>
      <label className="workflow-consent"><input type="checkbox" checked={compileConsent} onChange={e => setCompileConsent(e.target.checked)} /> I inspected this exact payload and approve sending it to Nebius Token Factory for workflow compilation.</label>
      <div className="workflow-form-footer"><button className="button button-soft" disabled={busy === 'confirm-compile'} onClick={cancelPreview}>Cancel</button><button className="button button-primary" disabled={!compileConsent || busy === 'confirm-compile'} onClick={confirmCompile}>{busy === 'confirm-compile' ? <LoaderCircle size={14} className="spin" /> : <ArrowRight size={14} />} Confirm and compile</button></div>
    </section>}

    <section className="panel workflow-library">
      <div className="panel-head"><div><div className="eyebrow">VERSIONED LIBRARY</div><h2>Your workflows and skills <span className="small-count">{custom.length}</span></h2></div><span className="local-tag"><LockKeyhole size={13} /> Stored locally</span></div>
      {custom.length ? custom.map(workflow => <article className="workflow-card" key={workflow.id}>
        <div className="workflow-card-title">
          <div className="workflow-card-icon"><GitBranch size={16} /></div>
          <div>
            <h3>{workflow.name}</h3>
            <p>{workflow.description || 'Custom workflow'} · {workflow.origin === 'skill' ? 'reusable skill' : 'one-off workflow'} · v{workflow.version}</p>
          </div>
          <button className="icon-button workflow-delete" title="Delete workflow" onClick={() => removeWorkflow(workflow.id)}><Trash2 size={14} /></button>
        </div>
        <div className="workflow-tool-list">
          {workflow.tools.map(tool => <code key={tool}>{tool}</code>)}
        </div>
        <details className="workflow-details"><summary>Inspect workflow spec <ChevronDown size={13} /></summary><pre>{JSON.stringify(workflow.spec, null, 2)}</pre></details>
        <label className="workflow-input-label">RUN INPUTS (JSON)<textarea rows={2} value={inputTexts[workflow.id] || '{}'} onChange={e => setInputTexts(current => ({ ...current, [workflow.id]: e.target.value }))} placeholder="{}" /></label>
        <div className="workflow-action-buttons" style={{ display: 'flex', gap: '8px', flexWrap: 'wrap', marginTop: '8px' }}>
          <button className="button button-soft" disabled={busy.startsWith('simulate:')} onClick={() => inspectRun(workflow)}><ShieldCheck size={14} /> Preview run</button>
          <button className="button button-soft" onClick={() => scheduleHourly(workflow.id)}><Clock size={14} /> Schedule (1h)</button>
          <button className="button button-soft" onClick={() => checkPromotion(workflow.id)}><Sparkles size={14} /> Promotion status</button>
        </div>
      </article>) : <div className="workflow-empty"><div className="empty-spark"><GitBranch size={18} /></div><strong>No custom workflow saved yet.</strong><span>Describe one above. It will become an inspectable, reusable skill.</span></div>}
      {workflows.filter(w => !w.id.startsWith('wf_')).length > 0 && <details className="workflow-builtins"><summary>Built-in workflows <ChevronDown size={13} /></summary>{workflows.filter(w => !w.id.startsWith('wf_')).map(w => <div key={w.id}><span><b>{w.name}</b><small>{w.description}</small></span><button className="edit-skill" onClick={() => { setBaseId(w.id); setName(`${w.name} variant`); window.scrollTo({ top: 0, behavior: 'smooth' }); }}><Plus size={13} /> Create a variant</button></div>)}</details>}
    </section>

    {schedules.length > 0 && <section className="panel workflow-schedules">
      <div className="panel-head"><div><div className="eyebrow">AUTOMATED TRIGGERS</div><h2>Scheduled Workflows <span className="small-count">{schedules.length}</span></h2></div><span className="local-tag"><Clock size={13} /> Background worker</span></div>
      <div className="workflow-step-list">
        {schedules.map(sch => <div className="workflow-step" key={sch.id}>
          <span><Clock size={13} /></span>
          <div>
            <strong>{sch.workflow_name}</strong>
            <small>{sch.cron_expression || 'Hourly'} · Next: {sch.next_run ? new Date(sch.next_run).toLocaleTimeString() : 'Pending'} · {sch.enabled ? 'Active' : 'Paused'}</small>
          </div>
          <div style={{ display: 'flex', gap: '6px' }}>
            <button className="button button-soft" style={{ padding: '3px 8px', fontSize: '9px' }} onClick={() => toggleSchedule(sch.id)}>{sch.enabled ? 'Pause' : 'Resume'}</button>
            <button className="icon-button" style={{ width: '24px', height: '24px' }} onClick={() => deleteSchedule(sch.id)}><Trash2 size={12} /></button>
          </div>
        </div>)}
      </div>
    </section>}

    {promotionInfo && <section className="panel workflow-promotion-modal" style={{ padding: '16px', border: '1px solid #c2dbbe', borderRadius: '8px', background: '#f7fbf6' }}>
      <div className="panel-head">
        <div><div className="eyebrow">SKILL PROMOTION ELIGIBILITY</div><h2>{promotionInfo.name} ({promotionInfo.lifecycle})</h2></div>
        <button className="icon-button" onClick={() => setPromotionInfo(null)}><X size={15} /></button>
      </div>
      <p style={{ fontSize: '11px', color: '#556554', margin: '8px 0' }}>{promotionInfo.promotion_criteria}</p>
      <div style={{ display: 'flex', gap: '16px', margin: '10px 0', fontSize: '11px' }}>
        <div>Total Runs: <b>{promotionInfo.total_runs}</b></div>
        <div>Successes: <b>{promotionInfo.successes}</b> ({Math.round(promotionInfo.success_rate * 100)}%)</div>
        <div>Wilson 95% Bound: <b>{promotionInfo.wilson_lower_95 !== null ? promotionInfo.wilson_lower_95 : 'N/A'}</b></div>
      </div>
      <div style={{ display: 'flex', gap: '10px', alignItems: 'center', marginTop: '12px' }}>
        {promotionInfo.eligible_for_promotion && promotionInfo.lifecycle !== 'published' ? (
          <button className="button button-primary" onClick={() => promoteSkill(promotionInfo.workflow_id)}><Sparkles size={13} /> Promote to Published Skill</button>
        ) : (
          <span style={{ fontSize: '11px', color: '#7a8a79' }}>{promotionInfo.lifecycle === 'published' ? 'Skill is already published.' : 'More verified runs needed to reach confidence threshold.'}</span>
        )}
      </div>
    </section>}

    {runPreview && <section className="panel workflow-run-preview">
      <div className="panel-head"><div><div className="eyebrow">SIMULATION · NO TOOLS HAVE RUN</div><h2>Review the steps before execution.</h2></div><span className="local-tag"><ShieldCheck size={13} /> {runPreview.plan.requires_approval ? 'Approval required' : 'Read only'}</span></div>
      <div className="workflow-step-list">
        {runPreview.plan.would_execute.map((step, i) => (
          <div className="workflow-step" key={step.node_id}>
            <span>{String(i + 1).padStart(2, '0')}</span>
            <div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                <strong>{step.tool || step.type}</strong>
                {step.type && step.type !== 'tool' && <span style={{ padding: '1px 6px', borderRadius: '4px', background: step.type === 'map' ? '#efe5fd' : step.type === 'branch' ? '#fdf0e2' : step.type === 'verify' ? '#e2f7e7' : '#e6edf9', color: step.type === 'map' ? '#6b21a8' : step.type === 'branch' ? '#c2410c' : step.type === 'verify' ? '#15803d' : '#1d4ed8', fontSize: '8px', fontWeight: 600 }}>{step.type.toUpperCase()}</span>}
              </div>
              <small>{step.side_effects} · {step.risk || 'guarded'} · egress {step.data_egress || 'none'}{step.over ? ` · over ${step.over}` : ''}{step.condition ? ` · if ${step.condition}` : ''}{step.autonomy_policy ? ` · ${step.autonomy_policy.global_enabled ? `L${step.autonomy_policy.level} ${step.autonomy_policy.shadow_mode ? 'shadow' : step.autonomy_policy.level >= 2 ? 'auto eligible' : 'ask'}` : 'automation paused'} · cap ${step.autonomy_policy.daily_cap}/day` : ''}</small>
            </div>
            <Check size={15} />
          </div>
        ))}
      </div>
      <div className="workflow-form-footer"><span>Local writes use Threadline's permissions, quiet-hours rules, caps, and undo controls. Drafts remain unsent.</span><button className="button button-primary" disabled={busy === 'run'} onClick={execute}>{busy === 'run' ? <LoaderCircle size={14} className="spin" /> : <Play size={14} />} Approve and run</button></div>
    </section>}

    {runReceipt && <section className="panel workflow-run-receipt">
      <div className="panel-head">
        <div>
          <div className="eyebrow">DURABLE RUN RECEIPT</div>
          <h2>{runReceipt.workflow_id} · {runReceipt.status}</h2>
        </div>
        <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
          {runReceipt.repair_attempts > 0 && <span style={{ padding: '2px 8px', borderRadius: '4px', background: '#e2effd', color: '#1e40af', fontSize: '9px', fontWeight: 600 }}>Repaired ({runReceipt.repair_attempts}/2)</span>}
          {runReceipt.compensation_status && <span style={{ padding: '2px 8px', borderRadius: '4px', background: '#fef3c7', color: '#92400e', fontSize: '9px', fontWeight: 600 }}>{runReceipt.compensation_status}</span>}
          <span className="local-tag"><Check size={13} /> Checkpointed</span>
        </div>
      </div>
      <pre>{JSON.stringify({ run_id: runReceipt.id, status: runReceipt.status, repair_attempts: runReceipt.repair_attempts, nodes: runReceipt.nodes, outputs: runReceipt.outputs, error: runReceipt.error }, null, 2)}</pre>
      <div style={{ display: 'flex', gap: '8px', marginTop: '12px' }}>
        {runReceipt.status === 'failed' && (runReceipt.repair_attempts || 0) < 2 && (
          <button className="button button-primary" disabled={busy === 'repair'} onClick={() => repairRun(runReceipt.id)}>
            {busy === 'repair' ? <LoaderCircle size={14} className="spin" /> : <RefreshCw size={14} />} Auto-repair failing node
          </button>
        )}
        <button className="button button-soft" disabled={busy === 'rollback'} onClick={() => rollbackRun(runReceipt.id)}>
          {busy === 'rollback' ? <LoaderCircle size={14} className="spin" /> : <RotateCcw size={14} />} Rollback side effects
        </button>
      </div>
    </section>}
  </div>;
}
