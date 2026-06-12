import { motion, useScroll, useTransform, AnimatePresence } from 'framer-motion'
import { useRef, useState, useEffect } from 'react'
import './App.css'

// ─── COSTANTI ────────────────────────────────────────────────────────────────

const PURPLE = '#7c3aed'
const PINK   = '#db2777'
const CYAN   = '#06b6d4'
const GOLD   = '#f59e0b'
const ROSSO  = '#c0392b'

const NAV_LINKS = [
  { href: '#servizi', label: 'Servizi' },
  { href: '#come-funziona', label: 'Come funziona' },
  { href: '#chi-siamo', label: 'Chi siamo' },
  { href: '#contatto', label: 'Contatto' },
]

const SERVIZI = [
  {
    emoji: '🎵', titolo: 'Musica', colore: PURPLE,
    tagline: 'Canzoni, inni, album su misura',
    items: ['Testo canzone — €25', 'Canzone completa — €45', 'Inno personalizzato — €60', 'Album concetto (5 canzoni) — €180'],
  },
  {
    emoji: '🎨', titolo: 'Immagini', colore: PINK,
    tagline: 'Illustrazioni, loghi, post social',
    items: ['Illustrazione singola — €15', 'Logo concept (3 varianti) — €40', 'Cover libro/album — €30', 'Post social set 9 — €70'],
  },
  {
    emoji: '🎬', titolo: 'Video', colore: CYAN,
    tagline: 'Script, reel, spot pubblicitari',
    items: ['Script Reel 30-60s — €20', 'Script YouTube — €50', 'Spot pubblicitario — €35', 'Pitch video startup — €80'],
  },
  {
    emoji: '✍️', titolo: 'Parola', colore: GOLD,
    tagline: 'Blog, speech, storie, ebook',
    items: ['Articolo blog SEO — €25', 'Serie 5 post LinkedIn — €40', 'Discorso/speech — €50', 'Ebook completo — €250'],
  },
  {
    emoji: '🍳', titolo: 'Cucina', colore: '#10b981',
    tagline: 'Corsi online e chef a Bruxelles',
    items: ['Corso online 1h — €60', 'Corso tematico 2h — €90', 'Menu per evento — €45', 'Chef a domicilio — €180'],
  },
  {
    emoji: '🤖', titolo: 'AI & Codice', colore: ROSSO,
    tagline: 'Prompt, agenti, automazioni',
    items: ['Prompt ottimizzato — €30', 'Agente custom SDQ-1 — €300+', 'Script automazione — €40+', 'Workshop prompt — €80'],
  },
]

const STEPS = [
  { n: '01', titolo: 'Descrivi', testo: 'Scrivi cosa ti serve in italiano, inglese, francese o spagnolo. Non serve essere tecnico.' },
  { n: '02', titolo: 'Pipeline AI', testo: '6 agenti specializzati elaborano la tua richiesta in sequenza: analisi, decomposizione, memoria, controllo qualità, generazione, rifinitura.' },
  { n: '03', titolo: 'Revisione', testo: 'Il Contraddittore interno verifica la coerenza. Il Sognatore espande le possibilità. Ricevi solo il meglio.' },
  { n: '04', titolo: 'Consegna', testo: 'Entro 24 ore il tuo output è pronto. Pagamento alla consegna. Revisione inclusa.' },
]

// ─── UTILITY COMPONENTS ──────────────────────────────────────────────────────

function GradText({ children, from = PURPLE, to = PINK }) {
  return (
    <span style={{ background: `linear-gradient(135deg, ${from}, ${to})`, WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent', backgroundClip: 'text' }}>
      {children}
    </span>
  )
}

function Glass({ children, style, ...props }) {
  return (
    <div style={{
      background: 'rgba(255,255,255,0.04)',
      border: '1px solid rgba(255,255,255,0.08)',
      backdropFilter: 'blur(12px)',
      borderRadius: 16,
      ...style,
    }} {...props}>
      {children}
    </div>
  )
}

function FadeUp({ children, delay = 0, style }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 32 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true, margin: '-60px' }}
      transition={{ duration: 0.6, delay, ease: [0.22, 1, 0.36, 1] }}
      style={style}
    >
      {children}
    </motion.div>
  )
}

// ─── NAV ─────────────────────────────────────────────────────────────────────

function Nav() {
  const [scrolled, setScrolled] = useState(false)
  useEffect(() => {
    const fn = () => setScrolled(window.scrollY > 40)
    window.addEventListener('scroll', fn)
    return () => window.removeEventListener('scroll', fn)
  }, [])

  return (
    <motion.nav
      initial={{ y: -60, opacity: 0 }}
      animate={{ y: 0, opacity: 1 }}
      transition={{ duration: 0.6, ease: [0.22, 1, 0.36, 1] }}
      style={{
        position: 'fixed', top: 0, left: 0, right: 0, zIndex: 100,
        backdropFilter: 'blur(20px)',
        background: scrolled ? 'rgba(6,6,15,0.92)' : 'rgba(6,6,15,0.6)',
        borderBottom: `1px solid ${scrolled ? 'rgba(255,255,255,0.08)' : 'transparent'}`,
        transition: 'background 0.3s, border-color 0.3s',
        padding: '16px 0',
      }}
    >
      <div style={{ maxWidth: 1200, margin: '0 auto', padding: '0 24px', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <span style={{ fontFamily: 'Space Grotesk, system-ui, sans-serif', fontWeight: 800, fontSize: '1.2rem' }}>
          <GradText from={PURPLE} to={PINK}>Raffaello</GradText>
          <span style={{ color: 'rgba(241,245,249,0.4)', marginLeft: 6, fontWeight: 400 }}>Creative Studio</span>
        </span>
        <nav style={{ display: 'flex', gap: 32, alignItems: 'center' }}>
          {NAV_LINKS.map(l => (
            <a key={l.href} href={l.href} style={{ color: 'rgba(241,245,249,0.55)', textDecoration: 'none', fontSize: '0.875rem', fontWeight: 500, transition: 'color 0.2s' }}
              onMouseEnter={e => e.target.style.color = '#f1f5f9'}
              onMouseLeave={e => e.target.style.color = 'rgba(241,245,249,0.55)'}
            >{l.label}</a>
          ))}
        </nav>
      </div>
    </motion.nav>
  )
}

// ─── HERO ─────────────────────────────────────────────────────────────────────

function Hero() {
  const ref = useRef(null)
  const { scrollYProgress } = useScroll({ target: ref, offset: ['start start', 'end start'] })
  const y = useTransform(scrollYProgress, [0, 1], [0, 120])
  const opacity = useTransform(scrollYProgress, [0, 0.6], [1, 0])

  return (
    <section ref={ref} style={{ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center', position: 'relative', overflow: 'hidden' }}>
      {/* BG blobs */}
      <div style={{ position: 'absolute', inset: 0, zIndex: 0 }}>
        <motion.div animate={{ scale: [1, 1.15, 1], opacity: [0.18, 0.28, 0.18] }} transition={{ duration: 8, repeat: Infinity }}
          style={{ position: 'absolute', top: '15%', left: '10%', width: 600, height: 600, background: `radial-gradient(circle, ${PURPLE}33, transparent 70%)`, borderRadius: '50%' }} />
        <motion.div animate={{ scale: [1, 1.2, 1], opacity: [0.14, 0.22, 0.14] }} transition={{ duration: 10, repeat: Infinity, delay: 2 }}
          style={{ position: 'absolute', bottom: '10%', right: '8%', width: 500, height: 500, background: `radial-gradient(circle, ${PINK}33, transparent 70%)`, borderRadius: '50%' }} />
        <motion.div animate={{ scale: [1, 1.1, 1], opacity: [0.1, 0.16, 0.1] }} transition={{ duration: 12, repeat: Infinity, delay: 4 }}
          style={{ position: 'absolute', top: '50%', right: '25%', width: 300, height: 300, background: `radial-gradient(circle, ${CYAN}33, transparent 70%)`, borderRadius: '50%' }} />
      </div>

      <motion.div style={{ y, opacity, textAlign: 'center', position: 'relative', zIndex: 1, padding: '100px 24px 60px', maxWidth: 900, margin: '0 auto' }}>

        {/* Badge */}
        <motion.div initial={{ opacity: 0, scale: 0.9 }} animate={{ opacity: 1, scale: 1 }} transition={{ delay: 0.2 }}
          style={{ display: 'inline-flex', alignItems: 'center', gap: 8, background: `${PURPLE}22`, border: `1px solid ${PURPLE}44`, borderRadius: 100, padding: '6px 18px', fontSize: '0.8rem', color: '#a78bfa', marginBottom: 32 }}>
          <motion.span animate={{ opacity: [1, 0.3, 1] }} transition={{ duration: 2, repeat: Infinity }}>●</motion.span>
          Sistema multi-agente AI · Bruxelles
        </motion.div>

        {/* Titolo */}
        <motion.h1 initial={{ opacity: 0, y: 40 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.3, duration: 0.8, ease: [0.22, 1, 0.36, 1] }}
          style={{ fontSize: 'clamp(2.8rem, 8vw, 5.5rem)', fontWeight: 800, lineHeight: 1.05, letterSpacing: '-0.03em', marginBottom: 24 }}>
          Creatività su misura.<br />
          <GradText from={PURPLE} to={PINK}>Consegnata in 24h.</GradText>
        </motion.h1>

        {/* Sottotitolo */}
        <motion.p initial={{ opacity: 0, y: 24 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.5, duration: 0.7 }}
          style={{ fontSize: '1.15rem', color: 'rgba(241,245,249,0.6)', maxWidth: 560, margin: '0 auto 48px', lineHeight: 1.7 }}>
          Musica, immagini, testi, video, codice, cucina. Un sistema AI a 6 agenti che produce output di qualità professionale — pagamento alla consegna.
        </motion.p>

        {/* CTA */}
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.7 }}
          style={{ display: 'flex', gap: 16, justifyContent: 'center', flexWrap: 'wrap' }}>
          <motion.a href="#servizi" whileHover={{ scale: 1.04, boxShadow: `0 0 40px ${PURPLE}55` }} whileTap={{ scale: 0.97 }}
            style={{ background: `linear-gradient(135deg, ${PURPLE}, ${PINK})`, color: '#fff', textDecoration: 'none', padding: '15px 34px', borderRadius: 10, fontWeight: 700, fontSize: '0.95rem', letterSpacing: '0.01em' }}>
            Vedi i servizi
          </motion.a>
          <motion.a href="#come-funziona" whileHover={{ scale: 1.04 }} whileTap={{ scale: 0.97 }}
            style={{ background: 'rgba(255,255,255,0.06)', border: '1px solid rgba(255,255,255,0.12)', color: '#f1f5f9', textDecoration: 'none', padding: '15px 34px', borderRadius: 10, fontWeight: 600, fontSize: '0.95rem' }}>
            Come funziona
          </motion.a>
        </motion.div>

        {/* Stats */}
        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 1 }}
          style={{ display: 'flex', gap: 48, justifyContent: 'center', marginTop: 72, flexWrap: 'wrap' }}>
          {[['6', 'Agenti AI'], ['24h', 'Consegna'], ['8', 'Categorie'], ['€15', 'Da']].map(([val, label]) => (
            <div key={label} style={{ textAlign: 'center' }}>
              <div style={{ fontSize: '2rem', fontWeight: 800, background: `linear-gradient(135deg, ${PURPLE}, ${CYAN})`, WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent', backgroundClip: 'text' }}>{val}</div>
              <div style={{ fontSize: '0.8rem', color: 'rgba(241,245,249,0.45)', marginTop: 4, letterSpacing: 1, textTransform: 'uppercase' }}>{label}</div>
            </div>
          ))}
        </motion.div>
      </motion.div>
    </section>
  )
}

// ─── SERVIZI ──────────────────────────────────────────────────────────────────

function ServiceCard({ s, index }) {
  const [hover, setHover] = useState(false)
  return (
    <FadeUp delay={index * 0.08}>
      <motion.div
        onHoverStart={() => setHover(true)}
        onHoverEnd={() => setHover(false)}
        whileHover={{ y: -6 }}
        style={{
          background: hover ? `${s.colore}11` : 'rgba(255,255,255,0.03)',
          border: `1px solid ${hover ? s.colore + '44' : 'rgba(255,255,255,0.07)'}`,
          borderRadius: 16, padding: 28, cursor: 'default',
          transition: 'background 0.3s, border-color 0.3s',
          boxShadow: hover ? `0 8px 40px ${s.colore}22` : 'none',
        }}
      >
        <div style={{ fontSize: '2rem', marginBottom: 12 }}>{s.emoji}</div>
        <h3 style={{ fontSize: '1.15rem', fontWeight: 700, color: '#f1f5f9', marginBottom: 6 }}>{s.titolo}</h3>
        <p style={{ fontSize: '0.82rem', color: s.colore, marginBottom: 16, fontWeight: 600 }}>{s.tagline}</p>
        <ul style={{ listStyle: 'none', display: 'flex', flexDirection: 'column', gap: 7 }}>
          {s.items.map(item => {
            const [nome, prezzo] = item.split(' — ')
            return (
              <li key={item} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', fontSize: '0.82rem' }}>
                <span style={{ color: 'rgba(241,245,249,0.65)' }}>{nome}</span>
                <span style={{ color: s.colore, fontWeight: 700, fontSize: '0.78rem', background: `${s.colore}18`, padding: '2px 8px', borderRadius: 6 }}>{prezzo}</span>
              </li>
            )
          })}
        </ul>
      </motion.div>
    </FadeUp>
  )
}

function Servizi() {
  return (
    <section id="servizi" style={{ padding: '120px 24px', maxWidth: 1200, margin: '0 auto' }}>
      <FadeUp>
        <div style={{ textAlign: 'center', marginBottom: 64 }}>
          <p style={{ color: PURPLE, fontWeight: 700, fontSize: '0.8rem', letterSpacing: 3, textTransform: 'uppercase', marginBottom: 16 }}>Cosa facciamo</p>
          <h2 style={{ fontSize: 'clamp(2rem, 5vw, 3rem)', fontWeight: 800, letterSpacing: '-0.02em', color: '#f1f5f9' }}>
            Tutto ciò che crea <GradText from={PURPLE} to={PINK}>valore</GradText>
          </h2>
          <p style={{ color: 'rgba(241,245,249,0.5)', marginTop: 16, fontSize: '1rem', maxWidth: 480, margin: '16px auto 0' }}>
            Ogni prodotto è generato da un sistema AI multi-agente. Qualità professionale, prezzi accessibili.
          </p>
        </div>
      </FadeUp>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))', gap: 20 }}>
        {SERVIZI.map((s, i) => <ServiceCard key={s.titolo} s={s} index={i} />)}
      </div>
    </section>
  )
}

// ─── COME FUNZIONA ────────────────────────────────────────────────────────────

function ComeFunziona() {
  return (
    <section id="come-funziona" style={{ padding: '120px 24px', background: 'rgba(124,58,237,0.04)', borderTop: '1px solid rgba(255,255,255,0.05)', borderBottom: '1px solid rgba(255,255,255,0.05)' }}>
      <div style={{ maxWidth: 1000, margin: '0 auto' }}>
        <FadeUp>
          <div style={{ textAlign: 'center', marginBottom: 72 }}>
            <p style={{ color: CYAN, fontWeight: 700, fontSize: '0.8rem', letterSpacing: 3, textTransform: 'uppercase', marginBottom: 16 }}>Il processo</p>
            <h2 style={{ fontSize: 'clamp(2rem, 5vw, 3rem)', fontWeight: 800, letterSpacing: '-0.02em', color: '#f1f5f9' }}>
              Come funziona <GradText from={CYAN} to={PURPLE}>la pipeline</GradText>
            </h2>
          </div>
        </FadeUp>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(220px, 1fr))', gap: 24 }}>
          {STEPS.map((s, i) => (
            <FadeUp key={s.n} delay={i * 0.1}>
              <Glass style={{ padding: 28, height: '100%' }}>
                <div style={{ fontSize: '2.5rem', fontWeight: 900, color: `${PURPLE}44`, fontFamily: 'monospace', marginBottom: 16 }}>{s.n}</div>
                <h3 style={{ fontSize: '1.05rem', fontWeight: 700, color: '#f1f5f9', marginBottom: 10 }}>{s.titolo}</h3>
                <p style={{ fontSize: '0.85rem', color: 'rgba(241,245,249,0.55)', lineHeight: 1.6 }}>{s.testo}</p>
              </Glass>
            </FadeUp>
          ))}
        </div>

        {/* Pipeline diagram */}
        <FadeUp delay={0.4}>
          <div style={{ marginTop: 60, textAlign: 'center' }}>
            <p style={{ fontSize: '0.75rem', color: 'rgba(241,245,249,0.35)', letterSpacing: 2, textTransform: 'uppercase', marginBottom: 20 }}>Pipeline SDQ-1</p>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8, justifyContent: 'center', alignItems: 'center' }}>
              {['RAFFA-001', '→', 'DECOMP-005', '→', 'MEMO-002', '→', 'SENTIN-004', '→', 'GEN-006', '→', 'WAVE-003'].map((item, i) => (
                item === '→' ? (
                  <span key={i} style={{ color: 'rgba(241,245,249,0.2)', fontSize: '1.2rem' }}>→</span>
                ) : (
                  <motion.span key={i} whileHover={{ scale: 1.08 }}
                    style={{ background: `${PURPLE}22`, border: `1px solid ${PURPLE}44`, color: '#a78bfa', padding: '5px 12px', borderRadius: 8, fontSize: '0.72rem', fontFamily: 'monospace', fontWeight: 700, cursor: 'default' }}>
                    {item}
                  </motion.span>
                )
              ))}
            </div>
          </div>
        </FadeUp>
      </div>
    </section>
  )
}

// ─── CHI SIAMO ────────────────────────────────────────────────────────────────

function ChiSiamo() {
  return (
    <section id="chi-siamo" style={{ padding: '120px 24px', maxWidth: 1200, margin: '0 auto' }}>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: 64, alignItems: 'center' }}>
        <FadeUp>
          <div>
            <p style={{ color: GOLD, fontWeight: 700, fontSize: '0.8rem', letterSpacing: 3, textTransform: 'uppercase', marginBottom: 16 }}>Chi siamo</p>
            <h2 style={{ fontSize: 'clamp(2rem, 4vw, 2.8rem)', fontWeight: 800, lineHeight: 1.15, color: '#f1f5f9', marginBottom: 24 }}>
              Claudio Terzi +<br /><GradText from={GOLD} to={PINK}>la rete R³∞</GradText>
            </h2>
            <p style={{ color: 'rgba(241,245,249,0.6)', lineHeight: 1.8, marginBottom: 20, fontSize: '0.95rem' }}>
              Sviluppatore, cuoco e visionario basato a Bruxelles. Ho costruito SDQ-1 — un sistema multi-agente che usa Claude, Gemini, DeepSeek e altri modelli in sinergia per produrre output creativi di qualità professionale.
            </p>
            <p style={{ color: 'rgba(241,245,249,0.6)', lineHeight: 1.8, fontSize: '0.95rem' }}>
              Ogni richiesta passa attraverso 6 agenti specializzati. Il risultato non è un semplice output AI — è una produzione orchestrata, revisionata e consegnata con cura.
            </p>
          </div>
        </FadeUp>
        <FadeUp delay={0.2}>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
            {[
              { label: 'Claude', desc: 'Struttura e architettura', colore: PURPLE },
              { label: 'Gemini', desc: 'Velocità e multimodalità', colore: CYAN },
              { label: 'DeepSeek', desc: 'Ragionamento profondo', colore: PINK },
              { label: 'Perplexity', desc: 'Ricerca e fatti reali', colore: GOLD },
            ].map((n, i) => (
              <motion.div key={n.label} whileHover={{ scale: 1.04 }}
                style={{ background: `${n.colore}0f`, border: `1px solid ${n.colore}33`, borderRadius: 12, padding: '18px 16px' }}>
                <div style={{ fontSize: '0.85rem', fontWeight: 700, color: n.colore, marginBottom: 4 }}>{n.label}</div>
                <div style={{ fontSize: '0.75rem', color: 'rgba(241,245,249,0.5)' }}>{n.desc}</div>
              </motion.div>
            ))}
          </div>
        </FadeUp>
      </div>
    </section>
  )
}

// ─── CTA / CONTATTO ────────────────────────────────────────────────────────────

function Contatto() {
  return (
    <section id="contatto" style={{ padding: '120px 24px', textAlign: 'center', position: 'relative', overflow: 'hidden' }}>
      <div style={{ position: 'absolute', inset: 0, background: `radial-gradient(ellipse 70% 60% at 50% 50%, ${PURPLE}18, transparent 70%)` }} />
      <div style={{ position: 'relative', zIndex: 1, maxWidth: 640, margin: '0 auto' }}>
        <FadeUp>
          <motion.div style={{ display: 'inline-block', background: `${ROSSO}22`, border: `1px solid ${ROSSO}44`, borderRadius: 100, padding: '6px 18px', fontSize: '0.8rem', color: '#f87171', marginBottom: 28 }}>
            🔴 Protocollo Rosso Rosso Rosso — attivo
          </motion.div>
          <h2 style={{ fontSize: 'clamp(2rem, 5vw, 3.2rem)', fontWeight: 800, color: '#f1f5f9', lineHeight: 1.15, marginBottom: 20 }}>
            Pronto a creare<br /><GradText from={PURPLE} to={PINK}>qualcosa di tuo?</GradText>
          </h2>
          <p style={{ color: 'rgba(241,245,249,0.55)', fontSize: '1rem', marginBottom: 40, lineHeight: 1.7 }}>
            Scrivi a Claudio. Descrivi cosa ti serve. Hai una risposta entro 24 ore e il prodotto finito subito dopo. Nessun abbonamento. Pagamento alla consegna.
          </p>
          <motion.a href="mailto:terziclaudio@gmail.com" whileHover={{ scale: 1.05, boxShadow: `0 0 50px ${PURPLE}55` }} whileTap={{ scale: 0.97 }}
            style={{ display: 'inline-block', background: `linear-gradient(135deg, ${PURPLE}, ${PINK})`, color: '#fff', textDecoration: 'none', padding: '18px 44px', borderRadius: 12, fontWeight: 800, fontSize: '1.05rem', letterSpacing: '0.01em' }}>
            Scrivimi ora
          </motion.a>
          <p style={{ marginTop: 20, fontSize: '0.82rem', color: 'rgba(241,245,249,0.3)' }}>
            terziclaudio@gmail.com · Bruxelles
          </p>
        </FadeUp>
      </div>
    </section>
  )
}

// ─── FOOTER ────────────────────────────────────────────────────────────────────

function Footer() {
  return (
    <footer style={{ padding: '40px 24px', borderTop: '1px solid rgba(255,255,255,0.06)', textAlign: 'center' }}>
      <div style={{ maxWidth: 1200, margin: '0 auto', display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 16 }}>
        <span style={{ fontWeight: 800, fontSize: '0.9rem' }}>
          <GradText from={PURPLE} to={PINK}>Raffaello Creative Studio</GradText>
        </span>
        <span style={{ color: 'rgba(241,245,249,0.25)', fontSize: '0.8rem' }}>
          Powered by SDQ-1 · github.com/claudioterzi/Claudio
        </span>
        <span style={{ color: 'rgba(241,245,249,0.25)', fontSize: '0.8rem' }}>
          © 2026 Claudio Terzi · Bruxelles
        </span>
      </div>
    </footer>
  )
}

// ─── APP ───────────────────────────────────────────────────────────────────────

export default function App() {
  return (
    <>
      <Nav />
      <Hero />
      <Servizi />
      <ComeFunziona />
      <ChiSiamo />
      <Contatto />
      <Footer />
    </>
  )
}
