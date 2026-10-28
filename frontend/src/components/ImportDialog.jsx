import { FileText, Upload, X } from 'lucide-react';
import { useRef, useState } from 'react';

export function ImportDialog({ onClose, onText, onFiles }) {
  const [text, setText] = useState('');
  const input = useRef(null);
  return <div className="modal-backdrop" onMouseDown={(e) => e.target === e.currentTarget && onClose()}>
    <section className="dialog import-dialog">
      <header className="dialog-header"><div><div className="eyebrow">CAPTURE A NEW THREAD</div><h2>Bring a loose end into focus.</h2></div><button className="icon-button" onClick={onClose}><X size={18} /></button></header>
      <p className="dialog-intro">Drop an email, calendar file, or note into your private workspace. Threadline keeps the original here and links every suggested task back to its source.</p>
      <button className="dropzone" onClick={() => input.current?.click()}><span className="drop-icon"><Upload size={20} /></span><strong>Choose files to import</strong><small>.eml, .ics, .txt, .md, .csv · up to 2 MB</small><input ref={input} hidden multiple type="file" accept=".eml,.ics,.txt,.md,.csv,.log" onChange={e => e.target.files?.length && onFiles(e.target.files)} /></button>
      <div className="or-divider"><span>or paste something in</span></div>
      <textarea value={text} onChange={e => setText(e.target.value)} className="capture-text" placeholder={'Paste an email, a thought, or a promise you don’t want to lose…'} />
      <footer className="dialog-footer"><span><FileText size={14} /> Saved to this device</span><button className="button button-primary" disabled={!text.trim()} onClick={() => onText(text)}>Add to Threadline</button></footer>
    </section>
  </div>;
}
