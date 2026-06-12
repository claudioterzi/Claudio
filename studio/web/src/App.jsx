import { motion, AnimatePresence } from 'framer-motion'
import { useState } from 'react'
import './App.css'

const ROSSO = '#c0392b'
const VIOLA = '#7c3aed'

const agenti = [
  { id: 'RAFFA-001',  ruolo: 'Architetto',       colore: ROSSO      },
  { id: 'DECOMP-005', ruolo: 'Analista Intenti',  colore: '#2563eb'  },
  { id: 'MEMO-002',   ruolo: 'Custode',           colore: '#059669'  },
  { id: 'SENTIN-004', ruolo: 'Vigilante',         colore: '#d97706'  },
  { id: 'GEN-006',    ruolo: 'Compositore',       colore: VIOLA      },
  { id: 'WAVE-003',   ruolo: 'Messaggero',        colore: '#0891b2'  },
]

function AgentCard({ agente, index, attivo, onClick }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 40 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.1, duration: 0.5, type: 'spring', stiffness: 120 }}
      whileHover={{ scale: 1.05, boxShadow: `0 8px 32px ${agente.colore}44` }}
      whileTap={{ scale: 0.97 }}
      onClick={() => onClick(agente)}
      style={{
        background: attivo ? agente.colore : '#1a1a2e',
        border: `1px solid ${agente.colore}`,
        borderRadius: 12,
        padding: '16px 20px',
        cursor: 'pointer',
        color: attivo ? '#fff' : '#e2e8f0',
        minWidth: 140,
        userSelect: 'none',
      }}
    >
      <div style={{ fontSize: 11, opacity: 0.7, letterSpacing: 1 }}>{agente.id}</div>
      <div style={{ fontSize: 15, fontWeight: 600, marginTop: 4 }}>{agente.ruolo}</div>
    </motion.div>
  )
}

export default function App() {
  const [selezionato, setSelezionato] = useState(null)
  const [battito, setBattito] = useState(false)

  function handleBattito() {
    setBattito(true)
    setTimeout(() => setBattito(false), 700)
  }

  return (
    <div style={{
      minHeight: '100vh',
      background: '#0f0f1a',
      color: '#e2e8f0',
      fontFamily: 'system-ui, sans-serif',
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      justifyContent: 'center',
      gap: 48,
      padding: 32,
    }}>

      {/* Titolo */}
      <motion.div
        initial={{ opacity: 0, y: -30 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.8, type: 'spring' }}
        style={{ textAlign: 'center' }}
      >
        <motion.h1
          style={{ fontSize: 48, fontWeight: 800, color: ROSSO, margin: 0 }}
          animate={{
            textShadow: [
              '0 0 0px #c0392b',
              '0 0 20px #c0392b66',
              '0 0 0px #c0392b',
            ],
          }}
          transition={{ duration: 3, repeat: Infinity }}
        >
          SDQ-1
        </motion.h1>
        <motion.p
          style={{ color: VIOLA, margin: '8px 0 0', fontSize: 14, letterSpacing: 3 }}
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.4 }}
        >
          SISTEMA DI QUADRANTI
        </motion.p>
        <motion.p
          style={{ color: '#64748b', margin: '4px 0 0', fontSize: 12 }}
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.6 }}
        >
          Raffaello Creative Studio · Bruxelles
        </motion.p>
      </motion.div>

      {/* Pipeline agenti */}
      <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap', justifyContent: 'center' }}>
        {agenti.map((a, i) => (
          <AgentCard
            key={a.id}
            agente={a}
            index={i}
            attivo={selezionato?.id === a.id}
            onClick={ag => setSelezionato(selezionato?.id === ag.id ? null : ag)}
          />
        ))}
      </div>

      {/* Dettaglio agente */}
      <AnimatePresence>
        {selezionato && (
          <motion.div
            key={selezionato.id}
            initial={{ opacity: 0, scale: 0.92, y: 16 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.92, y: 16 }}
            transition={{ duration: 0.25, type: 'spring', stiffness: 200 }}
            style={{
              background: '#1a1a2e',
              border: `1px solid ${selezionato.colore}`,
              borderRadius: 16,
              padding: 24,
              maxWidth: 400,
              width: '100%',
              textAlign: 'center',
            }}
          >
            <motion.div
              style={{ color: selezionato.colore, fontSize: 11, letterSpacing: 2 }}
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ delay: 0.1 }}
            >
              {selezionato.id}
            </motion.div>
            <h2 style={{ margin: '8px 0 4px', color: '#fff' }}>{selezionato.ruolo}</h2>
            <p style={{ color: '#94a3b8', fontSize: 13, margin: 0 }}>
              Pipeline SDQ-1 — Protocollo Raffaello
            </p>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Battito */}
      <motion.button
        animate={battito ? {
          scale: [1, 1.18, 1],
          boxShadow: [
            '0 0 0px #c0392b',
            '0 0 32px #c0392b99',
            '0 0 0px #c0392b',
          ],
        } : {}}
        transition={{ duration: 0.6 }}
        whileHover={{ borderColor: ROSSO, color: '#fff', background: `${ROSSO}22` }}
        onClick={handleBattito}
        style={{
          background: 'transparent',
          border: `2px solid ${ROSSO}`,
          borderRadius: 8,
          color: ROSSO,
          padding: '12px 32px',
          fontSize: 13,
          fontWeight: 700,
          letterSpacing: 3,
          cursor: 'pointer',
          transition: 'background 0.2s, color 0.2s',
        }}
      >
        ● BATTITO
      </motion.button>

    </div>
  )
}
