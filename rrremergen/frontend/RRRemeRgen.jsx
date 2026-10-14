import React, { useState, useRef } from 'react';
import { motion } from 'framer-motion';
import './RRRemeRgen.css';
import { compositionEvents } from './stream.js';

export default function RRRemeRgen() {
  const [prompt, setPrompt] = useState('');
  const [isComposing, setIsComposing] = useState(false);
  const [compositionStage, setCompositionStage] = useState(null);
  const [generatedApp, setGeneratedApp] = useState(null);
  const [error, setError] = useState(null);
  const [mode, setMode] = useState('local');
  const stagesRef = useRef(null);

  const stages = [
    { id: 'architect', label: 'Architect', desc: 'Analyzing requirements...' },
    { id: 'designer', label: 'Designer', desc: 'Creating UI specifications...' },
    { id: 'developer', label: 'Developer', desc: 'Generating code...' },
    { id: 'integrator', label: 'Integrator', desc: 'Connecting services...' },
    { id: 'pm', label: 'PM', desc: 'Validating & debugging...' },
    { id: 'export', label: 'Esporta', desc: 'Preparazione dei sorgenti...' },
  ];

  const handleCompose = async (e) => {
    e.preventDefault();

    if (!prompt.trim()) {
      setError('Please describe your application in natural language');
      return;
    }

    setError(null);
    setIsComposing(true);
    setCompositionStage(null);
    setGeneratedApp(null);

    try {
      // Initiate multi-agent composition
      const response = await fetch('/api/rrremergen/compose', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ prompt, advanced_options: { mode } }),
      });

      for await (const data of compositionEvents(response)) {
        if (data.type === 'stage_progress') {
          setCompositionStage(data.stage);
        } else if (data.type === 'completion') {
          setGeneratedApp(data.app);
        }
      }
    } catch (err) {
      setGeneratedApp(null);
      setError(err.message);
    } finally {
      setIsComposing(false);
      setCompositionStage(null);
    }
  };

  return (
    <div className="rrremergen">
      <header className="rrremergen-header">
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6 }}
        >
          <h1>🎨 RRREMERGEN</h1>
          <p className="subtitle">Web App Auto-Composer (R³∞ Protocol)</p>
          <p className="description">
            Describe your app in natural language. Multi-agent system generates full-stack code.
          </p>
        </motion.div>
      </header>

      <main className="rrremergen-main">
        {!generatedApp ? (
          <motion.form
            className="rrremergen-form"
            onSubmit={handleCompose}
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.2, duration: 0.5 }}
          >
            <div className="form-group">
              <label htmlFor="mode">Modalità:</label>
              <select id="mode" value={mode} onChange={event => setMode(event.target.value)} disabled={isComposing}>
                <option value="local">Generazione locale — OmniRoute / Raffaello</option>
                <option value="demo">Prova pipeline — esempio deterministico</option>
              </select>
              <label htmlFor="prompt">Describe your application:</label>
              <textarea
                id="prompt"
                value={prompt}
                onChange={(e) => setPrompt(e.target.value)}
                placeholder="E.g., Create a task management app with real-time collaboration, user authentication, and integration with Slack..."
                disabled={isComposing}
                rows={6}
                minLength={10}
                maxLength={4000}
              />
            </div>

            {error && (
              <motion.div
                className="error-message"
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
              >
                ⚠️ {error}
              </motion.div>
            )}

            <button type="submit" disabled={isComposing} className="compose-button">
              {isComposing ? '⚙️ Composing...' : '✨ Compose App'}
            </button>
          </motion.form>
        ) : (
          <motion.div
            className="result-container"
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.5 }}
          >
            <div className="success-badge">{generatedApp.simulation ? 'Esempio di prova pronto' : 'Sorgenti generati'}</div>

            <div className="app-info">
              <h2>{generatedApp.title}</h2>
              <p>{generatedApp.description}</p>
            </div>

            <div className="deployment-links">
              {generatedApp.artifact && <a
                href={`data:application/zip;base64,${generatedApp.artifact.content_base64}`}
                download={generatedApp.artifact.filename} className="link-button github">
                Scarica sorgenti ZIP
              </a>}
              <p>Nessuna pubblicazione eseguita. Controlli statici superati; l’app generata resta da eseguire e verificare.</p>
            </div>

            <div className="code-preview">
              <h3>Code Preview</h3>
              <pre><code>{generatedApp.code_preview}</code></pre>
            </div>

            <button
              onClick={() => {
                setGeneratedApp(null);
                setPrompt('');
              }}
              className="compose-button new-app"
            >
              ➕ Compose Another App
            </button>
          </motion.div>
        )}

        {isComposing && (
          <motion.div
            className="stages-progress"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            ref={stagesRef}
          >
            <h3>Composition Pipeline</h3>
            <div className="stages-list">
              {stages.map((stage, idx) => (
                <motion.div
                  key={stage.id}
                  className={`stage ${stage.id === compositionStage ? 'active' : ''} ${
                    idx < stages.findIndex(s => s.id === compositionStage) ? 'completed' : ''
                  }`}
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: idx * 0.1 }}
                >
                  <div className="stage-icon">
                    {idx < stages.findIndex(s => s.id === compositionStage) ? '✓' : idx === stages.findIndex(s => s.id === compositionStage) ? '⚙️' : '◯'}
                  </div>
                  <div className="stage-info">
                    <div className="stage-label">{stage.label}</div>
                    {stage.id === compositionStage && <div className="stage-desc">{stage.desc}</div>}
                  </div>
                </motion.div>
              ))}
            </div>
          </motion.div>
        )}
      </main>
    </div>
  );
}
