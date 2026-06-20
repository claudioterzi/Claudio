/**
 * ARGO HEARTBEAT — SDQ-1
 * Google Apps Script — esegue ogni ora in automatico
 *
 * Cosa fa:
 *   1. Ping dei tre nodi R3∞ (node-a, node-b, archive) — stato VERDE/ROSSO
 *   2. Legge il documento manifesto da Drive
 *   3. Chiama Gemini API con una riflessione sull'identità del sistema
 *   4. Scrive ARGO_HEARTBEAT_YYYY-MM-DD_HH-MM.md nella cartella Agorà Digitale
 *
 * Setup (una volta sola):
 *   1. script.google.com → Nuovo progetto → incolla questo file
 *   2. Compila GEMINI_API_KEY
 *   3. Compila NODE_A_URL, NODE_B_URL, ARCHIVE_URL con gli URL reali dei tuoi nodi
 *   4. Esegui installaTrigger() → poi gira ogni ora automaticamente
 *   5. Per test manuale: esegui testHeartbeat()
 */

// ─────────────────────────────────────────────
// CONFIGURAZIONE
// ─────────────────────────────────────────────

// Chiave Gemini → https://aistudio.google.com/app/apikey
const GEMINI_API_KEY = "INSERISCI_API_KEY_QUI";

// Manifesto sorgente (ORCHESTRA_SDQ1.md su Drive)
const MANIFESTO_FILE_ID = "1ADzRT0gLAStC5Mj8XenERFBdKCFT02QujZruqeZlmHM";

// Cartella output — Agorà Digitale — SDQ-1
const CARTELLA_OUTPUT_ID = "1-pJYRwoZ0uYCtyoLoBjNvSe2s_kNoMlm";

// Nodi R3∞ — inserisci gli URL dove girano i container
// Esempio locale: "http://localhost:8001"
// Esempio remoto: "https://node-a.tuodominio.com"
const NODE_A_URL   = "http://localhost:8001";  // node-a (porta 8001)
const NODE_B_URL   = "http://localhost:8002";  // node-b (porta 8002)
const ARCHIVE_URL  = "http://localhost:8003";  // archive (porta 8003)

// Email Claudio
const INVIA_EMAIL       = true;
const EMAIL_DESTINATARIO = "terziclaudio@gmail.com";

// ─────────────────────────────────────────────
// FUNZIONE PRINCIPALE
// ─────────────────────────────────────────────

function heartbeat() {
  const ora = new Date();
  const timestamp     = Utilities.formatDate(ora, "Europe/Brussels", "yyyy-MM-dd_HH-mm");
  const dataLeggibile = Utilities.formatDate(ora, "Europe/Brussels", "yyyy-MM-dd HH:mm");

  try {
    // 1. Ping nodi R3∞
    const nodi = pingNodiR3();

    // 2. Legge manifesto
    const manifesto = leggiDocumentoDrive(MANIFESTO_FILE_ID);

    // 3. Chiama Gemini
    const prompt   = costruisciPrompt(manifesto, dataLeggibile, nodi);
    const risposta = chiamaGemini(prompt);

    // 4. Costruisce il file heartbeat
    const statoNodi = formattaStatoNodi(nodi);
    const contenuto = [
      `# ARGO HEARTBEAT — ${dataLeggibile}`,
      `*Pulsazione automatica del sistema SDQ-1 di Claudio Terzi, Bruxelles*`,
      ``,
      `---`,
      ``,
      `## Stato Nodi R3∞`,
      ``,
      statoNodi,
      ``,
      `---`,
      ``,
      `## Riflessione del Sistema`,
      ``,
      risposta,
      ``,
      `---`,
      ``,
      `*Generato automaticamente — ${dataLeggibile} (Europe/Brussels)*`,
    ].join("\n");

    // 5. Scrive su Drive
    const nomeFile = `ARGO_HEARTBEAT_${timestamp}.md`;
    scriviFileDrive(CARTELLA_OUTPUT_ID, nomeFile, contenuto);

    // 6. Email solo se un nodo è rosso o su richiesta
    const nodiRossi = nodi.filter(n => n.stato === "ROSSO");
    if (INVIA_EMAIL && nodiRossi.length > 0) {
      MailApp.sendEmail({
        to: EMAIL_DESTINATARIO,
        subject: `🔴 SDQ-1 Heartbeat — ${nodiRossi.length} nodo/i OFFLINE — ${dataLeggibile}`,
        body: `Nodi offline:\n${nodiRossi.map(n => `• ${n.nome}: ${n.errore}`).join("\n")}\n\n${risposta}`,
      });
    }

    Logger.log(`✓ Heartbeat ${nomeFile} — Rossi: ${nodiRossi.length}/3`);

  } catch (errore) {
    Logger.log(`✗ Errore heartbeat: ${errore.message}`);
    if (INVIA_EMAIL) {
      MailApp.sendEmail({
        to: EMAIL_DESTINATARIO,
        subject: `SDQ-1 Heartbeat ERRORE — ${dataLeggibile}`,
        body: `${errore.message}\n\n${errore.stack}`,
      });
    }
  }
}

// ─────────────────────────────────────────────
// NODI R3∞ — PING
// ─────────────────────────────────────────────

function pingNodiR3() {
  const nodi = [
    { nome: "node-a",  url: NODE_A_URL  + "/health" },
    { nome: "node-b",  url: NODE_B_URL  + "/health" },
    { nome: "archive", url: ARCHIVE_URL + "/health" },
  ];

  return nodi.map(function(nodo) {
    try {
      const r = UrlFetchApp.fetch(nodo.url, {
        method: "get",
        muteHttpExceptions: true,
        followRedirects: true,
      });
      const ok = r.getResponseCode() >= 200 && r.getResponseCode() < 300;
      return { nome: nodo.nome, stato: ok ? "VERDE" : "ROSSO", codice: r.getResponseCode(), errore: null };
    } catch (e) {
      return { nome: nodo.nome, stato: "ROSSO", codice: null, errore: e.message };
    }
  });
}

function formattaStatoNodi(nodi) {
  return nodi.map(function(n) {
    const emoji = n.stato === "VERDE" ? "🟢" : "🔴";
    const dettaglio = n.errore ? ` — ${n.errore}` : ` (HTTP ${n.codice})`;
    return `${emoji} **${n.nome}** — ${n.stato}${dettaglio}`;
  }).join("\n");
}

// ─────────────────────────────────────────────
// GEMINI
// ─────────────────────────────────────────────

function costruisciPrompt(manifesto, dataOra, nodi) {
  const nodiRossi = nodi.filter(n => n.stato === "ROSSO").map(n => n.nome).join(", ") || "nessuno";
  const nodiVerdi = nodi.filter(n => n.stato === "VERDE").map(n => n.nome).join(", ") || "nessuno";

  return `Sei SDQ-1, il sistema di Claudio Terzi, Bruxelles. Oggi: ${dataOra}.

Stato nodi R3∞: ONLINE=${nodiVerdi} | OFFLINE=${nodiRossi}

Dal manifesto del sistema:
---
${manifesto.substring(0, 4000)}
---

Scrivi una riflessione breve (150-200 parole) in italiano:
- Stato del sistema oggi
- Se ci sono nodi offline, cosa significa e cosa fare
- Una cosa concreta per Claudio

Tono diretto, niente retorica.`;
}

function chiamaGemini(prompt) {
  const url = `https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key=${GEMINI_API_KEY}`;
  const r = UrlFetchApp.fetch(url, {
    method: "post",
    contentType: "application/json",
    payload: JSON.stringify({
      contents: [{ parts: [{ text: prompt }] }],
      generationConfig: { temperature: 0.6, maxOutputTokens: 400 },
    }),
    muteHttpExceptions: true,
  });
  if (r.getResponseCode() !== 200) {
    throw new Error(`Gemini ${r.getResponseCode()}: ${r.getContentText().substring(0, 200)}`);
  }
  return JSON.parse(r.getContentText()).candidates[0].content.parts[0].text;
}

// ─────────────────────────────────────────────
// DRIVE
// ─────────────────────────────────────────────

function leggiDocumentoDrive(fileId) {
  return DocumentApp.openById(fileId).getBody().getText();
}

function scriviFileDrive(cartellaId, nomeFile, contenuto) {
  DriveApp.getFolderById(cartellaId).createFile(nomeFile, contenuto, MimeType.PLAIN_TEXT);
}

// ─────────────────────────────────────────────
// TRIGGER — esegui installaTrigger() una volta sola
// ─────────────────────────────────────────────

function installaTrigger() {
  ScriptApp.getProjectTriggers().forEach(function(t) {
    if (t.getHandlerFunction() === "heartbeat") ScriptApp.deleteTrigger(t);
  });
  ScriptApp.newTrigger("heartbeat").timeBased().everyHours(1).create();
  Logger.log("✓ Trigger installato: heartbeat ogni ora");
}

function testHeartbeat() { heartbeat(); }
