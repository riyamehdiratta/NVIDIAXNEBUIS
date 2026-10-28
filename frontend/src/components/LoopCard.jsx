import { ArrowDownRight, ArrowUpRight, CalendarDays, Check, Clock3, CornerDownRight, FileText, Mail, MessageSquareText, MoreHorizontal, Sparkles, UserRound, X } from 'lucide-react';
import { useState } from 'react';

const kindLabels = { task: 'To do', promise: 'You promised', waiting_on_them: 'Waiting on', appointment: 'Event' };
const kindIcons = { task: CornerDownRight, promise: ArrowUpRight, waiting_on_them: ArrowDownRight, appointment: CalendarDays };

export function LoopCard({ item, onDone, onReminder, onDraft, onCalendar }) {
  const [expanded, setExpanded] = useState(false);
  const Icon = kindIcons[item.kind] || CornerDownRight;
  const dueDate = item.due_at ? new Date(`${item.due_at.slice(0, 10)}T00:00:00`) : null;
  const due = dueDate ? dueDate.toLocaleDateString(undefined, { month: 'short', day: 'numeric' }) : null;
  const isLate = dueDate && dueDate < new Date(new Date().toDateString());
  const evidence = item.evidence?.[0];
  const SourceIcon = item.source_kind === 'email' ? Mail : item.source_kind === 'calendar' ? CalendarDays : FileText;
  return (
    <article className={`loop-card ${expanded ? 'expanded' : ''}`}>
      <div className={`loop-kind kind-${item.kind}`}><Icon size={15} strokeWidth={1.9} /><span>{kindLabels[item.kind] || 'To do'}</span></div>
      <div className="loop-main">
        <button className="loop-title" onClick={() => setExpanded(!expanded)}>{item.title}</button>
        <div className="loop-meta">
          {due && <span className={`meta-chip ${isLate ? 'late' : ''}`}><Clock3 size={13} />{isLate ? 'Overdue · ' : 'Due '}{due}</span>}
          {item.owner && <span className="meta-chip"><UserRound size={13} />{item.owner}</span>}
          <span className="source-chip"><SourceIcon size={13} />{item.filename || 'Imported source'}</span>
        </div>
        {expanded && <div className="loop-evidence">
          <div className="evidence-heading"><span>WHY THIS IS HERE</span><span className="confidence"><span className={`confidence-dot ${item.confidence < .65 ? 'low' : ''}`} />{Math.round(item.confidence * 100)}% confidence</span></div>
          <p>{evidence?.quote || item.detail}</p>
          <div className="loop-detail">{item.detail}</div>
          {item.confidence < .68 && <div className="review-note">Check the date or owner before acting. This detail may need your correction.</div>}
          <div className="card-actions">
            <button className="button button-soft" onClick={() => onReminder(item)}><Clock3 size={14} /> Remind me</button>
            <button className="button button-soft" onClick={() => onCalendar(item)}><CalendarDays size={14} /> Add to calendar</button>
            <button className="button button-soft" onClick={() => onDraft(item)}><MessageSquareText size={14} /> Draft follow-up</button>
            <button className="button button-done" onClick={() => onDone(item)}><Check size={14} /> Done</button>
          </div>
        </div>}
      </div>
      <button aria-label="Show evidence" className="more-button" onClick={() => setExpanded(!expanded)}><MoreHorizontal size={19} /></button>
    </article>
  );
}
