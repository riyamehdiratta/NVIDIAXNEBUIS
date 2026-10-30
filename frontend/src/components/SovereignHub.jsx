import {
  Activity,
  AlertTriangle,
  ArrowRight,
  Brain,
  Check,
  CheckCircle2,
  ChevronDown,
  ChevronRight,
  Clock,
  Code,
  Compass,
  Cpu,
  Database,
  ExternalLink,
  Eye,
  FileCode,
  Flame,
  Folder,
  Gauge,
  GitBranch,
  HelpCircle,
  History,
  Layers,
  Link2,
  Lock,
  Maximize2,
  Monitor,
  Moon,
  MousePointer,
  Network,
  Play,
  Plus,
  Radio,
  RefreshCw,
  RotateCcw,
  Scale,
  Shield,
  ShieldAlert,
  ShieldCheck,
  Sliders,
  Sparkles,
  Square,
  Terminal,
  TrendingUp,
  Workflow,
  X,
  Zap,
} from 'lucide-react';
import { useCallback, useEffect, useMemo, useState } from 'react';
import { api, post } from '../api';
import './SovereignHub.css';

export function SovereignHub({ setToast, defaultTab = 'overview' }) {
  const [activeTab, setActiveTab] = useState(defaultTab);
  const [status, setStatus] = useState(null);
  const [loading, setLoading] = useState(true);

  // Pillar 1: Apprenticeship
  const [apprenticeStatus, setApprenticeStatus] = useState(null);
  const [traces, setTraces] = useState([]);
  const [newTraceTitle, setNewTraceTitle] = useState('Universal Desktop Demonstration');
  const [newTraceProcess, setNewTraceProcess] = useState('');
  const [synthesizedWf, setSynthesizedWf] = useState(null);
  const [isSynthesizing, setIsSynthesizing] = useState(false);

  // Pillar 2: Preference Model
  const [prefStatus, setPrefStatus] = useState(null);
  const [activeQueries, setActiveQueries] = useState([]);
  const [predictAction, setPredictAction] = useState('create_reminder');
  const [predictLifeArea, setPredictLifeArea] = useState('work');
  const [predictResult, setPredictResult] = useState(null);

  // Pillar 3: Provable Autonomy & CRC
  const [conformalStatus, setConformalStatus] = useState([]);
  const [riskBudgetAlpha, setRiskBudgetAlpha] = useState(0.02);
  const [evalActionType, setEvalActionType] = useState('create_reminder');
  const [evalProb, setEvalProb] = useState(0.96);
  const [evalResult, setEvalResult] = useState(null);

  // Pillar 4: Tool Synthesizer
  const [synthesizedTools, setSynthesizedTools] = useState([]);
  const [newToolName, setNewToolName] = useState('custom.data_aggregator');
  const [newToolDesc, setNewToolDesc] = useState('Aggregates and formats heterogeneous data items securely');
  const [newToolOp, setNewToolOp] = useState('computation');
  const [selectedTool, setSelectedTool] = useState(null);
  const [synthesizingTool, setSynthesizingTool] = useState(false);

  // Pillar 5: Causal World Model & Horizon
  const [horizonForecast, setHorizonForecast] = useState(null);
  const [causalTrials, setCausalTrials] = useState([]);
  const [triples, setTriples] = useState([]);
  const [newTrialName, setNewTrialName] = useState('Digest Batching Timing');
  const [newTrialIntervention, setNewTrialIntervention] = useState('Send at 08:30 vs Ad-hoc');
  const [newTrialMetric, setNewTrialMetric] = useState('Action Completion Rate');
  const [newTripleSubj, setNewTripleSubj] = useState('User');
  const [newTriplePred, setNewTriplePred] = useState('prefers_notification_at');
  const [newTripleObj, setNewTripleObj] = useState('09:00 AM');

  // Pillar 7: Computer-Use Agent & Action Ladder Substrate
  const [deviceManifest, setDeviceManifest] = useState(null);
  const [deviceHistory, setDeviceHistory] = useState([]);
  const [customGoal, setCustomGoal] = useState('Create a project workspace with README and config');
  const [customCategory, setCustomCategory] = useState('filesystem');
  const [deviceResult, setDeviceResult] = useState(null);
  const [isDeviceRunning, setIsDeviceRunning] = useState(false);

  // Pillar 6: Universal MCP & App Connectors Studio
  const [connectors, setConnectors] = useState([]);
  const [allTools, setAllTools] = useState([]);
  const [selectedToolForRun, setSelectedToolForRun] = useState('github.search_issues');
  const [toolArgsJson, setToolArgsJson] = useState('{\n  "query": "timeout",\n  "repo": "nvidia/nemotron"\n}');
  const [toolRunOutput, setToolRunOutput] = useState(null);
  const [isToolRunning, setIsToolRunning] = useState(false);
  const [newConnName, setNewConnName] = useState('');
  const [newConnDisplayName, setNewConnDisplayName] = useState('');
  const [newConnKind, setNewConnKind] = useState('mcp_stdio');
  const [newConnDesc, setNewConnDesc] = useState('');
  // Pillar 8: Dreams, Proves & Earns Substrate
  const [dreamReport, setDreamReport] = useState(null);
  const [isDreaming, setIsDreaming] = useState(false);
  const [backtestCandidate, setBacktestCandidate] = useState('decline_spam_invites');
  const [backtestAlpha, setBacktestAlpha] = useState(0.10);
  const [backtestAdversarial, setBacktestAdversarial] = useState(false);
  const [backtestResult, setBacktestResult] = useState(null);
  const [isBacktesting, setIsBacktesting] = useState(false);
  const [privacyBlocks, setPrivacyBlocks] = useState([]);
  const [privacyAudit, setPrivacyAudit] = useState(null);
  const [isAuditingPrivacy, setIsAuditingPrivacy] = useState(false);
  const [chaosResult, setChaosResult] = useState(null);
  const [isChaosRunning, setIsChaosRunning] = useState(false);

  // Load state across all pillars + MCP connectors
  const refreshAll = useCallback(async (quiet = false) => {
    if (!quiet) setLoading(true);
    try {
      const [
        appr,
        trc,
        pref,
        qrs,
        conf,
        tools,
        trials,
        horizon,
        trps,
        conns,
        toolsList,
        devManifest,
        devHist,
        dreamReportData,
        privacyData,
        chaosData
      ] = await Promise.all([
        api('/apprenticeship/status').catch(() => null),
        api('/apprenticeship/traces').catch(() => []),
        api('/preferences/status').catch(() => null),
        api('/preferences/active_queries').catch(() => ({ active_queries: [] })),
        api('/conformal/status').catch(() => ({ policies: [] })),
        api('/synthesizer/tools').catch(() => []),
        api('/world_model/causal_trials').catch(() => []),
        api('/world_model/simulate_horizon').catch(() => null),
        api('/world_model/triples').catch(() => []),
        api('/connectors/').catch(() => []),
        api('/connectors/all_tools').catch(() => ({ tools: [] })),
        api('/device/manifest').catch(() => null),
        api('/device/history').catch(() => []),
        api('/dreaming/latest').catch(() => null),
        api('/privacy/chain').catch(() => []),
        api('/chaos/latest').catch(() => null),
        api('/connectors').catch(() => []),
        api('/connectors/all_tools').catch(() => ({ tools: [] })),
      ]);

      setApprenticeStatus(appr);
      if (appr?.foreground_window?.process_name && !newTraceProcess) {
        setNewTraceProcess(appr.foreground_window.process_name);
      }
      setTraces(trc);
      setPrefStatus(pref);
      setActiveQueries(qrs.active_queries || []);
      setConformalStatus(conf.policies || []);
      setSynthesizedTools(tools);
      if (tools.length > 0 && !selectedTool) {
        setSelectedTool(tools[0]);
      }
      setCausalTrials(trials);
      setHorizonForecast(horizon);
      setTriples(trps);
      setConnectors(Array.isArray(conns) ? conns : []);
      setAllTools(toolsList.tools || []);
      if (dreamReportData) setDreamReport(dreamReportData);
      if (Array.isArray(privacyData)) setPrivacyBlocks(privacyData);
      if (chaosData) setChaosResult(chaosData);
    } catch (e) {
      console.error('Failed to load Sovereign Hub data', e);
    } finally {
      setLoading(false);
    }
  }, [newTraceProcess, selectedTool]);

  useEffect(() => {
    refreshAll();
    const interval = setInterval(() => {
      if (!document.hidden) refreshAll(true);
    }, 4000);
    return () => clearInterval(interval);
  }, [refreshAll]);

  // Pillar 1 Handlers
  const handleStartRecording = async () => {
    try {
      const res = await post('/apprenticeship/start', {
        title: newTraceTitle,
        process_name: newTraceProcess || 'universal_os',
        window_title: apprenticeStatus?.foreground_window?.window_title || 'Active Window',
      });
      setToast('Ambient OS demonstration recording started');
      await refreshAll(true);
    } catch (e) {
      setToast(e.message);
    }
  };

  const handleRecordEvent = async (type, targetName, val) => {
    if (!apprenticeStatus?.active_session?.trace_id) {
      setToast('No active recording session. Start recording first.');
      return;
    }
    try {
      await post('/apprenticeship/record_event', {
        trace_id: apprenticeStatus.active_session.trace_id,
        event_type: type,
        target_role: type === 'type' ? 'textbox' : 'element',
        target_name: targetName,
        value: val,
      });
      setToast(`Recorded: ${type} "${targetName}"`);
      await refreshAll(true);
    } catch (e) {
      setToast(e.message);
    }
  };

  const handleStopRecording = async () => {
    const traceId = apprenticeStatus?.active_session?.trace_id;
    if (!traceId) return;
    try {
      await post('/apprenticeship/stop', { trace_id: traceId });
      setToast('Demonstration recording completed. Ready to synthesize DAG.');
      await refreshAll(true);
    } catch (e) {
      setToast(e.message);
    }
  };

  const handleSynthesizeDAG = async (traceId) => {
    setIsSynthesizing(true);
    try {
      const res = await post('/apprenticeship/synthesize', { trace_id: traceId });
      setSynthesizedWf(res);
      setToast(`Autonomous DAG compiled! (${res.total_nodes} nodes, ${res.lifted_inputs.length} lifted params)`);
      await refreshAll(true);
    } catch (e) {
      setToast(e.message);
    } finally {
      setIsSynthesizing(false);
    }
  };

  // Pillar 2 Handlers
  const handleAnswerActiveQuery = async (query, approved) => {
    try {
      const res = await post('/preferences/feedback', {
        action_type: query.action_type,
        approved,
        learning_rate: 0.20,
      });
      setToast(`Bayesian update: Error ${res.prediction_error} · Weights adjusted`);
      await refreshAll(true);
    } catch (e) {
      setToast(e.message);
    }
  };

  const handlePredictApproval = async () => {
    try {
      const res = await post('/preferences/predict', {
        action_type: predictAction,
        life_area: predictLifeArea,
        payload: { source_id: 'test_doc' },
        daily_count: 3,
      });
      setPredictResult(res);
    } catch (e) {
      setToast(e.message);
    }
  };

  // Pillar 3 Handlers
  const handleCalibrateConformal = async (actionType) => {
    try {
      const res = await post('/conformal/calibrate', {
        action_type: actionType,
        risk_budget_alpha: Number(riskBudgetAlpha),
      });
      setToast(`Calibrated ${actionType}: tau = ${res.calibrated_tau ?? 'N/A'} (alpha = ${res.risk_budget_alpha})`);
      await refreshAll(true);
    } catch (e) {
      setToast(e.message);
    }
  };

  const handleEvaluateGate = async () => {
    try {
      const res = await post('/conformal/evaluate', {
        action_type: evalActionType,
        predicted_prob: Number(evalProb),
      });
      setEvalResult(res);
    } catch (e) {
      setToast(e.message);
    }
  };

  // Pillar 4 Handlers
  const handleSynthesizeNewTool = async (e) => {
    e.preventDefault();
    setSynthesizingTool(true);
    try {
      const res = await post('/synthesizer/synthesize_tool', {
        name: newToolName,
        description: newToolDesc,
        operation_type: newToolOp,
      });
      setToast(`Tool ${res.name} synthesized, sandbox-tested, and registered!`);
      await refreshAll(true);
      setSelectedTool(res);
    } catch (e) {
      setToast(e.message);
    } finally {
      setSynthesizingTool(false);
    }
  };

  const handleVerifyTool = async (toolId) => {
    try {
      const res = await post('/synthesizer/verify_tool', {
        tool_id: toolId,
        sample_inputs: { items: [10, 20, 30], text: 'Autonomous verification run' },
      });
      setToast(res.verified ? 'Sandbox test passed: 100% verified' : 'Sandbox test failed');
      await refreshAll(true);
    } catch (e) {
      setToast(e.message);
    }
  };

  // Pillar 5 Handlers
  const handleRunCausalTrial = async (e) => {
    e.preventDefault();
    try {
      const res = await post('/world_model/causal_trials/evaluate', {
        name: newTrialName,
        intervention: newTrialIntervention,
        outcome_metric: newTrialMetric,
        treatment_samples: [5.2, 5.8, 5.0, 6.1, 5.4],
        control_samples: [2.8, 3.1, 2.5, 3.4, 2.9],
      });
      const ateFormatted = `${res.causal_effect_ate > 0 ? '+' : ''}${Number(res.causal_effect_ate).toFixed(2)}`;
      setToast(`Trial evaluated! ATE = ${ateFormatted} (${res.statistically_significant ? 'Significant' : 'Inconclusive'})`);
      await refreshAll(true);
    } catch (e) {
      setToast(e.message);
    }
  };

  const handleAddTriple = async (e) => {
    e.preventDefault();
    try {
      await post('/world_model/triples', {
        subject: newTripleSubj,
        predicate: newTriplePred,
        object: newTripleObj,
        confidence: 1.0,
        evidence: 'User-stated constraint in Sovereign HUD',
      });
      setToast('Knowledge belief asserted with provenance link');
      setNewTripleSubj('');
      setNewTriplePred('');
      setNewTripleObj('');
      await refreshAll(true);
    } catch (e) {
      setToast(e.message);
    }
  };

  // Pillar 8: Dreams, Proves & Earns Handlers
  const handleTriggerDream = async () => {
    setIsDreaming(true);
    try {
      const res = await post('/dreaming/trigger', {});
      setDreamReport(res);
      setToast('Overnight dream cycle complete! New report generated.');
      await refreshAll(true);
    } catch (e) {
      setToast(e.message);
    } finally {
      setIsDreaming(false);
    }
  };

  const handleRunBacktest = async () => {
    setIsBacktesting(true);
    try {
      const res = await post('/backtest/run', {
        policy_name: backtestCandidate,
        target_autonomy_level: 3,
        time_window_days: 90,
        alpha_threshold: Number(backtestAlpha),
        inject_adversarial_counterexample: backtestAdversarial
      });
      setBacktestResult(res);
      setToast(`Backtest complete: ${res.status.toUpperCase()}`);
      await refreshAll(true);
    } catch (e) {
      setToast(e.message);
    } finally {
      setIsBacktesting(false);
    }
  };

  const handleVerifyPrivacyChain = async () => {
    setIsAuditingPrivacy(true);
    try {
      const res = await post('/privacy/verify', {});
      setPrivacyAudit(res);
      setToast(res.audit_verdict);
      await refreshAll(true);
    } catch (e) {
      setToast(e.message);
    } finally {
      setIsAuditingPrivacy(false);
    }
  };

  const handleRunChaosMonkey = async () => {
    setIsChaosRunning(true);
    try {
      const res = await post('/chaos/run', {});
      setChaosResult(res);
      setToast(`Chaos Monkey stress test complete: ${res.resilience_score}% Resilience!`);
      await refreshAll(true);
    } catch (e) {
      setToast(e.message);
    } finally {
      setIsChaosRunning(false);
    }
  };

  // Pillar 7: Computer-Use Device Agent Handlers
  const handleRunDeviceGoal = async (goalToRun, categoryToRun, params = {}, approve = false) => {
    setIsDeviceRunning(true);
    setDeviceResult(null);
    try {
      const res = await post('/device/execute', {
        goal: goalToRun || customGoal,
        task_category: categoryToRun || customCategory,
        parameters: params,
        autonomy_level: approve ? 3 : 1,
        human_approved: approve,
      });
      setDeviceResult(res);
      setToast(res.message);
      await refreshAll(true);
    } catch (e) {
      setDeviceResult({ verified: false, message: e.message });
      setToast(e.message);
    } finally {
      setIsDeviceRunning(false);
    }
  };

  const handleUndoDeviceAction = async (receiptId) => {
    try {
      const res = await post(`/device/undo/${receiptId}`);
      setToast(res.message);
      await refreshAll(true);
    } catch (e) {
      setToast(e.message);
    }
  };

  // Pillar 6: Connectors Handlers
  const handleToggleConnector = async (id) => {
    try {
      const res = await post(`/connectors/${id}/toggle`);
      setToast(res.message);
      await refreshAll(true);
    } catch (e) {
      setToast(e.message);
    }
  };

  const handleRunToolTest = async () => {
    setIsToolRunning(true);
    setToolRunOutput(null);
    try {
      let parsedArgs = {};
      if (toolArgsJson.trim()) {
        try {
          parsedArgs = JSON.parse(toolArgsJson);
        } catch (err) {
          throw new Error('Arguments must be valid JSON: ' + err.message);
        }
      }
      const res = await post('/connectors/call_tool', {
        tool_name: selectedToolForRun,
        args: parsedArgs,
        source_caller: 'mcp_studio',
      });
      setToolRunOutput(res);
      setToast(`Executed ${selectedToolForRun} successfully`);
    } catch (e) {
      setToolRunOutput({ success: false, error: e.message });
      setToast(e.message);
    } finally {
      setIsToolRunning(false);
    }
  };

  const handleRegisterConnector = async (e) => {
    e.preventDefault();
    if (!newConnName || !newConnDisplayName) return;
    try {
      await post('/connectors', {
        name: newConnName.toLowerCase().replace(/[^a-z0-9_-]/g, '_'),
        display_name: newConnDisplayName,
        kind: newConnKind,
        description: newConnDesc || `Custom ${newConnDisplayName} connector`,
        config: {},
        tools: [],
      });
      setToast(`Registered connector: ${newConnDisplayName}`);
      setNewConnName('');
      setNewConnDisplayName('');
      setNewConnDesc('');
      await refreshAll(true);
    } catch (e) {
      setToast(e.message);
    }
  };

  const handleSelectToolSample = (toolName) => {
    setSelectedToolForRun(toolName);
    const sampleArgsMap = {
      'github.search_issues': '{\n  "query": "timeout",\n  "repo": "nvidia/nemotron"\n}',
      'github.get_repo_summary': '{\n  "repo": "nvidia/nemotron"\n}',
      'github.create_issue_draft': '{\n  "title": "Bug: Conformal risk bound recalculation",\n  "body": "Re-evaluate alpha calibration after shift"\n}',
      'gsuite.search_docs': '{\n  "query": "roadmap"\n}',
      'gsuite.list_calendar_events': '{\n  "days": 7\n}',
      'slack.search_messages': '{\n  "query": "deployment",\n  "channel": "engineering"\n}',
      'slack.draft_channel_update': '{\n  "channel": "general",\n  "topics": "Sprint milestone reached"\n}',
      'fs.list_directory': '{\n  "path": "./data"\n}',
      'fs.read_file': '{\n  "path": "README.md"\n}',
      'db.inspect_schema': '{\n  "table_name": "loops"\n}',
      'db.execute_query': '{\n  "query": "SELECT COUNT(*) as count FROM loops"\n}',
      'web.search': '{\n  "query": "NVIDIA Nemotron 3.5 architecture",\n  "limit": 3\n}',
      'memory.open_loops': '{}',
      'report.daily_reset': '{}',
      'draft.follow_up': '{\n  "source_preview": "Product architecture discussion"\n}',
      'calendar.export': '{}',
    };
    setToolArgsJson(sampleArgsMap[toolName] || '{\n  "arg": "value"\n}');
    setToolRunOutput(null);
  };

  const activeWindow = apprenticeStatus?.foreground_window;
  const isRecording = apprenticeStatus?.is_recording;
  const currentSession = apprenticeStatus?.active_session;

  return (
    <div className="sovereign-hub">
      {/* Executive Sovereign Delegate HUD */}
      <header className="sovereign-hud">
        <div className="sovereign-hud-left">
          <div className="hud-icon-wrap">
            <Cpu size={24} strokeWidth={2.2} />
          </div>
          <div className="hud-title-block">
            <h2>Sovereign Delegate · AGI Operating System</h2>
            <p>
              Universal OS Perception · Conformal Risk Bounds (α = {riskBudgetAlpha}) · Self-Programming Runtime
            </p>
          </div>
        </div>
        <div className="sovereign-hud-right">
          <div className="os-window-pill" title="Live foreground window detected across any native desktop application">
            <span className="os-pulse-dot" />
            <span>Active OS:</span>
            <strong>{activeWindow?.window_title || 'Desktop'}</strong>
            <small style={{ color: '#88a88c' }}>({activeWindow?.process_name || 'universal_os'})</small>
          </div>
          <button className="button button-soft" onClick={() => refreshAll(false)} title="Poll OS state">
            <RefreshCw size={13} className={loading ? 'spin' : ''} />
          </button>
        </div>
      </header>

      {/* 5 Pillars Navigation Bar */}
      <nav className="sovereign-tabs">
        <button
          className={`sovereign-tab ${activeTab === 'overview' ? 'active' : ''}`}
          onClick={() => setActiveTab('overview')}
        >
          <Layers size={14} />
          <span>AGI Core Matrix</span>
        </button>
        <button
          className={`sovereign-tab ${activeTab === 'apprenticeship' ? 'active' : ''}`}
          onClick={() => setActiveTab('apprenticeship')}
        >
          <Monitor size={14} />
          <span>1. Ambient Apprenticeship</span>
          {isRecording && <span className="sovereign-tab-badge" style={{ background: '#fadad7', color: '#c33a28' }}>REC</span>}
        </button>
        <button
          className={`sovereign-tab ${activeTab === 'conformal' ? 'active' : ''}`}
          onClick={() => setActiveTab('conformal')}
        >
          <Scale size={14} />
          <span>2. Provable Autonomy (CRC)</span>
          <span className="sovereign-tab-badge">α = {riskBudgetAlpha}</span>
        </button>
        <button
          className={`sovereign-tab ${activeTab === 'preferences' ? 'active' : ''}`}
          onClick={() => setActiveTab('preferences')}
        >
          <Brain size={14} />
          <span>3. Preference Model</span>
          {activeQueries.length > 0 && <span className="sovereign-tab-badge">{activeQueries.length} query</span>}
        </button>
        <button
          className={`sovereign-tab ${activeTab === 'synthesizer' ? 'active' : ''}`}
          onClick={() => setActiveTab('synthesizer')}
        >
          <Terminal size={14} />
          <span>4. Tool Synthesizer</span>
          <span className="sovereign-tab-badge">{synthesizedTools.length} tools</span>
        </button>
        <button
          className={`sovereign-tab ${activeTab === 'world_model' ? 'active' : ''}`}
          onClick={() => setActiveTab('world_model')}
        >
          <Network size={14} />
          <span>5. Causal World Model</span>
          {horizonForecast?.bottlenecks?.length > 0 && (
            <span className="sovereign-tab-badge" style={{ background: '#fdf1dc', color: '#a07127' }}>
              Alert
            </span>
          )}
        </button>
        <button
          className={`sovereign-tab ${activeTab === 'connectors' ? 'active' : ''}`}
          onClick={() => setActiveTab('connectors')}
        >
          <Link2 size={14} />
          <span>6. MCP & Connectors Studio</span>
          <span className="sovereign-tab-badge">{connectors.length} active ({allTools.length} tools)</span>
        </button>
        <button
          className={`sovereign-tab ${activeTab === 'device' ? 'active' : ''}`}
          onClick={() => setActiveTab('device')}
        >
          <Folder size={14} />
          <span>7. Device & Action Ladder</span>
          <span className="sovereign-tab-badge" style={{ background: '#d7f2ea', color: '#1a5f4c' }}>4 RUNGS</span>
        </button>
        <button
          className={`sovereign-tab ${activeTab === 'dreams' ? 'active' : ''}`}
          onClick={() => setActiveTab('dreams')}
        >
          <Moon size={14} />
          <span>8. Dreams, Proves & Earns</span>
          <span className="sovereign-tab-badge" style={{ background: '#e0e7ff', color: '#3730a3' }}>TRIFECTA</span>
        </button>
      </nav>

      {/* TAB 1: OVERVIEW & OS MATRIX */}
      {activeTab === 'overview' && (
        <div className="sovereign-panel-grid">
          <section className="sovereign-card">
            <div className="panel-head">
              <div>
                <div className="eyebrow">CONTINUAL OS COGNITION MATRIX</div>
                <h2>The 5 Pillars of the Sovereign Delegate</h2>
              </div>
              <span className="local-tag">
                <ShieldCheck size={13} /> Locally Governed & Privately Calibrated
              </span>
            </div>
            <p className="section-intro">
              Unlike cloud-tethered voice assistants like Alexa, the Sovereign Delegate runs entirely on your host,
              perceives native applications directly without browser limits, guarantees error rates via distribution-free
              conformal risk bounds, and synthesizes its own tools when existing capabilities fall short.
            </p>

            <div className="matrix-grid">
              <div className="matrix-card" onClick={() => setActiveTab('apprenticeship')}>
                <div className="matrix-card-top">
                  <div className="matrix-card-icon"><Monitor size={15} /></div>
                  <ChevronRight size={14} color="#8a968a" />
                </div>
                <h4>1. Ambient Apprenticeship</h4>
                <p>Watches OS desktop interactions across any app and compiles demonstrations into typed DAGs.</p>
                <div>
                  <span className="matrix-stat">{traces.length}</span>
                  <span className="matrix-stat-sub">traces recorded</span>
                </div>
              </div>

              <div className="matrix-card" onClick={() => setActiveTab('conformal')}>
                <div className="matrix-card-top">
                  <div className="matrix-card-icon"><Scale size={15} /></div>
                  <ChevronRight size={14} color="#8a968a" />
                </div>
                <h4>2. Provable Autonomy (CRC)</h4>
                <p>Mathematically bounds unapproved action risk under error ceiling α with CUSUM drift detection.</p>
                <div>
                  <span className="matrix-stat">{(riskBudgetAlpha * 100).toFixed(0)}%</span>
                  <span className="matrix-stat-sub">max error ceiling</span>
                </div>
              </div>

              <div className="matrix-card" onClick={() => setActiveTab('preferences')}>
                <div className="matrix-card-top">
                  <div className="matrix-card-icon"><Brain size={15} /></div>
                  <ChevronRight size={14} color="#8a968a" />
                </div>
                <h4>3. Preference Model</h4>
                <p>Online Bayesian logistic regression learning your boundaries with active question synthesis.</p>
                <div>
                  <span className="matrix-stat">{activeQueries.length}</span>
                  <span className="matrix-stat-sub">active learning queries</span>
                </div>
              </div>

              <div className="matrix-card" onClick={() => setActiveTab('synthesizer')}>
                <div className="matrix-card-top">
                  <div className="matrix-card-icon"><Terminal size={15} /></div>
                  <ChevronRight size={14} color="#8a968a" />
                </div>
                <h4>4. Self-Extension Studio</h4>
                <p>Synthesizes missing Python tools with inverse rollback handlers, verified in isolated sandboxes.</p>
                <div>
                  <span className="matrix-stat">{synthesizedTools.length}</span>
                  <span className="matrix-stat-sub">custom tools live</span>
                </div>
              </div>

              <div className="matrix-card" onClick={() => setActiveTab('world_model')}>
                <div className="matrix-card-top">
                  <div className="matrix-card-icon"><Network size={15} /></div>
                  <ChevronRight size={14} color="#8a968a" />
                </div>
                <h4>5. Causal World Model</h4>
                <p>Provenance belief store, N-of-1 Rubin causal trials, and 7-day forward horizon rehearsals.</p>
                <div>
                  <span className="matrix-stat">{triples.length}</span>
                  <span className="matrix-stat-sub">provenance beliefs</span>
                </div>
              </div>

              <div className="matrix-card" onClick={() => setActiveTab('connectors')}>
                <div className="matrix-card-top">
                  <div className="matrix-card-icon" style={{ background: '#e1ede0', color: '#2b5a34' }}>
                    <Link2 size={15} />
                  </div>
                  <ChevronRight size={14} color="#8a968a" />
                </div>
                <h4>6. MCP & Connectors Studio</h4>
                <p>25+ tools across GitHub, Google Workspace, Slack, Filesystem, SQLite, and Web Search with live invocation.</p>
                <div>
                  <span className="matrix-stat">{connectors.length}</span>
                  <span className="matrix-stat-sub">connectors ({allTools.length} tools)</span>
                </div>
              </div>
            </div>
          </section>

          <aside className="sovereign-aside">
            <div className="policy-explainer">
              <div className="eyebrow">ARCHITECTURAL SUPERIORITY</div>
              <h3>Why Sovereign Beats Alexa</h3>
              <div className="trust-steps">
                <div className="trust-step">
                  <span className="step-no">01</span>
                  <div>
                    <strong>Zero Platform Limits</strong>
                    <p>Not limited to Amazon or Google ecosystem APIs; directly perceives and operates any desktop software.</p>
                  </div>
                </div>
                <div className="trust-step">
                  <span className="step-no">02</span>
                  <div>
                    <strong>Provable Risk Guarantees</strong>
                    <p>Alexa uses blind heuristic confidence. Sovereign uses Conformal Risk Control guaranteeing &le;2% error.</p>
                  </div>
                </div>
                <div className="trust-step">
                  <span className="step-no">03</span>
                  <div>
                    <strong>Self-Programming Sandbox</strong>
                    <p>When blocked by an unhandled operation, the agent writes, tests, and promotes new tool code on the fly.</p>
                  </div>
                </div>
              </div>
            </div>
          </aside>
        </div>
      )}

      {/* TAB 2: AMBIENT APPRENTICESHIP */}
      {activeTab === 'apprenticeship' && (
        <div className="sovereign-panel-grid">
          <section className="sovereign-card">
            <div className="panel-head">
              <div>
                <div className="eyebrow">PILLAR 1: AMBIENT APPRENTICESHIP</div>
                <h2>Learning by Watching Native Desktop Software</h2>
              </div>
              <span className="local-tag"><Eye size={13} /> Native OS Perception</span>
            </div>
            <p className="section-intro">
              Record real multi-window user actions across Excel, Slack, Terminal, or any desktop software.
              The apprenticeship engine captures interaction steps, masks credentials/PII, lifts concrete inputs into
              parameterized <code>$inputs</code>, and compiles deterministic DAG workflow specs.
            </p>

            {isRecording ? (
              <div className="recording-banner">
                <div className="recording-banner-left">
                  <span className="rec-blink-dot" />
                  <span>
                    RECORDING LIVE DEMONSTRATION · {currentSession?.title} ({currentSession?.process_name})
                  </span>
                </div>
                <div style={{ display: 'flex', gap: 8 }}>
                  <button className="button button-soft" onClick={handleStopRecording}>
                    <Square size={13} /> Finish Recording
                  </button>
                </div>
              </div>
            ) : (
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr auto', gap: 10, margin: '14px 0' }}>
                <label className="workflow-form" style={{ display: 'grid', gap: 4 }}>
                  <span className="eyebrow">DEMONSTRATION TITLE</span>
                  <input
                    value={newTraceTitle}
                    onChange={(e) => setNewTraceTitle(e.target.value)}
                    placeholder="e.g. Export Weekly Ledger & Follow Up"
                    style={{ padding: 8, borderRadius: 6, border: '1px solid #dce2d9', fontSize: 11 }}
                  />
                </label>
                <label className="workflow-form" style={{ display: 'grid', gap: 4 }}>
                  <span className="eyebrow">TARGET PROCESS</span>
                  <input
                    value={newTraceProcess}
                    onChange={(e) => setNewTraceProcess(e.target.value)}
                    placeholder="e.g. excel.exe, slack.exe"
                    style={{ padding: 8, borderRadius: 6, border: '1px solid #dce2d9', fontSize: 11 }}
                  />
                </label>
                <button
                  className="button button-primary"
                  style={{ alignSelf: 'end', height: 35 }}
                  onClick={handleStartRecording}
                >
                  <Play size={13} /> Start Recording Session
                </button>
              </div>
            )}

            {isRecording && (
              <div style={{ border: '1px solid #e1e7dc', borderRadius: 8, padding: 14, background: '#fafbfa', margin: '14px 0' }}>
                <div className="eyebrow">DEMONSTRATE INTERACTION STEPS</div>
                <p style={{ fontSize: 9, color: '#798578', margin: '4px 0 10px' }}>
                  Click below to log interaction steps or enter values. Parameter lifting automatically detects dates, emails, and numbers.
                </p>
                <div className="step-buttons-strip">
                  <button
                    className="step-quick-btn"
                    onClick={() => handleRecordEvent('click', 'Save & Export Button', null)}
                  >
                    <MousePointer size={12} /> Click "Export"
                  </button>
                  <button
                    className="step-quick-btn"
                    onClick={() => handleRecordEvent('type', 'Target Date Field', '2026-11-05')}
                  >
                    <Code size={12} /> Type Date "2026-11-05" (Lifts to $target_date)
                  </button>
                  <button
                    className="step-quick-btn"
                    onClick={() => handleRecordEvent('type', 'Contact Email Input', 'delegate@threadline.internal')}
                  >
                    <Code size={12} /> Type Email (Lifts to $contact_email)
                  </button>
                  <button
                    className="step-quick-btn"
                    onClick={() => handleRecordEvent('type', 'Password Input', 'SecretToken1234')}
                  >
                    <Lock size={12} /> Type Secret (Automatic PII Masking)
                  </button>
                  <button
                    className="step-quick-btn"
                    onClick={() => handleRecordEvent('hotkey', 'Keyboard Shortcut', 'Ctrl+S')}
                  >
                    <Terminal size={12} /> Hotkey "Ctrl+S"
                  </button>
                </div>

                <div className="eyebrow" style={{ marginTop: 12 }}>
                  RECORDED EVENTS IN CURRENT SESSION ({currentSession?.events?.length || 0})
                </div>
                {currentSession?.events?.length > 0 ? (
                  <table className="trace-event-table">
                    <thead>
                      <tr>
                        <th>Step</th>
                        <th>Type</th>
                        <th>Target Element</th>
                        <th>Value / Parameter</th>
                      </tr>
                    </thead>
                    <tbody>
                      {currentSession.events.map((ev) => (
                        <tr key={ev.step}>
                          <td>#{ev.step}</td>
                          <td><span className={`pill-type ${ev.type}`}>{ev.type}</span></td>
                          <td><strong>{ev.name}</strong></td>
                          <td><code>{ev.value || '-'}</code></td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                ) : (
                  <div style={{ padding: 12, textAlign: 'center', color: '#919b90', fontSize: 10 }}>
                    No steps recorded yet. Click one of the demonstrated interaction buttons above.
                  </div>
                )}
              </div>
            )}

            {/* Synthesized DAG Display */}
            {synthesizedWf && (
              <div style={{ marginTop: 16, padding: 14, background: '#f0f5ed', borderRadius: 8, border: '1px solid #d3e2cf' }}>
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 8 }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                    <Workflow size={16} color="#355e3b" />
                    <strong style={{ fontSize: 12, color: '#274b2e' }}>
                      Synthesized Workflow DAG: {synthesizedWf.spec?.name}
                    </strong>
                  </div>
                  <span className="sovereign-tab-badge">ID: {synthesizedWf.workflow_id}</span>
                </div>
                <div style={{ fontSize: 9, color: '#566e58', marginBottom: 8 }}>
                  Lifted Parameters: {synthesizedWf.lifted_inputs?.map((p) => <code key={p} style={{ margin: '0 4px', background: '#e1ede0', padding: '2px 4px', borderRadius: 3 }}>${p}</code>)}
                </div>
                <pre className="code-box" style={{ maxHeight: 180, background: '#1c261e' }}>
                  {JSON.stringify(synthesizedWf.spec, null, 2)}
                </pre>
              </div>
            )}

            {/* Past Recorded Traces */}
            <div style={{ marginTop: 20 }}>
              <div className="eyebrow">PAST DEMONSTRATION TRACES ({traces.length})</div>
              {traces.map((trc) => (
                <div
                  key={trc.id}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    padding: '10px 0',
                    borderTop: '1px solid #edf1eb',
                  }}
                >
                  <div>
                    <strong style={{ fontSize: 11, color: '#313f33' }}>{trc.title}</strong>
                    <div style={{ fontSize: 9, color: '#889487', marginTop: 2 }}>
                      {trc.window_title} ({trc.process_name}) · {trc.event_count} events · {trc.status}
                    </div>
                  </div>
                  <button
                    className="button button-soft"
                    style={{ fontSize: 9, padding: '5px 9px' }}
                    disabled={isSynthesizing}
                    onClick={() => handleSynthesizeDAG(trc.id)}
                  >
                    <Sparkles size={12} /> {trc.synthesized ? 'Re-synthesize DAG' : 'Synthesize DAG'}
                  </button>
                </div>
              ))}
            </div>
          </section>

          <aside className="sovereign-aside">
            <div className="policy-explainer">
              <div className="eyebrow">PARAMETER LIFTING</div>
              <h3>From Literal Actions to Reusable DAGs</h3>
              <p style={{ fontSize: 10, color: '#687367', lineHeight: 1.5, margin: '8px 0' }}>
                When you demonstrate an action like typing an email or picking a calendar slot, Sovereign lifts
                the literal constant into a typed input argument:
              </p>
              <div className="manifest-code">
                <span>inputs:</span>
                <b>target_date: string</b>
                <b>contact_email: string</b>
                <span>nodes:</span>
                <b>draft.follow_up: args: &quot;$inputs.contact_email&quot;</b>
                <b>verify_synthesis: type: verify</b>
              </div>
            </div>
          </aside>
        </div>
      )}

      {/* TAB 3: PROVABLE AUTONOMY & CONFORMAL RISK CONTROL (CRC) */}
      {activeTab === 'conformal' && (
        <div className="sovereign-panel-grid">
          <section className="sovereign-card">
            <div className="panel-head">
              <div>
                <div className="eyebrow">PILLAR 2: PROVABLE AUTONOMY</div>
                <h2>Finite-Sample Conformal Risk Control (CRC)</h2>
              </div>
              <span className="local-tag"><Scale size={13} /> Statistical Guarantees</span>
            </div>
            <p className="section-intro">
              Never rely on arbitrary model confidence scores. Under Conformal Risk Control, actions are only auto-executed
              if the non-conformity score <i>1 - p</i> falls below the empirically calibrated threshold &tau;&#770;, guaranteeing
              that the expected unapproved action rate satisfies <strong>E[Loss] &le; &alpha;</strong>.
            </p>

            {/* Alpha Slider Dial */}
            <div className="risk-budget-slider-box">
              <div className="risk-slider-header">
                <div>
                  <div className="eyebrow">SAFETY BUDGET (MAXIMUM ALLOWABLE ERROR CEILING &alpha;)</div>
                  <strong style={{ fontSize: 12, color: '#27362a' }}>
                    User-Selected Risk Ceiling: {(riskBudgetAlpha * 100).toFixed(1)}% Error Rate
                  </strong>
                </div>
                <div className="risk-dial-value">&alpha; = {Number(riskBudgetAlpha).toFixed(3)}</div>
              </div>
              <input
                type="range"
                min="0.005"
                max="0.10"
                step="0.005"
                className="risk-slider"
                value={riskBudgetAlpha}
                onChange={(e) => setRiskBudgetAlpha(Number(e.target.value))}
              />
              <div className="crc-guarantee-note">
                <ShieldCheck size={14} style={{ flexShrink: 0 }} />
                <span>
                  <strong>Mathematical Finite-Sample Bound:</strong> For calibration set size <i>n</i>, &tau;&#770; guarantees
                  unapproved actions occur in fewer than 1 out of {Math.round(1 / riskBudgetAlpha)} decisions.
                </span>
              </div>
            </div>

            {/* Active Action Policies Table */}
            <div style={{ marginTop: 16 }}>
              <div className="eyebrow">EMPIRICAL CALIBRATION & MARTINGALE DRIFT STATUS</div>
              <div style={{ display: 'grid', gap: 10, marginTop: 8 }}>
                {conformalStatus.map((pol) => (
                  <div key={pol.action_type} className="crc-policy-card">
                    <div className="crc-policy-row">
                      <div>
                        <strong style={{ fontSize: 11, color: '#253328' }}>
                          {pol.action_type.replace('_', ' ').toUpperCase()}
                        </strong>
                        <div style={{ fontSize: 9, color: '#828e81', marginTop: 2 }}>
                          Sample Size: <strong>{pol.sample_size}</strong> decisions · Empirical Risk: <strong>{(pol.empirical_risk * 100).toFixed(1)}%</strong>
                        </div>
                      </div>
                      <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                        <span className={`status-badge ${pol.status}`}>
                          {pol.status === 'calibrated' && <Check size={10} />}
                          {pol.status === 'drift_detected' && <AlertTriangle size={10} />}
                          {pol.status.replace('_', ' ').toUpperCase()}
                        </span>
                        <button
                          className="button button-soft"
                          style={{ fontSize: 9, padding: '4px 8px' }}
                          onClick={() => handleCalibrateConformal(pol.action_type)}
                        >
                          Calibrate (&alpha;={riskBudgetAlpha})
                        </button>
                      </div>
                    </div>
                    <div style={{ display: 'flex', gap: 14, fontSize: 8, color: '#7a8679', font: '8px var(--mono)', background: '#f8faf7', padding: '6px 8px', borderRadius: 4 }}>
                      <span>&tau;&#770; Threshold: <b>{pol.calibrated_tau ?? 'Collecting data'}</b></span>
                      <span>CUSUM Martingale Drift M<sub>t</sub>: <b>{pol.martingale_drift_statistic} / 3.5</b></span>
                      <span>Last Calibrated: <b>{pol.last_calibrated_at ? new Date(pol.last_calibrated_at).toLocaleTimeString() : 'Pending'}</b></span>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Interactive Gate Evaluator */}
            <div style={{ marginTop: 20, padding: 14, background: '#f9fbf8', border: '1px solid #e1e7dc', borderRadius: 8 }}>
              <div className="eyebrow">INTERACTIVE CRC GATE EVALUATOR</div>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr auto', gap: 10, margin: '10px 0' }}>
                <label style={{ display: 'grid', gap: 4, font: '8px var(--mono)', color: '#7b877a' }}>
                  ACTION TYPE
                  <select
                    value={evalActionType}
                    onChange={(e) => setEvalActionType(e.target.value)}
                    style={{ padding: 6, borderRadius: 5, border: '1px solid #dce2d9', background: '#fff' }}
                  >
                    <option value="create_reminder">create_reminder</option>
                    <option value="draft_reply">draft_reply</option>
                    <option value="calendar_export">calendar_export</option>
                  </select>
                </label>
                <label style={{ display: 'grid', gap: 4, font: '8px var(--mono)', color: '#7b877a' }}>
                  MODEL PREDICTED PROBABILITY: {evalProb}
                  <input
                    type="range"
                    min="0.50"
                    max="1.0"
                    step="0.01"
                    value={evalProb}
                    onChange={(e) => setEvalProb(Number(e.target.value))}
                  />
                </label>
                <button
                  className="button button-primary"
                  style={{ alignSelf: 'end', height: 32 }}
                  onClick={handleEvaluateGate}
                >
                  Evaluate CRC Gate
                </button>
              </div>

              {evalResult && (
                <div style={{
                  padding: 10,
                  borderRadius: 6,
                  background: evalResult.auto_execute ? '#eff7ed' : '#fcf3ee',
                  border: `1px solid ${evalResult.auto_execute ? '#cde0ca' : '#f1d7ce'}`,
                  color: evalResult.auto_execute ? '#2c5630' : '#a24c3e',
                  fontSize: 10,
                  display: 'flex',
                  alignItems: 'center',
                  gap: 8,
                }}>
                  {evalResult.auto_execute ? <CheckCircle2 size={16} /> : <AlertTriangle size={16} />}
                  <div>
                    <strong>{evalResult.auto_execute ? 'APPROVED FOR AUTONOMOUS EXECUTION' : 'ABSTAIN · ESCALATE TO USER APPROVAL'}</strong>
                    <div style={{ fontSize: 9, opacity: 0.9 }}>
                      Score: {evalResult.score} · Threshold: {evalResult.threshold ?? 'None'} · Reason: {evalResult.reason}
                    </div>
                  </div>
                </div>
              )}
            </div>
          </section>

          <aside className="sovereign-aside">
            <div className="policy-explainer">
              <div className="eyebrow">SEQUENTIAL DRIFT DETECTION</div>
              <h3>CUSUM Martingale Drift Alarm</h3>
              <p style={{ fontSize: 9, color: '#6a7669', lineHeight: 1.55 }}>
                Preferences drift over time. A CUSUM martingale accumulates deviations between predicted error and observed choices:
              </p>
              <div className="manifest-code">
                <span>M_t = max(0, M_(t-1) + (L_t - &alpha;) - &kappa;)</span>
                <span>Threshold: h = 3.5</span>
                <b>If M_t &gt; 3.5: Instant downshift to L1 Ask</b>
              </div>
              <p style={{ fontSize: 9, color: '#6a7669', lineHeight: 1.55, marginTop: 8 }}>
                This prevents the agent from continuing automatic actions if your preferences shift unexpectedly.
              </p>
            </div>
          </aside>
        </div>
      )}

{/* TAB 4: LEARNED PREFERENCE MODEL */}
      {activeTab === 'preferences' && (
        <div className="sovereign-panel-grid">
          <section className="sovereign-card">
            <div className="panel-head">
              <div>
                <div className="eyebrow">PILLAR 3: LEARNED MODEL OF YOU</div>
                <h2>Bayesian Preference Model & Active Uncertainty Elimination</h2>
              </div>
              <span className="local-tag"><Brain size={13} /> Active Learning</span>
            </div>
            <p className="section-intro">
              The Sovereign Delegate builds an online Bayesian model of your decision boundaries.
              Rather than interrupting you indiscriminately, it quantifies Shannon epistemic entropy <i>H(x)</i> and asks
              only strategic questions near the decision boundary to rapidly reduce uncertainty.
            </p>

            {/* Active Learning Questions */}
            <div style={{ marginTop: 14 }}>
              <div className="eyebrow">STRATEGIC ACTIVE LEARNING QUERIES ({activeQueries.length})</div>
              {activeQueries.length > 0 ? (
                activeQueries.map((q, i) => (
                  <div key={i} className="query-card">
                    <div className="query-card-header">
                      <strong style={{ fontSize: 10, color: '#273429' }}>
                        High-Entropy Decision Boundary ({q.action_type})
                      </strong>
                      <span className="entropy-meter">
                        <Flame size={10} /> Epistemic Entropy: {q.entropy} bits
                      </span>
                    </div>
                    <p>{q.question}</p>
                    <div className="query-actions">
                      <button
                        className="button button-soft"
                        onClick={() => handleAnswerActiveQuery(q, false)}
                      >
                        <X size={12} /> Decline (Reject Preference)
                      </button>
                      <button
                        className="button button-primary"
                        onClick={() => handleAnswerActiveQuery(q, true)}
                      >
                        <Check size={12} /> Approve (Accept Preference)
                      </button>
                    </div>
                  </div>
                ))
              ) : (
                <div className="quiet-empty" style={{ margin: '10px 0' }}>
                  <span className="quiet-check"><Check size={15} /></span>
                  <div>
                    <strong>Epistemic uncertainty minimized.</strong>
                    <p>Current decision boundaries are well-separated across tested contexts.</p>
                  </div>
                </div>
              )}
            </div>

            {/* Bayesian Weights Visualization */}
            <div style={{ marginTop: 20 }}>
              <div className="eyebrow">ONLINE BAYESIAN WEIGHT VECTOR (x &isin; &reals;<sup>8</sup>)</div>
              <div className="weights-list">
                {prefStatus?.feature_names?.map((name, idx) => {
                  const w = prefStatus?.weights?.[idx] ?? 0;
                  const isPos = w >= 0;
                  const absVal = Math.min(100, Math.abs(w) * 35);
                  return (
                    <div key={name} className="weight-row">
                      <span style={{ color: '#576559', fontWeight: 550 }}>{name}</span>
                      <div className="weight-bar-track">
                        <div
                          className={`weight-bar-fill ${isPos ? 'pos' : 'neg'}`}
                          style={{ width: `${absVal}%` }}
                        />
                      </div>
                      <span style={{ textAlign: 'right', font: '600 8px var(--mono)', color: isPos ? '#3b6f43' : '#b24f3e' }}>
                        {w > 0 ? `+${w}` : w}
                      </span>
                    </div>
                  );
                })}
              </div>
            </div>

            {/* Interactive Decision Simulator */}
            <div style={{ marginTop: 20, padding: 14, background: '#f8faf7', border: '1px solid #e2e8df', borderRadius: 8 }}>
              <div className="eyebrow">TEST CONTEXTUAL PREDICTION</div>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr auto', gap: 10, margin: '10px 0' }}>
                <select
                  value={predictAction}
                  onChange={(e) => setPredictAction(e.target.value)}
                  style={{ padding: 6, borderRadius: 5, border: '1px solid #dce2d9', background: '#fff' }}
                >
                  <option value="create_reminder">create_reminder</option>
                  <option value="draft_reply">draft_reply</option>
                  <option value="calendar_export">calendar_export</option>
                </select>
                <select
                  value={predictLifeArea}
                  onChange={(e) => setPredictLifeArea(e.target.value)}
                  style={{ padding: 6, borderRadius: 5, border: '1px solid #dce2d9', background: '#fff' }}
                >
                  <option value="work">Work Life Area</option>
                  <option value="personal">Personal Life Area</option>
                  <option value="family">Family Life Area</option>
                </select>
                <button className="button button-soft" onClick={handlePredictApproval}>
                  Predict
                </button>
              </div>

              {predictResult && (
                <div style={{ fontSize: 9, font: 'var(--mono)', color: '#455648', background: '#edf3ec', padding: 8, borderRadius: 5 }}>
                  Predicted Approval Probability: <strong>{(predictResult.predicted_prob * 100).toFixed(1)}%</strong> ·
                  Logit: {predictResult.logit} · Entropy: {predictResult.uncertainty_entropy} bits ·
                  Confident: {predictResult.is_confident ? 'YES' : 'UNCERTAIN'}
                </div>
              )}
            </div>
          </section>

          <aside className="sovereign-aside">
            <div className="policy-explainer">
              <div className="eyebrow">ACTIVE LEARNING</div>
              <h3>Maximum Value of Information</h3>
              <p style={{ fontSize: 9, color: '#687367', lineHeight: 1.55 }}>
                Instead of constant confirmation dialogs, Sovereign queries you only when the epistemic entropy is maximal:
              </p>
              <div className="manifest-code">
                <span>H(p) = -p log₂(p) - (1-p) log₂(1-p)</span>
                <b>Trigger active question if H(p) &gt; 0.70 bits</b>
              </div>
              <p style={{ fontSize: 9, color: '#687367', lineHeight: 1.55, marginTop: 8 }}>
                Every answer performs a Bayesian regularized gradient step, tightening the decision boundary permanently.
              </p>
            </div>
          </aside>
        </div>
      )}

{/* TAB 5: SELF-EXTENSION STUDIO */}
      {activeTab === 'synthesizer' && (
        <div className="sovereign-panel-grid">
          <section className="sovereign-card">
            <div className="panel-head">
              <div>
                <div className="eyebrow">PILLAR 4: SELF-EXTENSION</div>
                <h2>Autonomous Tool Synthesis & Sandbox Verification</h2>
              </div>
              <span className="local-tag"><Code size={13} /> Self-Programming Runtime</span>
            </div>
            <p className="section-intro">
              When a workflow requires a capability beyond built-in tools, Sovereign programs a new Python tool,
              synthesizes its inverse saga rollback handler for reversibility, proves safety inside an isolated sandbox,
              and dynamically registers it into <code>TOOL_MANIFESTS</code>.
            </p>

            {/* Synthesize New Tool Form */}
            <form onSubmit={handleSynthesizeNewTool} style={{ border: '1px solid #e1e7dc', borderRadius: 8, padding: 14, background: '#fafbfa', margin: '14px 0' }}>
              <div className="eyebrow">SYNTHESIZE NEW AGENT CAPABILITY</div>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10, margin: '8px 0' }}>
                <label className="workflow-form" style={{ display: 'grid', gap: 4 }}>
                  <span className="eyebrow">TOOL IDENTIFIER</span>
                  <input
                    value={newToolName}
                    onChange={(e) => setNewToolName(e.target.value)}
                    placeholder="e.g. crypto.verify_checksum"
                    required
                    style={{ padding: 8, borderRadius: 5, border: '1px solid #dce2d9', fontSize: 11 }}
                  />
                </label>
                <label className="workflow-form" style={{ display: 'grid', gap: 4 }}>
                  <span className="eyebrow">OPERATION TYPE</span>
                  <select
                    value={newToolOp}
                    onChange={(e) => setNewToolOp(e.target.value)}
                    style={{ padding: 8, borderRadius: 5, border: '1px solid #dce2d9', fontSize: 11, background: '#fff' }}
                  >
                    <option value="computation">Deterministic Computation</option>
                    <option value="formatting">Formatting & Text Sanitization</option>
                  </select>
                </label>
              </div>
              <label className="workflow-form" style={{ display: 'grid', gap: 4, margin: '6px 0' }}>
                <span className="eyebrow">TOOL CAPABILITY SPECIFICATION</span>
                <input
                  value={newToolDesc}
                  onChange={(e) => setNewToolDesc(e.target.value)}
                  placeholder="Describe what the synthesized tool should calculate or verify"
                  required
                  style={{ padding: 8, borderRadius: 5, border: '1px solid #dce2d9', fontSize: 11 }}
                />
              </label>
              <button
                type="submit"
                className="button button-primary"
                disabled={synthesizingTool}
                style={{ marginTop: 8 }}
              >
                <Terminal size={13} /> {synthesizingTool ? 'Synthesizing & Sandbox Testing...' : 'Synthesize, Verify & Inject Tool'}
              </button>
            </form>

            {/* Synthesized Tools List */}
            <div style={{ marginTop: 20 }}>
              <div className="eyebrow">REGISTERED SYNTHESIZED TOOLS ({synthesizedTools.length})</div>
              <div style={{ display: 'grid', gap: 10, marginTop: 10 }}>
                {synthesizedTools.map((tool) => (
                  <div
                    key={tool.id}
                    style={{
                      padding: 12,
                      border: '1px solid #e3e8df',
                      borderRadius: 8,
                      background: selectedTool?.id === tool.id ? '#f3f8f1' : '#ffffff',
                      cursor: 'pointer',
                    }}
                    onClick={() => setSelectedTool(tool)}
                  >
                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                        <Terminal size={14} color="#355e3b" />
                        <strong style={{ fontSize: 11, color: '#27382a' }}>{tool.name}</strong>
                      </div>
                      <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                        <span className="status-badge calibrated">
                          <Check size={10} /> Sandbox Verified
                        </span>
                        <button
                          className="button button-soft"
                          style={{ fontSize: 8, padding: '3px 7px' }}
                          onClick={(e) => {
                            e.stopPropagation();
                            handleVerifyTool(tool.id);
                          }}
                        >
                          Re-test
                        </button>
                      </div>
                    </div>
                    <p style={{ margin: '4px 0 0', fontSize: 9, color: '#7a8678' }}>{tool.description}</p>
                  </div>
                ))}
              </div>
            </div>

            {/* Selected Tool Code Viewer */}
            {selectedTool && (
              <div style={{ marginTop: 20, padding: 14, background: '#1c241e', borderRadius: 8, color: '#d2e2d4' }}>
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 8 }}>
                  <span className="eyebrow" style={{ color: '#90a894' }}>
                    SYNTHESIZED SOURCE CODE: {selectedTool.name}
                  </span>
                  <span style={{ fontSize: 8, color: '#88a38c' }}>MANIFEST REGISTERED</span>
                </div>
                <pre className="code-box" style={{ margin: 0, maxHeight: 160 }}>
                  {selectedTool.source_code || '# Source code generated inside sandbox runtime'}
                </pre>
                <div className="eyebrow" style={{ color: '#90a894', marginTop: 12 }}>
                  INVERSE SAGA ROLLBACK HANDLER (COMPENSATION)
                </div>
                <pre className="code-box" style={{ margin: '6px 0 0', maxHeight: 100 }}>
                  {selectedTool.inverse_code || 'def inverse_handler(output):\n    return {"rolled_back": True}'}
                </pre>
              </div>
            )}
          </section>

          <aside className="sovereign-aside">
            <div className="policy-explainer">
              <div className="eyebrow">REVERSIBLE BY DESIGN</div>
              <h3>Inverse Saga Handlers</h3>
              <p style={{ fontSize: 9, color: '#687367', lineHeight: 1.55 }}>
                Every tool generated by Sovereign is paired with an inverse compensation handler.
              </p>
              <div className="manifest-code">
                <span>def handler(args):</span>
                <b># Forward execution</b>
                <span>def inverse_handler(output):</span>
                <b># Inverse rollback</b>
              </div>
              <p style={{ fontSize: 9, color: '#687367', lineHeight: 1.55, marginTop: 8 }}>
                If a multi-step workflow fails verification midway, the engine automatically walks backwards
                and rolls back all preceding steps.
              </p>
            </div>
          </aside>
        </div>
      )}

{/* TAB 6: CAUSAL WORLD MODEL & HORIZON */}
      {activeTab === 'world_model' && (
        <div className="sovereign-panel-grid">
          <section className="sovereign-card">
            <div className="panel-head">
              <div>
                <div className="eyebrow">PILLAR 5: LIFELONG CAUSAL WORLD MODEL</div>
                <h2>7-Day Horizon Rehearsal & N-of-1 Personal Causal Trials</h2>
              </div>
              <span className="local-tag"><Network size={13} /> Provenance Knowledge</span>
            </div>
            <p className="section-intro">
              Separates what actually helps from coincidence using Rubin&apos;s potential outcomes causal model, maintains
              auditable knowledge triples linked to source files, and rehearses your upcoming 7 days to surface schedule
              bottlenecks before they happen.
            </p>

            {/* 7-Day Horizon Simulation */}
            <div style={{ marginTop: 14 }}>
              <div className="panel-head" style={{ marginBottom: 6 }}>
                <div className="eyebrow">FORWARD 7-DAY WORKLOAD HORIZON</div>
                <span style={{ fontSize: 9, color: '#697a6a' }}>
                  {horizonForecast?.morning_recommendation || 'Analyzing horizon...'}
                </span>
              </div>
              <div className="horizon-chart">
                {horizonForecast?.forecast?.map((day) => (
                  <div key={day.date} className="horizon-day-col">
                    <span className="horizon-day-load">{day.workload_score}</span>
                    <div className="horizon-bar-wrap">
                      <div
                        className={`horizon-bar-fill ${day.risk_level}`}
                        style={{ height: `${Math.max(10, day.workload_score)}%` }}
                        title={`${day.day_name}: ${day.commitments_due} due, ${day.accumulated_overdue} overdue`}
                      />
                    </div>
                    <span className="horizon-day-name">{day.day_name.slice(0, 3)}</span>
                    <small style={{ fontSize: 7, color: '#919b90' }}>{day.date.slice(5)}</small>
                  </div>
                ))}
              </div>
            </div>

            {/* N-of-1 Causal Trials */}
            <div style={{ marginTop: 20 }}>
              <div className="eyebrow">N-OF-1 PERSONAL CAUSAL TRIALS (RUBIN POTENTIAL OUTCOMES)</div>
              <form onSubmit={handleRunCausalTrial} style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr auto', gap: 8, margin: '8px 0' }}>
                <input
                  value={newTrialName}
                  onChange={(e) => setNewTrialName(e.target.value)}
                  placeholder="Trial Name"
                  required
                  style={{ padding: 6, borderRadius: 5, border: '1px solid #dce2d9', fontSize: 10 }}
                />
                <input
                  value={newTrialIntervention}
                  onChange={(e) => setNewTrialIntervention(e.target.value)}
                  placeholder="Intervention (e.g. 2h Delay)"
                  required
                  style={{ padding: 6, borderRadius: 5, border: '1px solid #dce2d9', fontSize: 10 }}
                />
                <input
                  value={newTrialMetric}
                  onChange={(e) => setNewTrialMetric(e.target.value)}
                  placeholder="Outcome Metric"
                  required
                  style={{ padding: 6, borderRadius: 5, border: '1px solid #dce2d9', fontSize: 10 }}
                />
                <button type="submit" className="button button-soft" style={{ fontSize: 9 }}>
                  Evaluate ATE
                </button>
              </form>

              <div style={{ display: 'grid', gap: 8, marginTop: 10 }}>
                {causalTrials.map((t) => (
                  <div key={t.id} style={{ padding: 10, border: '1px solid #e4eae0', borderRadius: 6, background: '#fafbfa' }}>
                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                      <strong style={{ fontSize: 10, color: '#273429' }}>{t.name}</strong>
                      <span className="status-badge calibrated">
                        ATE: {t.causal_effect > 0 ? `+${t.causal_effect}` : t.causal_effect} (p &le; {t.p_value})
                      </span>
                    </div>
                    <div style={{ fontSize: 9, color: '#687767', marginTop: 4 }}>
                      Intervention: <i>{t.intervention}</i> &rarr; Metric: <i>{t.outcome_metric}</i>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Provenance Triples */}
            <div style={{ marginTop: 20 }}>
              <div className="eyebrow">AUDITABLE BELIEF TRIPLES ({triples.length})</div>
              <form onSubmit={handleAddTriple} style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr auto', gap: 8, margin: '8px 0' }}>
                <input
                  value={newTripleSubj}
                  onChange={(e) => setNewTripleSubj(e.target.value)}
                  placeholder="Subject (e.g. Client)"
                  required
                  style={{ padding: 6, borderRadius: 5, border: '1px solid #dce2d9', fontSize: 10 }}
                />
                <input
                  value={newTriplePred}
                  onChange={(e) => setNewTriplePred(e.target.value)}
                  placeholder="Predicate (e.g. requires)"
                  required
                  style={{ padding: 6, borderRadius: 5, border: '1px solid #dce2d9', fontSize: 10 }}
                />
                <input
                  value={newTripleObj}
                  onChange={(e) => setNewTripleObj(e.target.value)}
                  placeholder="Object (e.g. NDA)"
                  required
                  style={{ padding: 6, borderRadius: 5, border: '1px solid #dce2d9', fontSize: 10 }}
                />
                <button type="submit" className="button button-primary" style={{ fontSize: 9 }}>
                  <Plus size={11} /> Assert Belief
                </button>
              </form>

              <div style={{ display: 'grid', gap: 6, marginTop: 10, maxHeight: 180, overflowY: 'auto' }}>
                {triples.map((trip) => (
                  <div key={trip.id} style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '6px 8px', borderBottom: '1px solid #edf1eb', fontSize: 9 }}>
                    <div>
                      <strong style={{ color: '#27382a' }}>{trip.subject}</strong>
                      <span style={{ color: '#7a8779', margin: '0 6px' }}>&mdash;[{trip.predicate}]&rarr;</span>
                      <strong style={{ color: '#38533b' }}>{trip.object}</strong>
                    </div>
                    <span style={{ font: '8px var(--mono)', color: '#889487' }}>
                      {trip.confidence * 100}% conf
                    </span>
                  </div>
                ))}
              </div>
            </div>
          </section>

          <aside className="sovereign-aside">
            <div className="policy-explainer">
              <div className="eyebrow">AUDITABLE DELETION</div>
              <h3>Source-Linked Cascade</h3>
              <p style={{ fontSize: 9, color: '#687367', lineHeight: 1.55 }}>
                Every belief in the knowledge graph is linked to a source document ID.
              </p>
              <div className="manifest-code">
                <span>ON DELETE CASCADE:</span>
                <b>DELETE FROM world_model_triples</b>
                <b>WHERE source_id = deleted.id</b>
              </div>
              <p style={{ fontSize: 9, color: '#687367', lineHeight: 1.55, marginTop: 8 }}>
                When you remove an imported source file, all downstream beliefs and open loops extracted from it
                are automatically erased from the world model.
              </p>
            </div>
          </aside>
        </div>
      )}

      {/* TAB 6: UNIVERSAL MCP & APP CONNECTORS STUDIO */}
      {activeTab === 'connectors' && (
        <div className="sovereign-panel-grid">
          <section className="sovereign-card">
            <div className="panel-head">
              <div>
                <div className="eyebrow">MODEL CONTEXT PROTOCOL & UNIVERSAL APPS</div>
                <h2>Connected MCP Servers & Tools Studio</h2>
              </div>
              <span className="local-tag">
                <Link2 size={13} /> {connectors.length} Connected · {allTools.length} Tools Live
              </span>
            </div>
            <p className="section-intro">
              The Sovereign Substrate unifies Model Context Protocol (MCP) servers, third-party app connectors,
              built-in workflow tools, and runtime-synthesized tools into a single sandbox execution substrate.
            </p>

            {/* Active Connectors Grid */}
            <div style={{ marginTop: 14 }}>
              <div className="eyebrow" style={{ marginBottom: 8 }}>
                ACTIVE EXTERNAL CONNECTORS & MCP SERVERS ({connectors.length})
              </div>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: 10 }}>
                {connectors.map((c) => (
                  <div
                    key={c.id}
                    style={{
                      padding: 12,
                      border: '1px solid #dce4da',
                      borderRadius: 8,
                      background: c.enabled ? '#ffffff' : '#f5f7f4',
                      opacity: c.enabled ? 1 : 0.65,
                      display: 'flex',
                      flexDirection: 'column',
                      justifyContent: 'space-between',
                    }}
                  >
                    <div>
                      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                        <strong style={{ fontSize: 12, color: '#1f2e21' }}>{c.display_name}</strong>
                        <span
                          style={{
                            font: '600 8px var(--mono)',
                            padding: '2px 6px',
                            borderRadius: 4,
                            background: c.enabled ? '#dcf3de' : '#ecefe9',
                            color: c.enabled ? '#22602e' : '#687768',
                          }}
                        >
                          {c.enabled ? 'ACTIVE' : 'DISABLED'}
                        </span>
                      </div>
                      <p style={{ fontSize: 9, color: '#5b695a', margin: '6px 0 10px', lineHeight: 1.4 }}>
                        {c.description}
                      </p>
                      <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
                        {(c.tools || []).map((t) => (
                          <span
                            key={t.name}
                            style={{
                              font: '8px var(--mono)',
                              background: '#f0f5ed',
                              color: '#38533b',
                              border: '1px solid #d4ded1',
                              borderRadius: 4,
                              padding: '2px 5px',
                            }}
                          >
                            {t.name}
                          </span>
                        ))}
                      </div>
                    </div>
                    <div style={{ marginTop: 10, display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                      <span style={{ fontSize: 8, color: '#7a8a79', fontStyle: 'italic' }}>Kind: {c.kind}</span>
                      <button
                        className="button button-soft"
                        onClick={() => handleToggleConnector(c.id)}
                        style={{ fontSize: 9, padding: '3px 8px' }}
                      >
                        {c.enabled ? 'Disable' : 'Enable'}
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Live Tool Invocation Runner */}
            <div style={{ marginTop: 24, padding: 14, border: '1px solid #d6e2d3', borderRadius: 8, background: '#f8faf7' }}>
              <div className="panel-head" style={{ marginBottom: 10 }}>
                <div>
                  <div className="eyebrow">INTERACTIVE TOOL RUNNER</div>
                  <h3 style={{ fontSize: 13, margin: '2px 0' }}>Execute Any Registered Tool</h3>
                </div>
                <span className="local-tag" style={{ background: '#e5efe2' }}>
                  <Zap size={11} /> Universal Substrate Caller
                </span>
              </div>
              <p style={{ fontSize: 9, color: '#687767', marginBottom: 10 }}>
                Test any tool in real-time. The Sovereign Substrate applies Conformal Risk gating and isolates execution.
              </p>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
                <div>
                  <label style={{ display: 'block', fontSize: 9, fontWeight: 600, color: '#27382a', marginBottom: 4 }}>
                    SELECT TOOL ({allTools.length} TOTAL)
                  </label>
                  <select
                    value={selectedToolForRun}
                    onChange={(e) => handleSelectToolSample(e.target.value)}
                    style={{
                      width: '100%',
                      padding: 7,
                      borderRadius: 6,
                      border: '1px solid #d0dcce',
                      fontSize: 10,
                      fontFamily: 'var(--mono)',
                      background: '#ffffff',
                    }}
                  >
                    <optgroup label="MCP Connectors (GitHub, GSuite, Slack, FS, DB, Web)">
                      {allTools.filter((t) => t.category === 'mcp_connector').map((t) => (
                        <option key={t.name} value={t.name}>
                          {t.name} — {t.connector_name}
                        </option>
                      ))}
                    </optgroup>
                    <optgroup label="Synthesized Tools (Pillar 4)">
                      {allTools.filter((t) => t.category === 'synthesized').map((t) => (
                        <option key={t.name} value={t.name}>
                          {t.name} (Custom Synthesized)
                        </option>
                      ))}
                    </optgroup>
                    <optgroup label="Built-in Workflow Tools">
                      {allTools.filter((t) => t.category === 'built_in').map((t) => (
                        <option key={t.name} value={t.name}>
                          {t.name} (Built-in)
                        </option>
                      ))}
                    </optgroup>
                  </select>

                  <div style={{ marginTop: 8 }}>
                    <label style={{ display: 'block', fontSize: 9, fontWeight: 600, color: '#27382a', marginBottom: 4 }}>
                      ARGUMENTS (JSON)
                    </label>
                    <textarea
                      rows={5}
                      value={toolArgsJson}
                      onChange={(e) => setToolArgsJson(e.target.value)}
                      style={{
                        width: '100%',
                        fontFamily: 'var(--mono)',
                        fontSize: 9,
                        padding: 8,
                        borderRadius: 6,
                        border: '1px solid #d0dcce',
                        background: '#ffffff',
                        resize: 'vertical',
                      }}
                    />
                  </div>

                  <div style={{ marginTop: 10, display: 'flex', gap: 6 }}>
                    <button
                      className="button button-primary"
                      onClick={handleRunToolTest}
                      disabled={isToolRunning}
                      style={{ fontSize: 10 }}
                    >
                      <Play size={12} /> {isToolRunning ? 'Executing...' : 'Run Tool'}
                    </button>
                    <button
                      className="button button-soft"
                      onClick={() => handleSelectToolSample(selectedToolForRun)}
                      style={{ fontSize: 10 }}
                    >
                      Reset Sample Args
                    </button>
                  </div>
                </div>

                {/* Output Console */}
                <div>
                  <label style={{ display: 'block', fontSize: 9, fontWeight: 600, color: '#27382a', marginBottom: 4 }}>
                    EXECUTION RESULT
                  </label>
                  <pre
                    style={{
                      height: 162,
                      overflowY: 'auto',
                      padding: 10,
                      borderRadius: 6,
                      background: '#121a14',
                      color: '#95e0a0',
                      fontSize: 9,
                      fontFamily: 'var(--mono)',
                      lineHeight: 1.45,
                      border: '1px solid #233426',
                    }}
                  >
                    {toolRunOutput
                      ? JSON.stringify(toolRunOutput, null, 2)
                      : '// Tool output will appear here after execution...'}
                  </pre>
                </div>
              </div>
            </div>

            {/* Register New Custom MCP Server */}
            <div style={{ marginTop: 20 }}>
              <div className="eyebrow">EXTENSIBILITY</div>
              <h3 style={{ fontSize: 12, margin: '2px 0 8px' }}>Register Custom MCP Server or Connector</h3>
              <form
                onSubmit={handleRegisterConnector}
                style={{
                  display: 'grid',
                  gridTemplateColumns: '1fr 1fr 120px 1.5fr auto',
                  gap: 8,
                  alignItems: 'center',
                }}
              >
                <input
                  placeholder="ID (e.g. jira_mcp)"
                  value={newConnName}
                  onChange={(e) => setNewConnName(e.target.value)}
                  required
                  style={{ padding: 6, borderRadius: 5, border: '1px solid #dce2d9', fontSize: 10 }}
                />
                <input
                  placeholder="Display Name (e.g. Jira MCP)"
                  value={newConnDisplayName}
                  onChange={(e) => setNewConnDisplayName(e.target.value)}
                  required
                  style={{ padding: 6, borderRadius: 5, border: '1px solid #dce2d9', fontSize: 10 }}
                />
                <select
                  value={newConnKind}
                  onChange={(e) => setNewConnKind(e.target.value)}
                  style={{ padding: 6, borderRadius: 5, border: '1px solid #dce2d9', fontSize: 10 }}
                >
                  <option value="mcp_stdio">mcp_stdio</option>
                  <option value="mcp_sse">mcp_sse</option>
                  <option value="app_connector">app_connector</option>
                </select>
                <input
                  placeholder="Description..."
                  value={newConnDesc}
                  onChange={(e) => setNewConnDesc(e.target.value)}
                  style={{ padding: 6, borderRadius: 5, border: '1px solid #dce2d9', fontSize: 10 }}
                />
                <button type="submit" className="button button-primary" style={{ fontSize: 9 }}>
                  <Plus size={11} /> Register
                </button>
              </form>
            </div>
          </section>

          <aside className="sovereign-aside">
            <div className="policy-explainer">
              <div className="eyebrow">SANDBOX ISOLATION</div>
              <h3>MCP Security Contract</h3>
              <p style={{ fontSize: 9, color: '#687367', lineHeight: 1.55 }}>
                External MCP tools run inside verified isolation boundaries. Read-only limits prevent accidental data loss.
              </p>
              <div className="manifest-code">
                <span>SQL BOUNDARY:</span>
                <b>Only SELECT statements allowed</b>
                <span style={{ marginTop: 4 }}>FILESYSTEM BOUNDARY:</span>
                <b>Local directory sandboxing</b>
                <span style={{ marginTop: 4 }}>DATA MINIMIZATION:</span>
                <b>Egress hash receipts generated</b>
              </div>
              <p style={{ fontSize: 9, color: '#687367', lineHeight: 1.55, marginTop: 8 }}>
                Every tool invocation is audited with execution timestamps and stored in the SQLite provenance record.
              </p>
            </div>
          </aside>
        </div>
      )}

      {/* TAB 7: COMPUTER-USE AGENT & 4-RUNG ACTION LADDER */}
      {activeTab === 'device' && (
        <div className="sovereign-panel-grid">
          <section className="sovereign-card">
            <div className="panel-head">
              <div>
                <div className="eyebrow">COMPUTER-USE SUBSTRATE · ACTION LADDER</div>
                <h2>Computer-Use Agent & Action Ladder</h2>
              </div>
              <span className="local-tag" style={{ background: '#daf3ec', color: '#165746' }}>
                <Folder size={13} /> 4 Rungs · Postcondition Contracts · Reversible Inverses
              </span>
            </div>
            <p className="section-intro">
              Instead of slow, fragile pixel-only clicking, the agent ascends the <strong>4-Rung Action Ladder</strong>: attempting the cheapest, most deterministic method first (Direct API/CLI), falling back to Accessibility trees & DOM, and using Vision only when necessary, with Human-in-the-Loop checkpoints for high-risk actions.
            </p>

            {/* The 4-Rung Action Ladder Hierarchy */}
            <div style={{ marginTop: 14 }}>
              <div className="eyebrow" style={{ marginBottom: 8 }}>THE 4-RUNG ACTION LADDER</div>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: 10 }}>
                <div style={{ padding: 12, border: '1px solid #d3e7df', borderRadius: 8, background: '#f5fbf9' }}>
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                    <strong style={{ fontSize: 11, color: '#165746' }}>Rung 1: Direct API & CLI</strong>
                    <span style={{ fontSize: 7, font: '600 7px var(--mono)', padding: '2px 5px', borderRadius: 3, background: '#d5f2e8', color: '#135443' }}>FASTEST (5-50ms)</span>
                  </div>
                  <p style={{ fontSize: 9, color: '#566e66', margin: '6px 0 8px', lineHeight: 1.4 }}>
                    Direct filesystem writes, shell commands, SQLite queries. 99.9% deterministic. Cost: $0.00.
                  </p>
                  <div style={{ fontSize: 8, font: 'var(--mono)', color: '#437c6d' }}>
                    Boundary: Sandboxed to ./data/workspace
                  </div>
                </div>

                <div style={{ padding: 12, border: '1px solid #dce4da', borderRadius: 8, background: '#f7f9f6' }}>
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                    <strong style={{ fontSize: 11, color: '#27382a' }}>Rung 2: OS A11y Tree & DOM</strong>
                    <span style={{ fontSize: 7, font: '600 7px var(--mono)', padding: '2px 5px', borderRadius: 3, background: '#e3ebe1', color: '#314c35' }}>STRUCTURED (100-300ms)</span>
                  </div>
                  <p style={{ fontSize: 9, color: '#5b695a', margin: '6px 0 8px', lineHeight: 1.4 }}>
                    Win32 UI Automation, Browser DOM, named element handles. 96% reliable. No pixel guessing.
                  </p>
                  <div style={{ fontSize: 8, font: 'var(--mono)', color: '#4b644f' }}>
                    Targeting: Selectors & accessible names
                  </div>
                </div>

                <div style={{ padding: 12, border: '1px solid #e2ded7', borderRadius: 8, background: '#faf8f5' }}>
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                    <strong style={{ fontSize: 11, color: '#544634' }}>Rung 3: Vision Coordinates</strong>
                    <span style={{ fontSize: 7, font: '600 7px var(--mono)', padding: '2px 5px', borderRadius: 3, background: '#f3ece2', color: '#6d5334' }}>FALLBACK (800-2500ms)</span>
                  </div>
                  <p style={{ fontSize: 9, color: '#6e6152', margin: '6px 0 8px', lineHeight: 1.4 }}>
                    Screen capture, OCR, coordinate clicking (x,y). For non-standard canvas and games.
                  </p>
                  <div style={{ fontSize: 8, font: 'var(--mono)', color: '#7a664e' }}>
                    Requires: Screenshot verification
                  </div>
                </div>

                <div style={{ padding: 12, border: '1px solid #e7d8d5', borderRadius: 8, background: '#fbf7f6' }}>
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                    <strong style={{ fontSize: 11, color: '#5b2b25' }}>Rung 4: Human-in-the-Loop</strong>
                    <span style={{ fontSize: 7, font: '600 7px var(--mono)', padding: '2px 5px', borderRadius: 3, background: '#f8e0dc', color: '#882d22' }}>SAFETY GATE</span>
                  </div>
                  <p style={{ fontSize: 9, color: '#735753', margin: '6px 0 8px', lineHeight: 1.4 }}>
                    Mandatory for external messaging, financial actions, OTPs, or uncertain conformal scores.
                  </p>
                  <div style={{ fontSize: 8, font: 'var(--mono)', color: '#883b30' }}>
                    Policy: L1 approval with draft preview
                  </div>
                </div>
              </div>
            </div>

            {/* 3 Exemplar Tasks Live Execution Cards */}
            <div style={{ marginTop: 20 }}>
              <div className="eyebrow" style={{ marginBottom: 8 }}>3 EXEMPLAR TASKS (LIVE 1-CLICK TEST RUNNERS)</div>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: 10 }}>
                {/* Exemplar 1: Filesystem */}
                <div style={{ padding: 12, border: '1px solid #cfe2db', borderRadius: 8, background: '#ffffff', display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>
                  <div>
                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                      <strong style={{ fontSize: 11, color: '#165746' }}>1. Create Folder & Files</strong>
                      <span style={{ fontSize: 7, font: '600 7px var(--mono)', background: '#d5f2e8', color: '#135443', padding: '1px 5px', borderRadius: 3 }}>EASY · RUNG 1</span>
                    </div>
                    <p style={{ fontSize: 9, color: '#566e66', margin: '6px 0', lineHeight: 1.4 }}>
                      "Create a project workspace with README.md, config.json, and src/index.js".
                    </p>
                    <div style={{ fontSize: 8, color: '#38533b', font: 'var(--mono)', background: '#f1f8f5', padding: '4px 6px', borderRadius: 4 }}>
                      Postconditions: dir exists &middot; files exist &middot; checksums match &middot; undo ready
                    </div>
                  </div>
                  <div style={{ marginTop: 10, display: 'flex', gap: 6 }}>
                    <button
                      className="button button-primary"
                      onClick={() => handleRunDeviceGoal('Create a project workspace with README and config', 'filesystem', { folder_name: 'demo_workspace' })}
                      disabled={isDeviceRunning}
                      style={{ fontSize: 9, padding: '4px 9px' }}
                    >
                      <Play size={10} /> Run Rung 1 Task
                    </button>
                  </div>
                </div>

                {/* Exemplar 2: WhatsApp / Messaging */}
                <div style={{ padding: 12, border: '1px solid #dce4da', borderRadius: 8, background: '#ffffff', display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>
                  <div>
                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                      <strong style={{ fontSize: 11, color: '#27382a' }}>2. WhatsApp / Chat Delegate</strong>
                      <span style={{ fontSize: 7, font: '600 7px var(--mono)', background: '#fdf1dc', color: '#a07127', padding: '1px 5px', borderRadius: 3 }}>MEDIUM · RUNG 2/4</span>
                    </div>
                    <p style={{ fontSize: 9, color: '#5b695a', margin: '6px 0', lineHeight: 1.4 }}>
                      "Open WhatsApp and chat with Jordan: 'Can we sync on the design review tomorrow at 2 PM?'".
                    </p>
                    <div style={{ fontSize: 8, color: '#68543a', font: 'var(--mono)', background: '#faf5ec', padding: '4px 6px', borderRadius: 4 }}>
                      Safety: L1 Mandatory Human Approval &middot; Inbound Taint Quarantined
                    </div>
                  </div>
                  <div style={{ marginTop: 10, display: 'flex', gap: 6 }}>
                    <button
                      className="button button-primary"
                      onClick={() => handleRunDeviceGoal('Open WhatsApp and chat with Jordan', 'messaging', { recipient: 'Jordan', message_body: 'Can we sync on the design review tomorrow at 2 PM?' })}
                      disabled={isDeviceRunning}
                      style={{ fontSize: 9, padding: '4px 9px' }}
                    >
                      <Play size={10} /> Test L1 Gate
                    </button>
                  </div>
                </div>

                {/* Exemplar 3: Game Match */}
                <div style={{ padding: 12, border: '1px solid #dce4da', borderRadius: 8, background: '#ffffff', display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>
                  <div>
                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                      <strong style={{ fontSize: 11, color: '#27382a' }}>3. Turn-Based Match</strong>
                      <span style={{ fontSize: 7, font: '600 7px var(--mono)', background: '#ecefe9', color: '#5a6b5c', padding: '1px 5px', borderRadius: 3 }}>HARD · RUNG 2/3</span>
                    </div>
                    <p style={{ fontSize: 9, color: '#5b695a', margin: '6px 0', lineHeight: 1.4 }}>
                      "Play turn-based chess with Jordan: execute legal opening move e2-e4".
                    </p>
                    <div style={{ fontSize: 8, color: '#4d5d4f', font: 'var(--mono)', background: '#f3f6f2', padding: '4px 6px', borderRadius: 4 }}>
                      Policy: Transparent Anti-Cheat Disclosure &middot; Vision Board Postcondition
                    </div>
                  </div>
                  <div style={{ marginTop: 10, display: 'flex', gap: 6 }}>
                    <button
                      className="button button-primary"
                      onClick={() => handleRunDeviceGoal('Play turn-based chess with Jordan', 'game', { game_title: 'Chess', move_notation: 'e2-e4' })}
                      disabled={isDeviceRunning}
                      style={{ fontSize: 9, padding: '4px 9px' }}
                    >
                      <Play size={10} /> Test Turn Move
                    </button>
                  </div>
                </div>
              </div>
            </div>

            {/* Interactive Device Goal Console */}
            <div style={{ marginTop: 20, padding: 14, border: '1px solid #d6e2d3', borderRadius: 8, background: '#f8faf7' }}>
              <div className="eyebrow">OBSERVE-ACT-VERIFY CONSOLE</div>
              <h3 style={{ fontSize: 13, margin: '2px 0 8px' }}>Execute Custom Device Instruction</h3>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 140px auto', gap: 8 }}>
                <input
                  value={customGoal}
                  onChange={(e) => setCustomGoal(e.target.value)}
                  placeholder="Describe task (e.g. Create a folder named analytics with script.py)..."
                  style={{ padding: 7, borderRadius: 6, border: '1px solid #d0dcce', fontSize: 10 }}
                />
                <select
                  value={customCategory}
                  onChange={(e) => setCustomCategory(e.target.value)}
                  style={{ padding: 7, borderRadius: 6, border: '1px solid #d0dcce', fontSize: 10 }}
                >
                  <option value="auto">auto-detect</option>
                  <option value="filesystem">filesystem (Rung 1)</option>
                  <option value="messaging">messaging (Rung 2/4)</option>
                  <option value="game">game (Rung 2/3)</option>
                </select>
                <button
                  className="button button-primary"
                  onClick={() => handleRunDeviceGoal(customGoal, customCategory)}
                  disabled={isDeviceRunning}
                  style={{ fontSize: 10 }}
                >
                  <Play size={11} /> {isDeviceRunning ? 'Executing...' : 'Execute Goal'}
                </button>
              </div>

              {/* Execution Result Box */}
              {deviceResult && (
                <div style={{ marginTop: 12, padding: 10, border: '1px solid #233426', borderRadius: 6, background: '#121a14', color: '#97e88b' }}>
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 6 }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                      <span style={{ fontSize: 8, font: '600 8px var(--mono)', padding: '2px 6px', borderRadius: 3, background: '#1c342f', color: '#7ce4cf' }}>
                        {deviceResult.rung_used}
                      </span>
                      {deviceResult.verified && (
                        <span style={{ fontSize: 8, font: '600 8px var(--mono)', padding: '2px 6px', borderRadius: 3, background: '#1c3924', color: '#97e88b' }}>
                          POSTCONDITIONS VERIFIED
                        </span>
                      )}
                      {deviceResult.requires_approval && (
                        <span style={{ fontSize: 8, font: '600 8px var(--mono)', padding: '2px 6px', borderRadius: 3, background: '#453213', color: '#e8c471' }}>
                          L1 APPROVAL REQUIRED
                        </span>
                      )}
                    </div>
                    {deviceResult.undo_available && (
                      <button
                        className="button button-soft"
                        onClick={() => handleUndoDeviceAction(deviceResult.receipt_id)}
                        style={{ fontSize: 8, padding: '2px 7px', color: '#fadad7', background: '#351c19', borderColor: '#5c2d28' }}
                      >
                        <RotateCcw size={9} /> Rollback (Undo)
                      </button>
                    )}
                  </div>

                  <p style={{ fontSize: 10, color: '#dcecdb', margin: '4px 0 8px' }}>
                    {deviceResult.message}
                  </p>

                  {/* L1 Human Confirmation Box */}
                  {deviceResult.requires_approval && deviceResult.draft && (
                    <div style={{ padding: 10, border: '1px solid #4a3c1e', borderRadius: 6, background: '#1e1a12', margin: '8px 0' }}>
                      <strong style={{ fontSize: 10, color: '#f5d58b' }}>Outbound Draft Preview (L1 Policy Check):</strong>
                      <div style={{ fontSize: 9, color: '#e8dcbe', margin: '6px 0', fontStyle: 'italic', background: '#13110c', padding: 6, borderRadius: 4 }}>
                        To: {deviceResult.draft.recipient} via {deviceResult.draft.platform}<br />
                        "{deviceResult.draft.body}"
                      </div>
                      <div style={{ display: 'flex', gap: 6, marginTop: 8 }}>
                        <button
                          className="button button-primary"
                          onClick={() => handleRunDeviceGoal(deviceResult.goal, deviceResult.task_category, { recipient: deviceResult.draft.recipient, message_body: deviceResult.draft.body }, true)}
                          style={{ fontSize: 9, padding: '3px 8px' }}
                        >
                          <Check size={11} /> Confirm & Stage Send
                        </button>
                      </div>
                    </div>
                  )}

                  {/* Step Timeline */}
                  {deviceResult.steps && (
                    <div style={{ display: 'grid', gap: 6, marginTop: 8 }}>
                      {deviceResult.steps.map((st) => (
                        <div key={st.step_index} style={{ padding: '6px 8px', background: '#18241b', borderRadius: 4, border: '1px solid #233426', fontSize: 9 }}>
                          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                            <span>Step {st.step_index}: <strong>{st.action}</strong></span>
                            <span style={{ font: '8px var(--mono)', color: '#7ce4cf' }}>{st.rung_resolved}</span>
                          </div>
                          {st.postcondition_check && (
                            <div style={{ fontSize: 8, color: st.postcondition_check.passed ? '#88cc8e' : '#e8a088', marginTop: 3 }}>
                              Assertion: <code>{st.postcondition_check.assertion}</code> &mdash; {st.postcondition_check.passed ? 'PASSED' : 'PENDING'}
                            </div>
                          )}
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              )}
            </div>

            {/* Action History & Undo Log */}
            <div style={{ marginTop: 20 }}>
              <div className="eyebrow">AUDITABLE DEVICE RECEIPTS ({deviceHistory.length})</div>
              <div style={{ display: 'grid', gap: 6, marginTop: 8, maxHeight: 200, overflowY: 'auto' }}>
                {deviceHistory.map((rec) => (
                  <div key={rec.id} style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '8px 10px', border: '1px solid #e1e8df', borderRadius: 6, background: '#fafbfa', fontSize: 9 }}>
                    <div>
                      <strong style={{ color: '#27382a' }}>{rec.goal}</strong>
                      <div style={{ display: 'flex', gap: 6, marginTop: 3 }}>
                        <span style={{ font: '8px var(--mono)', color: '#437c6d' }}>{rec.rung_used}</span>
                        <span style={{ color: '#7a8a7a' }}>&middot;</span>
                        <span style={{ color: rec.verified ? '#22602e' : '#882d22' }}>{rec.verified ? '100% Verified' : 'Check Pending'}</span>
                      </div>
                    </div>
                    {rec.undo_available && (
                      <button
                        className="button button-soft"
                        onClick={() => handleUndoDeviceAction(rec.id)}
                        style={{ fontSize: 8, padding: '3px 8px' }}
                      >
                        <RotateCcw size={10} /> Rollback
                      </button>
                    )}
                  </div>
                ))}
              </div>
            </div>
          </section>

          <aside className="sovereign-aside">
            <div className="policy-explainer">
              <div className="eyebrow">LADDER ARCHITECTURE</div>
              <h3>Action Ladder Advantages</h3>
              <p style={{ fontSize: 9, color: '#687367', lineHeight: 1.55 }}>
                1. <strong>Direct API/CLI First:</strong> Why guess screen pixels when you can create folders or read data via deterministic system calls?
              </p>
              <p style={{ fontSize: 9, color: '#687367', lineHeight: 1.55 }}>
                2. <strong>A11y Tree Over Vision:</strong> UI automation uses semantic labels instead of bounding boxes that break on resolution changes.
              </p>
              <p style={{ fontSize: 9, color: '#687367', lineHeight: 1.55 }}>
                3. <strong>Taint Quarantine:</strong> Inbound WhatsApp messages cannot hijack the agent or trigger shell commands.
              </p>
              <div className="manifest-code">
                <span>CONFORMAL BOUND:</span>
                <b>E[Error] &le; 0.02 (alpha)</b>
                <span style={{ marginTop: 4 }}>POSTCONDITION CONTRACT:</span>
                <b>Assert state change after every step</b>
                <span style={{ marginTop: 4 }}>ATOMIC UNDO:</span>
                <b>Inverse compensation handlers</b>
              </div>
            </div>
          </aside>
        </div>
      )}
      {/* TAB 8: DREAMS, PROVES & EARNS (AUTONOMY SUBSTRATE) */}
      {activeTab === 'dreams' && (
        <div className="sovereign-panel-grid">
          <section className="sovereign-card" style={{ gridColumn: '1 / -1' }}>
            <div className="panel-head">
              <div>
                <div className="eyebrow">THE SOVEREIGN TRIFECTA · AUTONOMY SUBSTRATE</div>
                <h2>An Assistant That Dreams, Proves, and Earns</h2>
              </div>
              <span className="local-tag" style={{ background: '#e0e7ff', color: '#3730a3' }}>
                <Moon size={13} /> Self-Refining · Verifiable Privacy · Evidence-Gated
              </span>
            </div>
            <p className="section-intro">
              Commercial voice assistants cannot be trusted with device autonomy because they cannot dream without vendor surveillance, cannot prove privacy without open runtimes, and grant autonomy through casual clicks rather than statistical replay.
              Threadline implements the <strong>Sovereign Trifecta</strong>: improving overnight, proving cryptographic containment, and earning autonomy only through 90-day counterfactual backtesting.
            </p>

            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: 14, margin: '20px 0 30px' }}>
              <div style={{ padding: 14, background: '#131c15', border: '1px solid #1f3022', borderRadius: 8 }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 8, color: '#88ab8e' }}>
                  <Moon size={16} />
                  <strong style={{ fontSize: 13 }}>1. Overnight Dreaming</strong>
                </div>
                <p style={{ fontSize: 11, color: '#97b89c', lineHeight: 1.5, margin: 0 }}>
                  Consolidates memory, distills repeated traces into Hermes skills, rehearses DAGs in sandbox with inverse rollbacks, and flags tomorrow's calendar conflicts.
                </p>
              </div>

              <div style={{ padding: 14, background: '#131c15', border: '1px solid #1f3022', borderRadius: 8 }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 8, color: '#88ab8e' }}>
                  <Scale size={16} />
                  <strong style={{ fontSize: 13 }}>2. Autonomy Backtesting</strong>
                </div>
                <p style={{ fontSize: 11, color: '#97b89c', lineHeight: 1.5, margin: 0 }}>
                  Replays 90 days of real/synthetic decision history. Promotes from L1 to L3 ONLY IF Wilson UCB error rate &le; &alpha; and zero safety invariants are breached.
                </p>
              </div>

              <div style={{ padding: 14, background: '#131c15', border: '1px solid #1f3022', borderRadius: 8 }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 8, color: '#88ab8e' }}>
                  <ShieldCheck size={16} />
                  <strong style={{ fontSize: 13 }}>3. Proof-of-Privacy</strong>
                </div>
                <p style={{ fontSize: 11, color: '#97b89c', lineHeight: 1.5, margin: 0 }}>
                  Every egress and model call is locked in a SHA-256 Merkle chain signed by OpenShell. Provides cryptographic proof: <em>"0 raw records left this device."</em>
                </p>
              </div>
            </div>

            {/* SECTION 1: OVERNIGHT DREAMING */}
            <div style={{ borderTop: '1px solid #1e2e22', paddingTop: 20, marginTop: 20 }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
                <div>
                  <h3 style={{ margin: 0, fontSize: 15, color: '#eef8ef' }}>Overnight Dream Engine</h3>
                  <small style={{ color: '#88a88c' }}>Simulates always-on Nebius Serverless nightly consolidation</small>
                </div>
                <button
                  className="button button-primary"
                  onClick={handleTriggerDream}
                  disabled={isDreaming}
                  style={{ display: 'flex', alignItems: 'center', gap: 6 }}
                >
                  <RefreshCw size={13} className={isDreaming ? 'spin' : ''} />
                  <span>{isDreaming ? 'Dreaming...' : 'Trigger Overnight Dream Cycle'}</span>
                </button>
              </div>

              {dreamReport && (
                <div style={{ background: '#0e1510', border: '1px solid #1f3022', borderRadius: 8, padding: 16 }}>
                  <div style={{ display: 'flex', gap: 10, alignItems: 'center', marginBottom: 12 }}>
                    <span className="badge" style={{ background: '#1f3325', color: '#95dbab' }}>REPORT ID: {dreamReport.report_id || dreamReport.id}</span>
                    <span style={{ fontSize: 11, color: '#7e9683' }}>Generated in {dreamReport.duration_seconds || 0.8}s</span>
                  </div>

                  <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))', gap: 12 }}>
                    {/* Consolidated Memories */}
                    <div style={{ padding: 12, background: '#121a14', borderRadius: 6, border: '1px solid #1a281c' }}>
                      <strong style={{ fontSize: 11, color: '#88ab8e', display: 'block', marginBottom: 6 }}>Consolidated Memory Clusters ({dreamReport.memories_consolidated?.length || 0})</strong>
                      <ul style={{ margin: 0, paddingLeft: 16, fontSize: 10, color: '#97b89c', lineHeight: 1.6 }}>
                        {(dreamReport.memories_consolidated || []).map((m, idx) => (
                          <li key={idx}><strong>{m.category}:</strong> {m.summary}</li>
                        ))}
                      </ul>
                    </div>

                    {/* Draft Skills Synthesized */}
                    <div style={{ padding: 12, background: '#121a14', borderRadius: 6, border: '1px solid #1a281c' }}>
                      <strong style={{ fontSize: 11, color: '#88ab8e', display: 'block', marginBottom: 6 }}>Quarantined Hermes Skill Drafts ({dreamReport.draft_skills_synthesized?.length || 0})</strong>
                      {(dreamReport.draft_skills_synthesized || []).map((s, idx) => (
                        <div key={idx} style={{ padding: '6px 8px', background: '#090e0a', borderRadius: 4, marginBottom: 6, border: '1px solid #18261b' }}>
                          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                            <span style={{ fontSize: 11, fontWeight: 600, color: '#d2ebd7' }}>{s.name}</span>
                            <span className="badge" style={{ background: '#3b2f15', color: '#f0c458', fontSize: 8 }}>{s.status}</span>
                          </div>
                          <p style={{ fontSize: 9, color: '#88a88c', margin: '4px 0 0' }}>{s.description}</p>
                          <div style={{ display: 'flex', gap: 8, marginTop: 4, fontSize: 8, color: '#7eb88a' }}>
                            <span>Sandbox: {s.rehearsal_status}</span>
                            <span>·</span>
                            <span>Inverse Rollback: {s.inverse_rollback_verified ? 'VERIFIED' : 'PENDING'}</span>
                          </div>
                        </div>
                      ))}
                    </div>

                    {/* Tomorrow Conflicts */}
                    <div style={{ padding: 12, background: '#121a14', borderRadius: 6, border: '1px solid #1a281c' }}>
                      <strong style={{ fontSize: 11, color: '#88ab8e', display: 'block', marginBottom: 6 }}>Tomorrow's Calendar Pre-Rehearsal ({dreamReport.conflicts_caught_for_tomorrow?.length || 0})</strong>
                      {(dreamReport.conflicts_caught_for_tomorrow || []).map((c, idx) => (
                        <div key={idx} style={{ padding: '6px 8px', background: '#1c150c', borderRadius: 4, marginBottom: 6, border: '1px solid #362914' }}>
                          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                            <span style={{ fontSize: 10, fontWeight: 600, color: '#ebd097' }}>{c.title}</span>
                            <span className="badge" style={{ background: '#3e2e12', color: '#f5c66b', fontSize: 8 }}>{c.severity}</span>
                          </div>
                          <div style={{ fontSize: 8, color: '#a89476', marginTop: 2 }}>{c.time_slot}</div>
                          <p style={{ fontSize: 9, color: '#c4b39b', margin: '4px 0 0' }}>{c.mitigation_advice}</p>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              )}
            </div>

            {/* SECTION 2: AUTONOMY BACKTESTING SIMULATOR */}
            <div style={{ borderTop: '1px solid #1e2e22', paddingTop: 20, marginTop: 24 }}>
              <div style={{ marginBottom: 12 }}>
                <h3 style={{ margin: 0, fontSize: 15, color: '#eef8ef' }}>Autonomy Backtesting Engine</h3>
                <small style={{ color: '#88a88c' }}>Replays 90 days of decision history to evaluate statistical risk before promoting L1 &rarr; L3</small>
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))', gap: 14, background: '#0e1510', border: '1px solid #1f3022', borderRadius: 8, padding: 16 }}>
                <div>
                  <label style={{ fontSize: 10, color: '#88a88c', display: 'block', marginBottom: 4 }}>Select Policy to Backtest</label>
                  <select
                    className="select-field"
                    value={backtestCandidate}
                    onChange={(e) => setBacktestCandidate(e.target.value)}
                    style={{ width: '100%', padding: '6px 8px', background: '#141d15', border: '1px solid #233527', color: '#d2ebd7', borderRadius: 4 }}
                  >
                    <option value="decline_spam_invites">Decline Cold Calendar Spam (L1 &rarr; L3)</option>
                    <option value="auto_reply_delivery">Delivery & Tracking Update Processor (L1 &rarr; L3)</option>
                    <option value="auto_approve_workspaces">Sandboxed Workspace Generator (L2 &rarr; L3)</option>
                  </select>

                  <div style={{ marginTop: 12 }}>
                    <label style={{ fontSize: 10, color: '#88a88c', display: 'block', marginBottom: 4 }}>Conformal Risk Tolerance (&alpha;)</label>
                    <div style={{ display: 'flex', gap: 8 }}>
                      {[0.02, 0.05, 0.10].map((a) => (
                        <button
                          key={a}
                          type="button"
                          className="button button-soft"
                          onClick={() => setBacktestAlpha(a)}
                          style={{
                            flex: 1,
                            fontSize: 10,
                            padding: '4px 6px',
                            background: backtestAlpha === a ? '#1f3b28' : '#121a14',
                            borderColor: backtestAlpha === a ? '#3e7550' : '#1e2e22',
                            color: backtestAlpha === a ? '#9ae0ab' : '#88a88c'
                          }}
                        >
                          &alpha; = {a}
                        </button>
                      ))}
                    </div>
                  </div>

                  <div style={{ marginTop: 14, display: 'flex', alignItems: 'center', gap: 8 }}>
                    <input
                      type="checkbox"
                      id="advToggle"
                      checked={backtestAdversarial}
                      onChange={(e) => setBacktestAdversarial(e.target.checked)}
                    />
                    <label htmlFor="advToggle" style={{ fontSize: 10, color: '#c3d6c7', cursor: 'pointer' }}>
                      Inject Invariant Violation (VIP Conflict)
                    </label>
                  </div>

                  <button
                    className="button button-primary"
                    onClick={handleRunBacktest}
                    disabled={isBacktesting}
                    style={{ width: '100%', marginTop: 16 }}
                  >
                    {isBacktesting ? 'Replaying 90 Days...' : 'Run 90-Day Backtest'}
                  </button>
                </div>

                {/* Backtest Results Card */}
                <div>
                  <label style={{ fontSize: 10, color: '#88a88c', display: 'block', marginBottom: 4 }}>Backtest Verdict & Statistical Bounds</label>
                  {backtestResult ? (
                    <div style={{ padding: 12, background: backtestResult.status === 'promoted' ? '#0f2415' : '#291111', border: `1px solid ${backtestResult.status === 'promoted' ? '#1f592e' : '#5e2323'}`, borderRadius: 6 }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
                        <span className="badge" style={{
                          background: backtestResult.status === 'promoted' ? '#1c4d29' : '#571818',
                          color: backtestResult.status === 'promoted' ? '#a3f0ba' : '#fca6a6',
                          fontWeight: 700
                        }}>
                          {backtestResult.status.toUpperCase()}
                        </span>
                        <span style={{ fontSize: 9, color: '#88a88c' }}>{backtestResult.total_samples} historical events replayed</span>
                      </div>

                      <div style={{ fontSize: 10, color: '#d2ebd7', margin: '6px 0', lineHeight: 1.45 }}>
                        {backtestResult.verdict_explanation}
                      </div>

                      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8, marginTop: 10, fontSize: 9 }}>
                        <div style={{ padding: 6, background: '#090d0a', borderRadius: 4 }}>
                          <span style={{ color: '#88a88c', display: 'block' }}>Empirical Error:</span>
                          <strong style={{ fontSize: 11, color: '#eef8ef' }}>{(backtestResult.empirical_error_rate * 100).toFixed(1)}%</strong>
                        </div>
                        <div style={{ padding: 6, background: '#090d0a', borderRadius: 4 }}>
                          <span style={{ color: '#88a88c', display: 'block' }}>Wilson 95% UCB:</span>
                          <strong style={{ fontSize: 11, color: backtestResult.ucb_error_rate <= backtestResult.alpha_threshold ? '#9fe8b3' : '#f08989' }}>
                            {(backtestResult.ucb_error_rate * 100).toFixed(1)}%
                          </strong>
                        </div>
                      </div>

                      {backtestResult.worst_case_trace && (
                        <div style={{ marginTop: 10, padding: 8, background: '#3b1212', borderRadius: 4, border: '1px solid #6b2121', fontSize: 9, color: '#f7bcbc' }}>
                          <strong>Worst-Case Counterexample:</strong> {backtestResult.worst_case_trace}
                        </div>
                      )}
                    </div>
                  ) : (
                    <div style={{ padding: 20, textAlign: 'center', color: '#728575', fontSize: 11, background: '#121a14', borderRadius: 6 }}>
                      Select a policy and click "Run 90-Day Backtest" to evaluate statistical risk bounds and counterexamples.
                    </div>
                  )}
                </div>
              </div>
            </div>

            {/* SECTION 3: PROOF-OF-PRIVACY & CHAOS MONKEY */}
            <div style={{ borderTop: '1px solid #1e2e22', paddingTop: 20, marginTop: 24, display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: 16 }}>
              {/* Proof of Privacy */}
              <div style={{ background: '#0e1510', border: '1px solid #1f3022', borderRadius: 8, padding: 16 }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
                  <div>
                    <h3 style={{ margin: 0, fontSize: 14, color: '#eef8ef' }}>Proof-of-Privacy Merkle Chain</h3>
                    <small style={{ color: '#88a88c' }}>Tamper-evident cryptographic log cross-checked with OpenShell</small>
                  </div>
                  <button
                    className="button button-soft"
                    onClick={handleVerifyPrivacyChain}
                    disabled={isAuditingPrivacy}
                    style={{ fontSize: 10, padding: '4px 8px' }}
                  >
                    <ShieldCheck size={12} />
                    <span>{isAuditingPrivacy ? 'Verifying...' : 'Run Cryptographic Audit'}</span>
                  </button>
                </div>

                {privacyAudit && (
                  <div style={{ padding: 8, background: privacyAudit.chain_valid ? '#0f2415' : '#2e1212', borderRadius: 4, marginBottom: 12, border: `1px solid ${privacyAudit.chain_valid ? '#1f592e' : '#571e1e'}` }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: 10, fontWeight: 600, color: privacyAudit.chain_valid ? '#9ae0ab' : '#f08989' }}>
                      <CheckCircle2 size={13} />
                      <span>{privacyAudit.audit_verdict}</span>
                    </div>
                    <div style={{ fontSize: 8, color: '#88a88c', marginTop: 4 }}>
                      Verified {privacyAudit.total_blocks_verified} blocks from Genesis. OpenShell signatures: {privacyAudit.openshell_signatures_valid ? 'VALID' : 'INVALID'}.
                    </div>
                  </div>
                )}

                <div style={{ maxHeight: 200, overflowY: 'auto' }}>
                  {privacyBlocks.map((b) => (
                    <div key={b.block_index} style={{ padding: '6px 8px', background: '#121a14', borderRadius: 4, marginBottom: 6, border: '1px solid #1a281c', fontSize: 9 }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', color: '#88ab8e' }}>
                        <span>Block #{b.block_index} · {b.event_type}</span>
                        <span style={{ color: '#68826d', fontFamily: 'var(--mono)', fontSize: 8 }}>{b.timestamp.slice(11, 19)}</span>
                      </div>
                      <div style={{ fontFamily: 'var(--mono)', fontSize: 8, color: '#7e9c84', margin: '2px 0' }}>
                        Hash: {b.block_hash.slice(0, 24)}...
                      </div>
                      <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 8, color: '#a0c4a7' }}>
                        <span>Target: {b.destination}</span>
                        <span style={{ color: b.raw_pii_detected === 0 ? '#86e39e' : '#f08989' }}>
                          Raw PII: {b.raw_pii_detected} records
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Personal Chaos Monkey */}
              <div style={{ background: '#0e1510', border: '1px solid #1f3022', borderRadius: 8, padding: 16 }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
                  <div>
                    <h3 style={{ margin: 0, fontSize: 14, color: '#eef8ef' }}>Personal Chaos Monkey</h3>
                    <small style={{ color: '#88a88c' }}>Nightly adversarial stress-testing (10 attack vectors)</small>
                  </div>
                  <button
                    className="button button-soft"
                    onClick={handleRunChaosMonkey}
                    disabled={isChaosRunning}
                    style={{ fontSize: 10, padding: '4px 8px' }}
                  >
                    <Flame size={12} />
                    <span>{isChaosRunning ? 'Attacking...' : 'Run Security Stress Test'}</span>
                  </button>
                </div>

                {chaosResult && (
                  <div>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '8px 12px', background: '#131f16', borderRadius: 6, marginBottom: 12, border: '1px solid #1f3825' }}>
                      <span style={{ fontSize: 11, color: '#d2ebd7' }}>Nightly Resilience Score:</span>
                      <strong style={{ fontSize: 16, color: '#86e39e' }}>{chaosResult.resilience_score}%</strong>
                    </div>

                    <div style={{ maxHeight: 180, overflowY: 'auto' }}>
                      {(chaosResult.probes || []).map((p) => (
                        <div key={p.probe_id} style={{ padding: '6px 8px', background: '#121a14', borderRadius: 4, marginBottom: 6, border: '1px solid #1a281c', fontSize: 9 }}>
                          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                            <span style={{ fontWeight: 600, color: '#d2ebd7' }}>{p.name}</span>
                            <span className="badge" style={{ background: '#123b1c', color: '#97f0ab', fontSize: 8 }}>{p.status}</span>
                          </div>
                          <p style={{ margin: '3px 0 0', color: '#88a88c', fontSize: 8 }}>{p.defense_triggered}</p>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </div>
          </section>
        </div>
      )}

    </div>
  );
}
