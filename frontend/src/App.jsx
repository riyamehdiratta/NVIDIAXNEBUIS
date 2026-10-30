import { Activity, ArrowDownRight, ArrowRight, ArrowUpRight, ArrowUpRightFromSquare, Bell, BookOpenText, Check, CheckCheck, ChevronDown, ChevronRight, CircleHelp, Clock3, Cpu, Download, FileClock, FilePlus2, FileText, Fingerprint, GitBranch, Inbox, KeyRound, LayoutDashboard, LoaderCircle, LockKeyhole, Mail, Menu, MessageSquareText, MoreHorizontal, Plus, Search, Settings2, ShieldAlert, ShieldCheck, Sparkles, Upload, WandSparkles, X } from 'lucide-react';
import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { api, post, put } from './api';
import { ImportDialog } from './components/ImportDialog';
import { LiveAssistant, LiveAssistantTrigger } from './components/LiveAssistant';
import { LoopCard } from './components/LoopCard';
import { SovereignHub } from './components/SovereignHub';
import { WorkflowLab } from './components/WorkflowLab';

const nav = [
  { id: 'today', label: 'Today', icon: LayoutDashboard },
  { id: 'live', label: 'Live Assistant', icon: Sparkles, badge: 'LIVE VOICE' },
  { id: 'delegate', label: 'Sovereign OS (AGI)', icon: Cpu, badge: '5 PILLARS' },
  { id: 'workflows', label: 'Agent workflows', icon: GitBranch },
  { id: 'loops', label: 'Open loops', icon: Inbox },
  { id: 'skills', label: 'Skills', icon: WandSparkles },
  { id: 'permissions', label: 'Permissions', icon: ShieldCheck },
  { id: 'commitments', label: 'Precommitments', icon: LockKeyhole },
  { id: 'scam', label: 'Scam check', icon: ShieldAlert },
];
const auxNav = [
  { id: 'sources', label: 'Your sources', icon: FileText },
  { id: 'privacy', label: 'Privacy & activity', icon: Fingerprint },
];
const loopFilters = [['all', 'Everything'], ['task', 'To do'], ['promise', 'Promised'], ['waiting_on_them', 'Waiting on'], ['appointment', 'Events']];
const categoryNames = { task: 'To do', promise: 'You promised', waiting_on_them: 'Waiting on', appointment: 'On your calendar' };

function dateLabel(date = new Date()) { return date.toLocaleDateString(undefined, { weekday: 'long', month: 'long', day: 'numeric' }); }
function shortDate(value) { if (!value) return 'No date yet'; const d = new Date(`${value.slice(0, 10)}T00:00:00`); return d.toLocaleDateString(undefined, { month: 'short', day: 'numeric' }); }
function timeAgo(value) {
  const diff = Math.max(0, Date.now() - new Date(value).getTime());
  const minutes = Math.floor(diff / 60000);
  if (minutes < 1) return 'just now'; if (minutes < 60) return `${minutes}m ago`;
  const hours = Math.floor(minutes / 60); if (hours < 24) return `${hours}h ago`;
  const days = Math.floor(hours / 24); return `${days}d ago`;
}

function useWorkspace() {
  const [data, setData] = useState({ dashboard: null, loops: [], sources: [], skills: [], policies: [], actions: [], egress: [], egressSummary: null, reminders: [], health: null, autonomy: { enabled: true }, family: [], scamChecks: [], contracts: [] });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const refresh = useCallback(async (quiet = false) => {
    if (!quiet) setLoading(true);
    try {
      const [dashboard, loops, sources, skills, policies, actions, egress, egressSummary, reminders, health, autonomy, family, scamChecks, contracts] = await Promise.all([
        api('/dashboard'), api('/loops?status=all'), api('/sources'), api('/skills'), api('/policies'), api('/actions'), api('/egress'), api('/egress/summary'), api('/reminders'), api('/health'), api('/autonomy'), api('/family'), api('/scam/checks'), api('/contracts'),
      ]);
      setData({ dashboard, loops, sources, skills, policies, actions, egress, egressSummary, reminders, health, autonomy, family, scamChecks, contracts });
      setError('');
    } catch (e) { setError(e.message); }
    finally { setLoading(false); }
  }, []);
  useEffect(() => { refresh(); const id = setInterval(() => { if (!document.hidden) refresh(true); }, 15000); return () => clearInterval(id); }, [refresh]);
  return { ...data, loading, error, refresh };
}

function App() {
  const workspace = useWorkspace();
  const { dashboard, loops, sources, skills, policies, actions, egress, egressSummary, reminders, health, autonomy, family, scamChecks, contracts } = workspace;
  const [view, setView] = useState('today');
  const [showLiveAssistant, setShowLiveAssistant] = useState(false);
  const [showImport, setShowImport] = useState(false);
  const [preview, setPreview] = useState(null);
  const [busy, setBusy] = useState('');
  const [toast, setToast] = useState('');
  const [query, setQuery] = useState('');
  const [filter, setFilter] = useState('all');
  const [mobileMenu, setMobileMenu] = useState(false);
  const [expandedEgress, setExpandedEgress] = useState(null);
  const [weekSimulation, setWeekSimulation] = useState(null);
  const [simulationBusy, setSimulationBusy] = useState(false);
  const [localTime, setLocalTime] = useState(new Date());

  useEffect(() => { const id = setInterval(() => setLocalTime(new Date()), 60000); return () => clearInterval(id); }, []);
  useEffect(() => { if (!toast) return; const id = setTimeout(() => setToast(''), 3500); return () => clearTimeout(id); }, [toast]);

  const openImport = () => {
    if (health?.demo_mode) { setToast('This hosted demo accepts synthetic sample data only.'); return; }
    setShowImport(true);
  };

  const openLoops = useMemo(() => loops.filter(x => x.status === 'open'), [loops]);
  const visibleLoops = useMemo(() => openLoops.filter(x => (filter === 'all' || x.kind === filter) && (!query || `${x.title} ${x.detail} ${x.source_title || ''}`.toLowerCase().includes(query.toLowerCase()))), [openLoops, filter, query]);
  const unscanned = sources.filter(s => !s.scanned);
  const pendingActions = actions.filter(a => a.status === 'pending');
  const todayName = new Date().getHours() < 12 ? 'Good morning' : new Date().getHours() < 18 ? 'Good afternoon' : 'Good evening';

  const runPreview = async (skillId = 'commitment-scan', sourceIds = []) => {
    setBusy('preview');
    try { setPreview(await post('/scan/preview', { skill_id: skillId, source_ids: sourceIds })); }
    catch (e) { setToast(e.message); }
    finally { setBusy(''); }
  };

  const runScan = async (allowRemote) => {
    if (!preview) return;
    setBusy(allowRemote ? 'remote' : 'local');
    try {
      const result = await post('/scan', { source_ids: preview.source_ids, skill_id: preview.skill_id || 'commitment-scan', allow_remote: allowRemote, preview_id: allowRemote ? preview.preview_id : null });
      setPreview(null);
      await workspace.refresh(true);
      setToast(`${result.added} open loop${result.added === 1 ? '' : 's'} added · ${result.mode}`);
    } catch (e) { if (allowRemote) setPreview(null); setToast(e.message); }
    finally { setBusy(''); }
  };

  const addText = async text => {
    try { await post('/sources/text', { text, filename: 'Pasted note.txt' }); setShowImport(false); await workspace.refresh(true); setToast('Added to your local workspace'); }
    catch (e) { setToast(e.message); }
  };
  const addFiles = async files => {
    setBusy('import');
    let count = 0;
    try {
      for (const file of files) { const form = new FormData(); form.append('file', file); await api('/sources', { method: 'POST', body: form }); count++; }
      setShowImport(false); await workspace.refresh(true); setToast(`${count} source${count === 1 ? '' : 's'} added to this device`);
    } catch (e) { setToast(e.message); }
    finally { setBusy(''); }
  };

  const finishLoop = async item => {
    try { await post(`/loops/${item.id}/decision`, { decision: 'done' }); await workspace.refresh(true); setToast('Closed the loop'); }
    catch (e) { setToast(e.message); }
  };

  const propose = async (item, actionType) => {
    let title = item.title;
    let payload = { due_at: item.due_at, description: item.detail };
    if (actionType === 'draft_reply') payload.draft = `Hi,\n\nFollowing up on ${item.title.toLowerCase()}.\n\nThanks`;
    try {
      const result = await post('/actions', { loop_id: item.id, action_type: actionType, title, payload });
      await workspace.refresh(true);
      if (result.result?.content) downloadText(result.result.filename || 'threadline.ics', result.result.content, 'text/calendar');
      setToast(result.status === 'completed' ? result.result?.message || 'Saved locally' : 'Ready for your review in Permissions');
    } catch (e) { setToast(e.message); }
  };

  const decideAction = async (item, decision) => {
    try {
      let result;
      try { result = await post(`/actions/${item.id}/decision`, { decision }); }
      catch (e) {
        if (decision !== 'approve' || !e.message.toLowerCase().includes('precommitment')) throw e;
        const reason = window.prompt(`${e.message}\n\nType at least 20 characters explaining why you want to override this commitment.`);
        if (!reason || reason.trim().length < 20) { setToast('Override cancelled; the precommitment is still active'); return; }
        result = await post(`/actions/${item.id}/decision`, { decision, override_reason: reason.trim() });
      }
      await workspace.refresh(true);
      if (result.result?.draft) setToast('Draft is ready. Open the action details to copy it.');
      else setToast(result.promotion_suggested ? 'Shadow agreement supports raising this action level; you decide.' : decision === 'approve' ? 'Approved and completed locally' : 'Action rejected');
      if (result.result?.content) downloadText(result.result.filename || 'threadline.ics', result.result.content, 'text/calendar');
    } catch (e) { setToast(e.message); }
  };

  const loadDemo = async () => {
    setBusy('demo');
    try { await post('/demo/load'); await workspace.refresh(true); setToast('Synthetic workspace loaded. Scan locally or send a minimized preview to Nemotron.'); }
    catch (e) { setToast(e.message); }
    finally { setBusy(''); }
  };

  const runWeekSimulation = async () => {
    setSimulationBusy(true);
    try { setWeekSimulation(await post('/demo/simulated-week')); }
    catch (e) { setToast(e.message); }
    finally { setSimulationBusy(false); }
  };

  const changePolicy = async (p, patch) => {
    if (patch.autonomy_level >= 2 && patch.autonomy_level > p.autonomy_level && !window.confirm(`Allow Threadline to run ${p.label.toLowerCase()} automatically on this device with a 10-minute undo window?`)) return;
    try { await put(`/policies/${p.action_type}`, patch); await workspace.refresh(true); setToast(`Policy updated · ${p.label}`); }
    catch (e) { setToast(e.message); }
  };

  const setGlobalAutonomy = async enabled => {
    try { await put('/autonomy', { enabled }); await workspace.refresh(true); setToast(enabled ? 'Local autonomy resumed' : 'Global pause is on · autonomous actions stopped'); }
    catch (e) { setToast(e.message); }
  };

  const undoAction = async action => {
    if (!window.confirm(`Undo “${action.title}” locally? Its autonomy level will drop by one.`)) return;
    try { const result = await post(`/actions/${action.id}/undo`); await workspace.refresh(true); setToast(`Undone · autonomy lowered to L${result.autonomy_level}`); }
    catch (e) { setToast(e.message); }
  };

  const inspectScam = async message => {
    try { const result = await post('/scam/check', { message }); await workspace.refresh(true); setToast(`Local check complete · ${result.signals.length} signal${result.signals.length === 1 ? '' : 's'}`); return result; }
    catch (e) { setToast(e.message); return null; }
  };

  const saveFamily = async profile => {
    try { await post('/family', profile); await workspace.refresh(true); setToast('Verification profile saved locally. Share the phrase through a trusted channel.'); return true; }
    catch (e) { setToast(e.message); return false; }
  };

  const verifyFamily = async (memberId, phrase) => {
    try { return await post('/family/verify', { member_id: memberId, verification_phrase: phrase }); }
    catch (e) { setToast(e.message); return null; }
  };

  const removeFamily = async member => {
    if (!window.confirm(`Delete the local verification profile for ${member.display_name}?`)) return;
    try { await api(`/family/${member.id}`, { method: 'DELETE' }); await workspace.refresh(true); setToast('Verification profile deleted'); }
    catch (e) { setToast(e.message); }
  };

  const removeScamCheck = async check => {
    try { await api(`/scam/checks/${check.id}`, { method: 'DELETE' }); await workspace.refresh(true); setToast('Local check receipt deleted'); }
    catch (e) { setToast(e.message); }
  };

  const saveContract = async contract => {
    try { await post('/contracts', contract); await workspace.refresh(true); setToast('Precommitment compiled and saved locally'); return true; }
    catch (e) { setToast(e.message); return false; }
  };

  const removeContract = async contract => {
    if (!window.confirm(`Remove the precommitment “${contract.title}”?`)) return;
    try { await api(`/contracts/${contract.id}`, { method: 'DELETE' }); await workspace.refresh(true); setToast('Precommitment removed'); }
    catch (e) { setToast(e.message); }
  };

  const removeSource = async source => {
    if (!window.confirm(`Delete "${source.filename}" and the open loops extracted from it?`)) return;
    try { await api(`/sources/${source.id}`, { method: 'DELETE' }); await workspace.refresh(true); setToast('Source and derived memory deleted'); }
    catch (e) { setToast(e.message); }
  };

  const exportWorkspace = async () => {
    try { const data = await api('/export'); downloadText('threadline-export.json', JSON.stringify(data, null, 2), 'application/json'); setToast('Workspace exported'); }
    catch (e) { setToast(e.message); }
  };

  const shownTitle = { today: 'Your day, unknotted.', delegate: 'The Sovereign Delegate · AGI Operating System', loops: 'Nothing slips the thread.', skills: 'Make the routine reusable.', workflows: 'Give a task its own workflow.', permissions: 'You set the boundaries.', commitments: 'Your rules, before the moment.', scam: 'Pause. Verify. Then decide.', sources: 'Your information, your call.', privacy: 'See what leaves. See what changes.' }[view];
  const shownSubtitle = { today: "A clear view of what's next, what's waiting, and what you said you'd do.", delegate: 'Universal OS perception across all native apps, provable conformal risk control (α ≤ 0.02), online Bayesian preference model, autonomous tool synthesis, and 7-day causal horizon rehearsals.', loops: 'A living memory of commitments, each tied back to where it came from.', skills: 'Give Threadline a repeatable way to handle the things you do all the time.', workflows: 'Describe a task. Review the generated plan. Approve each local run.', permissions: 'Threadline earns a recommendation. You decide when it gets more room to act.', commitments: 'Compile a plain-language boundary into a rule checked by the action API.', scam: 'Check pressure tactics locally and verify a familiar voice with a private phrase.', sources: 'Choose what Threadline can remember by bringing it here.', privacy: 'Your sources stay on this device. Every model request has a receipt.' }[view];

  return <div className="app-shell">
    <aside className={`sidebar ${mobileMenu ? 'mobile-open' : ''}`}>
      <div className="brand-row"><div className="brand-mark"><span /><span /><span /></div><div className="brand-name">threadline<span>PERSONAL AI</span></div><button className="mobile-close" onClick={() => setMobileMenu(false)}><X size={17} /></button></div>
      <div className="workspace-selector"><div className="avatar">Y</div><div className="workspace-name"><strong>Your workspace</strong><span>Private · this device</span></div><ChevronDown size={15} className="muted-icon" /></div>
      <div className="sidebar-label">WORKSPACE</div>
      <nav className="nav-list">{nav.map(({ id, label, icon: Icon, badge }) => <button key={id} className={`nav-item ${view === id ? 'active' : ''}`} onClick={() => { if (id === 'live') { setShowLiveAssistant(true); } else { setView(id); } setMobileMenu(false); }}><Icon size={17} strokeWidth={1.8} /><span>{label}</span>{badge && <b className="nav-count" style={{ background: id === 'live' ? '#2f603c' : '#2f5b3a', color: id === 'live' ? '#c2f296' : '#bce481', fontSize: '8px' }}>{badge}</b>}{id === 'permissions' && pendingActions.length > 0 && <b className="nav-count">{pendingActions.length}</b>}</button>)}</nav>
      <div className="sidebar-label secondary-label">CONTROL & CONTEXT</div>
      <nav className="nav-list">{auxNav.map(({ id, label, icon: Icon }) => <button key={id} className={`nav-item ${view === id ? 'active' : ''}`} onClick={() => { setView(id); setMobileMenu(false); }}><Icon size={17} strokeWidth={1.8} /><span>{label}</span>{id === 'sources' && sources.length > 0 && <b className="nav-count muted-count">{sources.length}</b>}</button>)}</nav>
      <div className="sidebar-bottom">
        <div className="runtime-card"><span className={`runtime-dot ${health?.api_key_configured ? 'connected' : ''}`} /><div><strong>{health?.api_key_configured ? 'Nemotron ready' : 'Private mode'}</strong><span>{health?.api_key_configured ? 'Token Factory connected' : 'Local memory is active'}</span></div><ChevronRight size={14} /></div>
        <div className="profile-row"><div className="profile-avatar">Y</div><div><strong>Your profile</strong><small>Personal workspace</small></div><MoreHorizontal size={18} /></div>
      </div>
    </aside>
    {mobileMenu && <div className="mobile-scrim" onClick={() => setMobileMenu(false)} />}
    <main className="main-area">
      <header className="topbar"><div className="topbar-left"><button className="mobile-menu-button icon-button" onClick={() => setMobileMenu(true)}><Menu size={19} /></button><div className="breadcrumbs"><span>Workspace</span><ChevronRight size={13} /><strong>{nav.concat(auxNav).find(n => n.id === view)?.label || 'Today'}</strong></div></div><div className="topbar-right"><LiveAssistantTrigger onClick={() => setShowLiveAssistant(true)} isActive={showLiveAssistant} /><span className="sync-label"><span className="sync-dot" /> Saved locally</span><button className="icon-button help-button" title="About Threadline" onClick={() => setToast('A personal memory with receipts. Always yours, always reviewable.')}><CircleHelp size={17} /></button><div className="top-avatar">Y</div></div></header>
      <div className="page-wrap">
        {workspace.error && <div className="error-banner">{workspace.error} <button onClick={() => workspace.refresh()}>Retry</button></div>}
        <div className="page-heading"><div><div className="eyebrow">{view === 'today' ? dateLabel(localTime).toUpperCase() : 'THREADLINE WORKSPACE'}</div><h1>{shownTitle}</h1><p>{shownSubtitle}</p></div><div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}><LiveAssistantTrigger onClick={() => setShowLiveAssistant(true)} isActive={showLiveAssistant} /><button className="button button-primary add-button" onClick={openImport}><Plus size={16} /> {health?.demo_mode ? 'Synthetic demo mode' : 'Capture something'}</button></div></div>
        {view === 'today' && <TodayView dashboard={dashboard} loops={openLoops} sources={sources} health={health} loading={workspace.loading} onPreview={runPreview} onImport={openImport} onDemo={loadDemo} busy={busy} onDone={finishLoop} onReminder={x => propose(x, 'create_reminder')} onDraft={x => propose(x, 'draft_reply')} onCalendar={x => propose(x, 'calendar_export')} onNavigate={setView} />}
        {view === 'delegate' && <SovereignHub setToast={setToast} />}
        {view === 'loops' && <LoopsView loops={visibleLoops} filter={filter} setFilter={setFilter} query={query} setQuery={setQuery} onDone={finishLoop} onReminder={x => propose(x, 'create_reminder')} onDraft={x => propose(x, 'draft_reply')} onCalendar={x => propose(x, 'calendar_export')} />}
        {view === 'skills' && <SkillsView skills={skills} refresh={workspace.refresh} setToast={setToast} onRun={skill => runPreview(skill.id, sources.map(s => s.id))} hasSources={sources.length > 0} />}
        {view === 'workflows' && <WorkflowLab apiKeyConfigured={health?.api_key_configured} demoMode={health?.demo_mode} setToast={setToast} />}
        {view === 'permissions' && <PermissionsView policies={policies} actions={actions} autonomy={autonomy} onPolicy={changePolicy} onDecision={decideAction} onUndo={undoAction} onGlobalPause={setGlobalAutonomy} simulation={weekSimulation} simulationBusy={simulationBusy} onSimulateWeek={runWeekSimulation} />}
        {view === 'commitments' && <ContractsView contracts={contracts} onSave={saveContract} onRemove={removeContract} />}
        {view === 'scam' && <ScamView checks={scamChecks} family={family} onCheck={inspectScam} onSaveFamily={saveFamily} onVerify={verifyFamily} onRemoveFamily={removeFamily} onRemoveCheck={removeScamCheck} />}
        {view === 'sources' && <SourcesView sources={sources} importDir={health?.import_dir} onImport={openImport} onRemove={removeSource} onPreview={runPreview} onDemo={loadDemo} busy={busy} />}
        {view === 'privacy' && <PrivacyView health={health} events={egress} summary={egressSummary} expanded={expandedEgress} setExpanded={setExpandedEgress} onExport={exportWorkspace} />}
        <footer className="page-footer"><span>THREADLINE <b>·</b> YOUR MEMORY, WITH RECEIPTS</span><span>Local workspace <i>•</i> {sources.length} source{sources.length === 1 ? '' : 's'} remembered</span></footer>
      </div>
    </main>
    {showImport && !health?.demo_mode && <ImportDialog onClose={() => setShowImport(false)} onText={addText} onFiles={addFiles} />}
    {preview && <ScanDialog preview={preview} busy={busy} onClose={() => setPreview(null)} onLocal={() => runScan(false)} onRemote={() => runScan(true)} />}
    <LiveAssistant isOpen={showLiveAssistant} onClose={() => setShowLiveAssistant(false)} setToast={setToast} />
    {toast && <div className="toast"><span className="toast-mark"><Check size={14} /></span>{toast}<button onClick={() => setToast('')}><X size={14} /></button></div>}
  </div>;
}

function TodayView({ dashboard, loops, sources, health, loading, onPreview, onImport, onDemo, busy, onDone, onReminder, onDraft, onCalendar, onNavigate }) {
  const priorities = [...loops].sort((a, b) => {
    if (a.due_at && b.due_at) return a.due_at.localeCompare(b.due_at);
    if (a.due_at) return -1; if (b.due_at) return 1;
    return b.confidence - a.confidence;
  }).slice(0, 3);
  const dueSoon = loops.filter(l => l.due_at && l.due_at <= new Date(Date.now() + 3 * 86400000).toISOString().slice(0, 10)).length;
  return <>
    <section className="stats-grid">
      <StatCard label="Open loops" value={dashboard?.open_loops ?? '-'} note="Things worth keeping in view" icon={Inbox} accent="green" />
      <StatCard label="Due soon" value={dueSoon} note="In the next three days" icon={Clock3} accent="amber" />
      <StatCard label="Waiting on" value={dashboard?.waiting_on_them ?? '-'} note="You're waiting for a reply" icon={ArrowDownRight} accent="blue" />
      <StatCard label="Needs your review" value={dashboard?.pending_actions ?? '-'} note="Nothing happens without you" icon={ShieldCheck} accent="violet" />
    </section>
    <div className="dashboard-grid">
      <section className="panel loops-panel">
        <div className="panel-head"><div><div className="eyebrow">THE THINGS THAT MATTER</div><h2>Keep these in view <span className="small-count">{loops.length}</span></h2></div><button className="text-button" onClick={() => onNavigate('loops')}>All open loops <ArrowRight size={14} /></button></div>
        {loading ? <div className="empty-state"><LoaderCircle className="spin" /> Loading your workspace...</div> : priorities.length ? <div className="loop-list">{priorities.map(item => <LoopCard key={item.id} item={item} onDone={onDone} onReminder={onReminder} onDraft={onDraft} onCalendar={onCalendar} />)}</div> : <EmptyLoops onImport={onImport} onDemo={onDemo} busy={busy} />}
        {loops.length > 3 && <button className="panel-bottom-link" onClick={() => onNavigate('loops')}>See all {loops.length} open loops <ArrowRight size={14} /></button>}
      </section>
      <section className="right-stack">
        <div className="daily-card">
          <div className="daily-top"><div className="daily-icon"><Sparkles size={17} /></div><span className="eyebrow">YOUR DAILY RESET</span><span className="daily-live"><i /> READY</span></div>
          <h2>Make room for what's next.</h2>
          <p>Threadline sorts your open loops into a short, source-linked plan. No background messages. Just a clearer next step.</p>
          <button className="button button-dark" onClick={() => onPreview('daily-reset')} disabled={!sources.some(s => !s.scanned) || busy === 'preview'}>{busy === 'preview' ? <LoaderCircle size={15} className="spin" /> : <Sparkles size={15} />}{sources.some(s => !s.scanned) ? 'Review new information' : 'You\'re up to date'}</button>
          <div className="daily-foot"><span><ShieldCheck size={13} /> Approvals follow your per-action policy</span><span>Takes about a minute</span></div>
        </div>
        <div className="privacy-card"><div className="privacy-card-head"><div className="privacy-icon"><LockKeyhole size={16} /></div><div><strong>Your data stays yours</strong><span>Memory is stored on this device</span></div><span className="privacy-status">LOCAL</span></div><div className="privacy-lines"><span><i className="line-local" /> Files & memory <b>On device</b></span><span><i className={`line-model ${health?.api_key_configured ? 'online' : ''}`} /> Model requests <b>{health?.api_key_configured ? 'Preview first' : 'Not connected'}</b></span></div><button onClick={() => onNavigate('privacy')} className="privacy-link">See your data activity <ArrowRight size={13} /></button></div>
        <div className="tip-card"><div className="tip-spark"><Sparkles size={13} /></div><div><span className="eyebrow">THE THREADLINE IDEA</span><p>Every useful action begins with a memory you can inspect-and ends with a receipt you can trust.</p></div></div>
      </section>
    </div>
    {dashboard?.activity?.length > 0 && <ActivityStrip items={dashboard.activity.slice(0, 5)} />}
  </>;
}

function StatCard({ label, value, note, icon: Icon, accent }) {
  return <div className="stat-card"><div className={`stat-icon ${accent}`}><Icon size={16} strokeWidth={1.9} /></div><div className="stat-label">{label}</div><div className="stat-value">{value}</div><div className="stat-note">{note}</div></div>;
}

function EmptyLoops({ onImport, onDemo, busy }) {
  return <div className="empty-state empty-loops"><div className="empty-illustration"><span className="empty-orbit orbit-one" /><span className="empty-orbit orbit-two" /><span className="empty-spark"><Sparkles size={22} /></span></div><h3>Your first thread starts here.</h3><p>Bring in a note, email, or calendar file. Threadline will pull out the promises and follow-ups worth remembering.</p><div className="empty-actions"><button className="button button-primary" onClick={onImport}><Plus size={15} /> Capture a source</button><button className="button button-ghost" disabled={busy === 'demo'} onClick={onDemo}>Try the sample workspace <ArrowRight size={14} /></button></div></div>;
}

function ActivityStrip({ items }) {
  return <section className="activity-strip"><div className="activity-heading"><Activity size={15} /><span>RECENT ACTIVITY</span></div><div className="activity-items">{items.slice(0, 4).map(item => <div className="activity-item" key={item.id}><span className="activity-dot" /><span>{item.detail}</span><time>{timeAgo(item.created_at)}</time></div>)}</div></section>;
}

function LoopsView({ loops, filter, setFilter, query, setQuery, onDone, onReminder, onDraft, onCalendar }) {
  return <section className="panel memory-panel"><div className="memory-toolbar"><div className="filter-tabs">{loopFilters.map(([id, label]) => <button key={id} className={`filter-tab ${filter === id ? 'selected' : ''}`} onClick={() => setFilter(id)}>{label}{id === 'all' && <span>{loops.length}</span>}</button>)}</div><label className="search-box"><Search size={15} /><input placeholder="Search your memory" value={query} onChange={e => setQuery(e.target.value)} /><kbd>Ctrl K</kbd></label></div>
    {loops.length ? <div className="loop-list memory-list">{loops.map(item => <LoopCard key={item.id} item={item} onDone={onDone} onReminder={onReminder} onDraft={onDraft} onCalendar={onCalendar} />)}</div> : <div className="empty-state compact-empty"><div className="empty-spark"><Inbox size={20} /></div><h3>No threads match.</h3><p>Try a different search or bring in a new source.</p></div>}
    </section>;
}

function SkillsView({ skills, refresh, setToast, onRun, hasSources }) {
  const [editing, setEditing] = useState(null);
  const [draft, setDraft] = useState({});
  const editSkill = skill => { setEditing(skill.id); setDraft({ name: skill.name, description: skill.description, instructions: skill.instructions, enabled: Boolean(skill.enabled) }); };
  const save = async id => {
    try { await put(`/skills/${id}`, draft); setEditing(null); await refresh(true); setToast('Skill updated and saved locally'); }
    catch (e) { setToast(e.message); }
  };
  return <div className="skills-layout"><section className="panel skills-panel"><div className="panel-head"><div><div className="eyebrow">REUSABLE PLAYBOOKS</div><h2>Your skills</h2></div><span className="local-tag"><BookOpenText size={13} /> Editable by you</span></div><p className="section-intro">Skills are instructions you can inspect, edit, and run again. They never get new permissions just because they run.</p>
    {skills.map((skill, i) => <div className={`skill-row ${editing === skill.id ? 'is-editing' : ''}`} key={skill.id}><div className={`skill-number n-${i}`}><span>0{i + 1}</span></div><div className="skill-content">{editing === skill.id ? <><div className="skill-fields"><label>Name<input value={draft.name} onChange={e => setDraft({ ...draft, name: e.target.value })} /></label><label>Description<input value={draft.description} onChange={e => setDraft({ ...draft, description: e.target.value })} /></label></div><label className="instructions-label">INSTRUCTIONS<textarea value={draft.instructions} onChange={e => setDraft({ ...draft, instructions: e.target.value })} rows={5} /></label><div className="skill-edit-actions"><label className="mini-toggle-label"><input type="checkbox" checked={draft.enabled} onChange={e => setDraft({ ...draft, enabled: e.target.checked })} /> Enabled</label><button className="button button-soft" onClick={() => setEditing(null)}>Cancel</button><button className="button button-primary" onClick={() => save(skill.id)}>Save skill</button></div></> : <><div className="skill-title-row"><h3>{skill.name}</h3><span className={`skill-enabled ${skill.enabled ? '' : 'off'}`}>{skill.enabled ? 'ACTIVE' : 'PAUSED'}</span></div><p>{skill.description}</p><details className="skill-instructions"><summary>View instructions <ChevronDown size={13} /></summary><pre>{skill.instructions}</pre></details><div className="skill-meta"><span><FileText size={12} /> {skill.instructions.length} characters</span><span><Clock3 size={12} /> Edited {timeAgo(skill.updated_at)}</span></div><div className="skill-actions"><button className="edit-skill" onClick={() => editSkill(skill)}><Settings2 size={13} /> Edit skill</button><button className="edit-skill" disabled={!skill.enabled || !hasSources} onClick={() => onRun(skill)}><Sparkles size={13} /> Run on imported sources</button></div></>}</div></div>)}
    </section><aside className="skills-aside"><div className="skill-manifest"><div className="manifest-icon"><WandSparkles size={17} /></div><div className="eyebrow">SKILLS THAT STAY YOURS</div><h3>Teach once.<br />Use on your terms.</h3><p>Your skills are plain instructions, saved in your workspace. Read them, change them, or turn them off whenever you like.</p><div className="manifest-code"><span>threadline/skills/</span><b>daily-reset.md</b><b>commitment-scan.md</b><b>follow-up-draft.md</b></div></div><div className="skill-safety-note"><ShieldCheck size={15} /><span>A skill can suggest an action.<br /><b>Your policy decides if it can run.</b></span></div></aside></div>;
}

function PermissionsView({ policies, actions, autonomy, onPolicy, onDecision, onUndo, onGlobalPause, simulation, simulationBusy, onSimulateWeek }) {
  const pending = actions.filter(a => a.status === 'pending');
  const history = actions.filter(a => a.status !== 'pending').slice(0, 8);
  return <div className="permissions-layout"><div className="permissions-main">
    <section className={`panel autonomy-master ${autonomy?.enabled ? '' : 'paused'}`}><div><div className="eyebrow">GLOBAL KILL SWITCH</div><h2>{autonomy?.enabled ? 'Autonomy is available.' : 'Autonomy is paused.'}</h2><p>{autonomy?.enabled ? 'Only opted-in, reversible local actions can run automatically.' : 'Automatic actions are stopped across every life area. You can still review and approve queued actions.'}</p></div><button className={`button ${autonomy?.enabled ? 'button-soft' : 'button-primary'}`} onClick={() => onGlobalPause(!autonomy?.enabled)}>{autonomy?.enabled ? 'Pause all autonomy' : 'Resume autonomy'}</button></section>
    <section className="panel simulated-week"><div className="panel-head"><div><div className="eyebrow">DEMO REPLAY</div><h2>See earned autonomy over a simulated week.</h2></div><button className="button button-soft" disabled={simulationBusy} onClick={onSimulateWeek}>{simulationBusy ? 'Replaying...' : 'Run 7-day simulation'}</button></div><p className="section-intro">Replays 49 synthetic decisions through the same shadow baseline and Wilson confidence calculations. It does not change your real policies or action history.</p>{simulation && <><div className="simulation-badge">SIMULATED DATA - NOT YOUR HISTORY</div><div className="simulation-chart">{simulation.daily.map((day, index) => { const lower = day.wilson_lower_95 == null ? 0 : Math.round(day.wilson_lower_95 * 100); return <div className="simulation-day" key={day.day}><div className="simulation-bar-wrap"><div className={`simulation-bar ${day.promotion_suggested ? 'earned' : ''}`} style={{ height: `${Math.max(3, lower)}%` }} title={`${lower}% lower bound`} /></div><strong>{day.shadow_samples}</strong><small>{new Date(`${day.day}T12:00:00`).toLocaleDateString(undefined, { weekday: 'short' })}</small></div>; })}</div><div className="simulation-legend"><span>95% Wilson lower bound by day</span><span>{simulation.earned_example.agreements}/{simulation.earned_example.shadow_samples} agreements - suggestion threshold {Math.round(simulation.earned_example.promotion_target * 100)}%</span></div><div className="simulation-block"><LockKeyhole size={15} /><div><strong>Not earned: {simulation.unearned_example.action_type.replace('_', ' ')} stays approval-only.</strong><p>{simulation.unearned_example.blocked_reason} A promotion suggestion never changes the actual autonomy level.</p></div><b>L{simulation.unearned_example.configured_level}</b></div></>}{!simulation && <div className="quiet-empty"><span className="quiet-check"><Activity size={16} /></span><div><strong>Preview a week of evidence.</strong><p>The replay is disposable synthetic data; no workspace records are written.</p></div></div>}</section>
    <section className="panel permission-panel"><div className="panel-head"><div><div className="eyebrow">EARNED AUTONOMY ? PER ACTION TYPE</div><h2>Trust with measurable evidence.</h2></div><span className="local-tag"><ShieldCheck size={13} /> Local policy gate</span></div><p className="section-intro">Shadow mode privately predicts your likely choice, then scores the prediction when you decide. A statistical bound informs promotion; it never changes the level for you.</p>
      {policies.map(p => <PolicyControl key={p.action_type} policy={p} onChange={onPolicy} />)}
    </section>
    <section className="panel queued-actions"><div className="panel-head"><div><div className="eyebrow">ACTION QUEUE</div><h2>Ready for your call <span className="small-count">{pending.length}</span></h2></div></div>{pending.length ? pending.map(action => <ActionCard key={action.id} action={action} onDecision={onDecision} />) : <div className="quiet-empty"><span className="quiet-check"><CheckCheck size={17} /></span><div><strong>All clear.</strong><p>Actions Threadline suggests will wait here until you approve them.</p></div></div>}</section>
    {history.length > 0 && <section className="panel queued-actions"><div className="panel-head"><div><div className="eyebrow">ACTION RECEIPTS</div><h2>Completed and declined</h2></div></div>{history.map(action => <div className="action-history" key={action.id}><div className="action-history-head"><span><PolicyIcon type={action.action_type} /> {action.title}</span><b className={action.status}>{action.status}</b></div>{action.result?.message && <p className="action-result-note">{action.result.message}{action.execution_mode === 'autonomous' ? ` ? L${action.policy_level} automatic` : ''}</p>}{action.result?.draft && <div className="action-history-result"><pre>{action.result.draft}</pre><button className="button button-soft" onClick={() => navigator.clipboard?.writeText(action.result.draft)}>Copy draft</button></div>}{action.result?.content && <button className="button button-soft" onClick={() => downloadText(action.result.filename || 'threadline.ics', action.result.content, 'text/calendar')}>Download calendar file</button>}{action.undo_deadline && new Date(action.undo_deadline).getTime() > Date.now() && <button className="button button-soft undo-action" onClick={() => onUndo(action)}>Undo ? {Math.max(1, Math.ceil((new Date(action.undo_deadline).getTime() - Date.now()) / 60000))} min left</button>}</div>)}</section>}
    </div><aside className="permissions-aside"><div className="policy-explainer"><div className="eyebrow">THE FOUR CHECKS</div><div className="trust-steps"><div className="trust-step"><span className="step-no">01</span><div><strong>Observe first</strong><p>L0 is read-only; L1 asks you before every action.</p></div></div><div className="trust-step"><span className="step-no">02</span><div><strong>Shadow before promotion</strong><p>Predictions are scored only after you choose. The 95% Wilson lower bound avoids trusting a tiny sample.</p></div></div><div className="trust-step"><span className="step-no">03</span><div><strong>Undo and demote</strong><p>Automatic reminders and drafts have a ten-minute undo. Undo lowers that action type one level.</p></div></div><div className="trust-step"><span className="step-no">04</span><div><strong>Keep the blast radius small</strong><p>Daily caps are checked by the API. Non-reversible calendar exports stay approval-only.</p></div></div></div><div className="enforcement-badge"><LockKeyhole size={14} /><span>These controls govern local app tools. OpenShell enforcement is a separate deployment step.</span></div></div></aside></div>;
}

function PolicyControl({ policy: p, onChange }) {
  const [cap, setCap] = useState(p.max_actions_per_day);
  useEffect(() => setCap(p.max_actions_per_day), [p.max_actions_per_day]);
  const lower = p.wilson_lower_95 == null ? null : Math.round(p.wilson_lower_95 * 100);
  const accuracy = p.shadow_accuracy == null ? null : Math.round(p.shadow_accuracy * 100);
  return <div className="policy-control"><div className="policy-row"><div className="policy-icon"><PolicyIcon type={p.action_type} /></div><div className="policy-description"><strong>{p.label}</strong><span>{p.life_area} | {p.approved_count} approved | {p.rejected_count} declined</span>{p.promotion_suggested && <em>Statistical promotion threshold reached - your choice</em>}</div><label className="level-select">AUTONOMY<select value={p.autonomy_level} onChange={e => onChange(p, { autonomy_level: Number(e.target.value) })}><option value="0">L0 - Observe only</option><option value="1">L1 - Ask each time</option>{[2,3,4].map(level => <option key={level} value={level} disabled={!p.reversible}>L{level} - {level === 2 ? 'Undo window' : level === 3 ? 'Daily report' : 'Capped'}{!p.reversible ? ' - unavailable' : ''}</option>)}</select></label></div>
    <div className="policy-controls"><label className="mini-toggle-label shadow-toggle"><input type="checkbox" checked={Boolean(p.shadow_mode)} onChange={e => onChange(p, { shadow_mode: e.target.checked })} /> Shadow predictions</label><span className="shadow-stat">{p.shadow_samples ? `${accuracy}% agreement ? ${lower}% 95% lower bound` : 'No scored shadow predictions yet'}{p.samples_to_minimum ? ` ? ${p.samples_to_minimum} more to minimum` : ''}</span><label className="policy-setting">Life area<select value={p.life_area} onChange={e => onChange(p, { life_area: e.target.value })}><option value="work">Work</option><option value="money">Money</option><option value="family">Family</option><option value="health">Health</option><option value="personal">Personal</option></select></label><label className="policy-setting">Daily auto cap<input type="number" min="1" max="100" value={cap} onChange={e => setCap(e.target.value)} onBlur={() => { const value = Math.max(1, Math.min(100, Number(cap) || 1)); setCap(value); if (value !== p.max_actions_per_day) onChange(p, { max_actions_per_day: value }); }} /></label></div>
    {p.shadow_mode && <p className="shadow-note">Shadow mode keeps this action approval-only while it gathers comparison data. It does not auto-run.</p>}
  </div>;
}

function ContractsView({ contracts, onSave, onRemove }) {
  const [title, setTitle] = useState('Quiet hours');
  const [statement, setStatement] = useState('No automatic actions from 22:00 to 07:00.');
  const [scope, setScope] = useState('all_auto');
  const [saving, setSaving] = useState(false);
  const submit = async e => { e.preventDefault(); setSaving(true); const ok = await onSave({ title, statement, scope }); setSaving(false); if (ok) { setTitle('Quiet hours'); setStatement('No automatic actions from 22:00 to 07:00.'); } };
  return <div className="contracts-layout"><section className="panel contracts-panel"><div className="panel-head"><div><div className="eyebrow">PRECOMMITMENT COMPILER</div><h2>Decide your boundary ahead of time.</h2></div><span className="local-tag"><LockKeyhole size={13} /> Enforced by API</span></div><p className="section-intro">Write a clear quiet-hours rule. Threadline compiles it, checks boundary cases, then blocks matching automatic actions. During the window, manual approval needs a reason of at least 20 characters.</p>
    <form className="contract-form" onSubmit={submit}><label>Rule name<input value={title} onChange={e => setTitle(e.target.value)} required maxLength={100} /></label><label>Plain-language rule<textarea value={statement} onChange={e => setStatement(e.target.value)} rows={3} required maxLength={500} /></label><label>Applies to<select value={scope} onChange={e => setScope(e.target.value)}><option value="all_auto">All automatic local actions</option><option value="create_reminder">Create reminders</option><option value="draft_reply">Save reply drafts</option><option value="calendar_export">Calendar exports</option></select></label><div className="contract-hint">Supported format: “No automatic actions from 22:00 to 07:00.” Times use this host’s local clock.</div><button className="button button-primary" disabled={saving}>{saving ? 'Checking boundaries…' : 'Compile and save rule'}</button></form>
    </section><section className="panel contract-list"><div className="panel-head"><div><div className="eyebrow">ACTIVE RULES</div><h2>Your precommitments <span className="small-count">{contracts.length}</span></h2></div></div>{contracts.length ? contracts.map(rule => <article className="contract-card" key={rule.id}><div className="contract-card-head"><div><h3>{rule.title}</h3><span>{rule.scope_label} · {rule.start_time}–{rule.end_time}</span></div><button className="text-button" onClick={() => onRemove(rule)}>Remove</button></div><p>{rule.statement}</p><div className="contract-tests">{Object.entries(rule.red_team || {}).map(([key, result]) => <span key={key} className={result.blocked ? 'blocked' : 'allowed'}><Check size={12} /> {key.replaceAll('_', ' ')} · {result.time} · {result.blocked ? 'blocked' : 'allowed'}</span>)}</div></article>) : <div className="quiet-empty"><span className="quiet-check"><LockKeyhole size={16} /></span><div><strong>No precommitments yet.</strong><p>Add a rule to make your boundary part of the action gate.</p></div></div>}</section><aside className="policy-explainer contract-explainer"><div className="eyebrow">HOW IT HOLDS</div><div className="trust-steps"><div className="trust-step"><span className="step-no">01</span><div><strong>Plain language, bounded parser</strong><p>Supported quiet-hours statements become a narrow time rule. Unsupported wording is rejected.</p></div></div><div className="trust-step"><span className="step-no">02</span><div><strong>Checked at execution time</strong><p>The API rechecks the active local clock when an action is proposed and when you approve it.</p></div></div><div className="trust-step"><span className="step-no">03</span><div><strong>Override leaves a receipt</strong><p>An override requires a typed reason. This is a friction mechanism, not an unbreakable lock.</p></div></div></div></aside></div>;
}

function ScamView({ checks, family, onCheck, onSaveFamily, onVerify, onRemoveFamily, onRemoveCheck }) {
  const [message, setMessage] = useState('');
  const [result, setResult] = useState(null);
  const [name, setName] = useState('');
  const [relationship, setRelationship] = useState('family');
  const [newPhrase, setNewPhrase] = useState('');
  const [memberId, setMemberId] = useState('');
  const [phrase, setPhrase] = useState('');
  const [verification, setVerification] = useState(null);
  const submitCheck = async e => { e.preventDefault(); if (!message.trim()) return; const value = await onCheck(message); if (value) setResult(value); };
  const addProfile = async e => { e.preventDefault(); if (!name.trim() || !newPhrase) return; const ok = await onSaveFamily({ display_name: name, relationship, verification_phrase: newPhrase }); if (ok) { setName(''); setNewPhrase(''); } };
  const verify = async e => { e.preventDefault(); const selectedId = memberId || family[0]?.id; if (!selectedId || !phrase) return; const value = await onVerify(selectedId, phrase); setVerification(value); };
  return <div className="scam-layout"><div className="scam-main">
    <section className="panel scam-check-panel"><div className="panel-head"><div><div className="eyebrow">LOCAL SCAM TRIAGE</div><h2>Slow the pressure down.</h2></div><span className="local-tag"><LockKeyhole size={13} /> No model egress</span></div><p className="section-intro">Paste a suspicious text or email. Threadline checks for common pressure tactics on this device; its signals are prompts to verify, not proof a message is fraudulent.</p><form onSubmit={submitCheck}><label className="scam-input-label">MESSAGE TO CHECK<textarea value={message} onChange={e => setMessage(e.target.value)} rows={6} maxLength={20000} placeholder="Paste a suspicious message here…" /></label><div className="scam-form-footer"><span>The message is analyzed locally. Only its digest and matched signal labels are saved.</span><button className="button button-primary" type="submit"><ShieldAlert size={14} /> Check message</button></div></form>
      {result && <div className={`scam-result ${result.score >= 50 ? 'high' : result.score >= 20 ? 'caution' : ''}`}><div className="scam-score"><span>{result.score}</span><small>/ 100 signal score</small><b>{result.band}</b></div><div className="scam-result-content"><strong>{result.signals.length ? `${result.signals.length} pressure signal${result.signals.length === 1 ? '' : 's'} found` : 'No listed pressure signals found'}</strong>{result.signals.length > 0 && <ul>{result.signals.map(s => <li key={s.id}>{s.label}</li>)}</ul>}<ul className="scam-advice">{result.advice.map(x => <li key={x}>{x}</li>)}</ul></div></div>}
    </section>
    <section className="panel family-panel"><div className="panel-head"><div><div className="eyebrow">FAMILY VERIFICATION</div><h2>Agree on a private phrase.</h2></div><span className="local-tag"><KeyRound size={13} /> Stored as a salted hash</span></div><p className="section-intro">Set up a phrase with someone you trust, then verify it when an unexpected call asks for money or private information. Share it in person or through a channel you already trust. Threadline never stores the phrase itself.</p>
      {family.length > 0 && <><div className="family-list">{family.map(member => <div key={member.id} className="family-row"><span><strong>{member.display_name}</strong><small>{member.relationship}</small></span><button className="text-button" onClick={() => onRemoveFamily(member)}>Remove</button></div>)}</div><form className="verify-form" onSubmit={verify}><label>Contact<select value={memberId || family[0].id} onChange={e => { setMemberId(e.target.value); setVerification(null); }}><option value="" disabled>Select contact</option>{family.map(m => <option key={m.id} value={m.id}>{m.display_name}</option>)}</select></label><label>Phrase they give you<input type="password" autoComplete="off" value={phrase} onChange={e => setPhrase(e.target.value)} /></label><button className="button button-soft" type="submit">Verify phrase</button></form>{verification && <div className={`verify-result ${verification.verified ? 'verified' : 'failed'}`}><strong>{verification.verified ? 'Phrase matched' : 'Phrase did not match'}</strong><span>{verification.next_step}</span></div>}</>}
      <details className="family-add"><summary>Add trusted contact <Plus size={13} /></summary><form onSubmit={addProfile}><label>Name<input value={name} onChange={e => setName(e.target.value)} maxLength={80} /></label><label>Relationship<input value={relationship} onChange={e => setRelationship(e.target.value)} maxLength={80} /></label><label>Private phrase<input type="password" autoComplete="new-password" value={newPhrase} onChange={e => setNewPhrase(e.target.value)} minLength={8} maxLength={200} /><small>Use a unique phrase of at least 8 characters; it is not shown again after saving.</small></label><button className="button button-primary" type="submit">Save phrase hash</button></form></details>
    </section>
    <section className="panel scam-history"><div className="panel-head"><div><div className="eyebrow">LOCAL CHECK HISTORY</div><h2>Recent checks <span className="small-count">{checks.length}</span></h2></div></div>{checks.length ? checks.slice(0, 8).map(check => <div className="scam-history-row" key={check.id}><div><strong>{check.band}</strong><span>{check.signals.map(s => s.label).join(' · ') || 'No listed signals'}</span></div><b>{check.score}</b><time>{new Date(check.created_at).toLocaleString()}</time><button className="icon-button" title="Delete this local check receipt" onClick={() => onRemoveCheck(check)}><X size={13} /></button></div>) : <div className="quiet-empty"><span className="quiet-check"><ShieldCheck size={16} /></span><div><strong>No checks yet.</strong><p>Messages are never retained; history contains only a digest and signal labels.</p></div></div>}</section>
  </div><aside className="scam-aside"><div className="policy-explainer"><div className="eyebrow">A SAFER SECOND</div><h3>Take control back from urgency.</h3><div className="trust-steps"><div className="trust-step"><span className="step-no">01</span><div><strong>Pause</strong><p>Pressure to act quickly is a reason to verify through another route.</p></div></div><div className="trust-step"><span className="step-no">02</span><div><strong>Keep secrets private</strong><p>Never share an OTP, PIN, password, or remote-control access with an unsolicited caller.</p></div></div><div className="trust-step"><span className="step-no">03</span><div><strong>Call a known number</strong><p>Use a contact saved before the message arrived; do not rely on its links or caller ID.</p></div></div></div><div className="enforcement-badge"><LockKeyhole size={14} /><span>Local pattern checks can miss scams and can flag legitimate messages.</span></div></div></aside></div>;
}

function PolicyIcon({ type }) { return type === 'create_reminder' ? <Bell size={16} /> : type === 'calendar_export' ? <FileClock size={16} /> : <MessageSquareText size={16} />; }

function ActionCard({ action, onDecision }) {
  const [show, setShow] = useState(false);
  const p = action.payload || {};
  return <div className="action-card"><div className="action-card-top"><span className="action-type"><PolicyIcon type={action.action_type} />{action.action_type.replace('_', ' ')}</span><span className="queued-tag">AWAITING APPROVAL</span></div><strong>{action.title}</strong>{action.loop_title && <span className="action-origin">From open loop · {action.loop_title}</span>}<button className="action-preview-toggle" onClick={() => setShow(!show)}>{show ? 'Hide details' : 'Inspect intended effect'}<ChevronDown size={13} /></button>{show && <pre className="action-payload">{JSON.stringify(p, null, 2)}</pre>}<div className="action-card-footer"><span><LockKeyhole size={12} /> Local only · no external send</span><div><button className="button button-soft" onClick={() => onDecision(action, 'reject')}>Decline</button><button className="button button-primary" onClick={() => onDecision(action, 'approve')}><Check size={14} /> Approve</button></div></div></div>;
}

function SourcesView({ sources, onImport, onRemove, onPreview, onDemo, busy }) {
  return <div className="sources-layout"><section className="panel sources-panel"><div className="panel-head"><div><div className="eyebrow">YOUR PRIVATE INBOX</div><h2>Sources you chose <span className="small-count">{sources.length}</span></h2></div><button className="button button-primary" onClick={onImport}><Plus size={15} /> Add source</button></div><p className="section-intro">Sources live in your local workspace. Add them one at a time, or drop files into the watched import folder on your device.</p><div className="source-file-strip"><div className="folder-glyph"><FilePlus2 size={17} /></div><div><strong>Local import folder</strong><span>Configured in your local environment · checked every 20 seconds</span></div><span className="folder-watch"><i /> WATCHING</span></div>{sources.length ? <div className="source-list">{sources.map(s => <div key={s.id} className="source-row"><div className={`source-file-icon source-${s.kind}`}>{s.kind === 'email' ? <MessageSquareText size={16} /> : s.kind === 'calendar' ? <FileClock size={16} /> : <FileText size={16} />}</div><div className="source-info"><strong>{s.filename}</strong><span>{s.title} · added {timeAgo(s.created_at)}</span></div><span className={`source-status ${s.scanned ? 'processed' : ''}`}><i />{s.scanned ? 'In memory' : 'Ready to scan'}</span><button className="icon-button source-delete" title="Delete source and extracted memory" onClick={() => onRemove(s)}><X size={15} /></button></div>)}</div> : <div className="empty-state source-empty"><div className="empty-spark"><FileText size={20} /></div><h3>No sources yet.</h3><p>Start with one note, email, or calendar file. Your first import stays on this device.</p><button className="button button-primary" onClick={onImport}><Upload size={14} /> Import a source</button><button className="text-button sample-link" disabled={busy === 'demo'} onClick={onDemo}>or load synthetic demo data</button></div>}{sources.some(s => !s.scanned) && <div className="source-scan-cta"><div><strong>{sources.filter(s => !s.scanned).length} source{sources.filter(s => !s.scanned).length === 1 ? '' : 's'} ready for a scan</strong><span>Preview the minimized model request before sending anything.</span></div><button className="button button-dark" onClick={() => onPreview('commitment-scan')} disabled={busy === 'preview'}>{busy === 'preview' ? <LoaderCircle size={15} className="spin" /> : <Sparkles size={15} />} Review sources</button></div>}</section><aside className="source-guide"><div className="eyebrow">SOURCES, BY DESIGN</div><h3>You choose what Threadline knows.</h3><p>There's no always-on account connection. Bring information in when it's useful, and remove it when it isn't.</p><div className="format-grid"><span><Mail size={14} /> .eml</span><span><FileClock size={14} /> .ics</span><span><FileText size={14} /> .txt</span><span><FileText size={14} /> .md</span></div><div className="source-guide-rule"><ShieldCheck size={15} /> Every memory item links back to a source you can inspect.</div></aside></div>;
}

function PrivacyView({ health, events, summary, expanded, setExpanded, onExport }) {
  const [showAll, setShowAll] = useState(false);
  const shown = showAll ? events : events.slice(0, 5);
  const metrics = [
    ['Original files uploaded', summary?.source_files_uploaded ?? 0, 'Source attachments sent'],
    ['Remote attempts', summary?.attempts ?? events.length, 'Includes failed requests'],
    ['Successful responses', summary?.sent ?? events.filter(e => e.status === 'sent').length, 'Returned successfully'],
    ['Redaction matches', summary?.redaction_matches ?? 0, 'Pattern replacements, not identity detection'],
    ['Local-only scans', summary?.local_only_scans ?? 0, 'No inference request'],
    ['Prompt characters', summary?.payload_characters ?? 0, 'Across attempted requests'],
  ];
  return <div className="privacy-layout"><div className="privacy-main">
    <section className="panel privacy-overview"><div className="panel-head"><div><div className="eyebrow">THE PRIVACY RECEIPT</div><h2>Your device, your memory.</h2></div><span className="local-tag"><LockKeyhole size={13} /> Local-first</span></div><p className="section-intro">Sources and durable memory live in the local SQLite workspace. A remote model request happens only after you inspect and confirm the preview.</p>
      <div className="egress-summary"><div className="eyebrow">RUNNING DATA MOVEMENT TOTALS</div><div className="egress-summary-grid">{metrics.map(([label, value, note]) => <div key={label}><span>{label}</span><strong>{Number(value).toLocaleString()}</strong><small>{note}</small></div>)}</div><p className="egress-summary-note">Original source files are not uploaded as attachments. Confirmed requests send minimized text shown in each receipt. Regex redaction can miss personal information.</p></div>
      <div className="egress-boundary"><div className="boundary-icon"><ArrowUpRightFromSquare size={16} /></div><div><strong>What leaves this device?</strong><p>Only the selected text included in a confirmed request. The receipt shows its exact request body and response status.</p></div></div>
    </section>
    <section className="panel egress-panel"><div className="panel-head"><div><div className="eyebrow">MODEL EGRESS LOG</div><h2>Receipts <span className="small-count">{events.length}</span></h2></div><span className="model-chip"><span className="model-chip-dot" /> {health?.api_key_configured ? 'Nebius Token Factory' : 'No model key configured'}</span></div>{events.length ? <div className="egress-list">{shown.map(event => <div className="egress-event" key={event.id}><button className="egress-event-top" onClick={() => setExpanded(expanded === event.id ? null : event.id)}><span className={`egress-state ${event.status}`}><i />{event.status}</span><span className="egress-model">{event.model}</span><span className="egress-detail">{event.source_ids.length} source{event.source_ids.length === 1 ? '' : 's'} | {event.redacted_fields} redaction match{event.redacted_fields === 1 ? '' : 'es'}</span><time>{new Date(event.created_at).toLocaleString()}</time><ChevronDown className={expanded === event.id ? 'rotated' : ''} size={15} /></button>{expanded === event.id && <div className="egress-receipt"><div><span className="eyebrow">EXACT MINIMIZED PROMPT</span><button className="copy-payload" onClick={() => navigator.clipboard?.writeText(event.payload)}>Copy</button></div><pre>{event.payload}</pre>{event.response_summary && <p className="receipt-response">{event.response_summary}</p>}</div>}</div>)}</div> : <div className="quiet-empty"><div className="quiet-check"><LockKeyhole size={17} /></div><div><strong>No model requests yet.</strong><p>Local-only scans do not create egress requests.</p></div></div>}{events.length > 5 && <button className="panel-bottom-link" onClick={() => setShowAll(!showAll)}>{showAll ? 'Show recent only' : 'View all receipts'} <ArrowRight size={14} /></button>}</section>
  </div><aside className="privacy-aside"><div className="device-boundary"><div className="device-top"><span className="device-light" /><span>YOUR DEVICE</span><MoreHorizontal size={15} /></div><div className="device-diagram"><div className="device-file"><FileText size={17} /><span>Sources</span><b>Local</b></div><div className="device-link"><span /><ArrowRight size={13} /><span /></div><div className="device-file memory"><Fingerprint size={17} /><span>Memory</span><b>Local</b></div><div className="device-egress"><ArrowUpRight size={14} /><span>Selected context</span></div></div><div className="device-note"><span className="runtime-dot connected" /> Confirmed requests go to Token Factory</div></div><button className="export-card" onClick={onExport}><span className="export-icon"><Download size={16} /></span><span><strong>Take your data with you</strong><small>Export your workspace as JSON</small></span><ArrowRight size={15} /></button><div className="local-caveat"><CircleHelp size={14} /><p>This database is not encrypted by the app. Use device-level disk encryption and use synthetic data in a hosted demo.</p></div></aside></div>;
}
function ScanDialog({ preview, busy, onClose, onLocal, onRemote }) {
  const [showPayload, setShowPayload] = useState(true);
  const [confirmed, setConfirmed] = useState(false);
  const isBusy = busy === 'remote' || busy === 'local';
  return <div className="modal-backdrop scan-backdrop" onMouseDown={e => e.target === e.currentTarget && !isBusy && onClose()}><section className="dialog scan-dialog"><header className="dialog-header"><div><div className="eyebrow">PRE-FLIGHT CHECK · {preview.source_count} SOURCE{preview.source_count === 1 ? '' : 'S'}</div><h2>Review what the model will see.</h2></div><button disabled={isBusy} className="icon-button" onClick={onClose}><X size={18} /></button></header><div className="scan-locality"><div className="scan-lock"><LockKeyhole size={16} /></div><div><strong>Your originals stay here.</strong><span>Threadline prepares a minimized text request. You choose whether it leaves this device.</span></div></div><div className="scan-facts"><div><span>MODEL</span><strong>{preview.model}</strong></div><div><span>FIELDS REDACTED</span><strong>{preview.redacted_count}</strong></div><div><span>SKILL</span><strong>{preview.skill}</strong></div><div><span>ROUTE</span><strong>{preview.api_key_configured ? 'Nebius Token Factory' : 'Not connected'}</strong></div></div><button className="payload-toggle" onClick={() => setShowPayload(!showPayload)}><span><FileText size={14} /> Exact outgoing payload</span><ChevronDown className={showPayload ? 'rotated' : ''} size={14} /></button>{showPayload && <pre className="payload-preview">{preview.payload}</pre>}{preview.redaction_counts && Object.keys(preview.redaction_counts).length > 0 && <div className="redaction-note"><ShieldCheck size={14} /> Redacted: {Object.entries(preview.redaction_counts).map(([k, v]) => `${v} ${k}`).join(' · ')}</div>}<label className="send-confirm"><input type="checkbox" checked={confirmed} onChange={e => setConfirmed(e.target.checked)} /><span>I reviewed this preview and understand this text will be sent to the selected model if I choose the remote scan.</span></label><footer className="dialog-footer scan-footer"><button className="button button-soft" disabled={isBusy} onClick={onLocal}><span className="local-option"><span className="runtime-dot" /> Local-only scan</span><span className="local-option-note">No model request is sent</span></button><button className="button button-primary" disabled={!confirmed || !preview.api_key_configured || isBusy} onClick={onRemote}>{busy === 'remote' ? <LoaderCircle size={15} className="spin" /> : <ArrowUpRight size={15} />} {busy === 'remote' ? 'Sending...' : preview.api_key_configured ? 'Send minimized preview' : 'Nebius key required'}</button></footer>{!preview.api_key_configured && <div className="key-missing">Add <code>NEBIUS_API_KEY</code> to your local environment to enable Nemotron. You can still use the local-only scan.</div>}</section></div>;
}

function downloadText(filename, content, mime = 'text/plain') {
  const url = URL.createObjectURL(new Blob([content], { type: mime }));
  const a = document.createElement('a'); a.href = url; a.download = filename; a.click(); URL.revokeObjectURL(url);
}

export default App;

