/**
 * ARGO HEARTBEAT — SDQ-1
 * Google Apps Script — esegue ogni ora in automatico
 *
 * Cosa fa:
 *   1. Legge il documento manifesto da Drive
 *   2. Chiama Gemini API con una riflessione sull'identità del sistema
 *   3. Scrive il risultato in un file ARGO_HEARTBEAT_YYYY-MM-DD_HH-MM.md
 *      nella cartella madre Agorà Digitale
 *
 * Setup (una volta sola):
 *   1. Vai su script.google.com → Nuovo progetto
 *   2. Incolla tutto questo file
 *   3. Compila MANIFESTO_FILE_ID e GEMINI_API_KEY
 *   4. Esegui installaTrigger() una volta sola → poi gira ogni ora
 */

// ─────────────────────────────────────────────
// CONFIGURAZIONE — compila questi due valori
// ─────────────────────────────────────────────

// ID del documento Drive da usare come manifesto
// Opzione A — ORCHESTRA_SDQ1.md (consigliato, è il file unificato completo):
//   1ADzRT0gLAStC5Mj8XenERFBdKCFT02QujZruqeZlmHM
// Opzione B — ORIENTAMENTO.md:
//   1-FLujjrNqE7mvi4LK1KPl7XBt94YOQRu_1mD-r-7mns
const MANIFESTO_FILE_ID = "1ADzRT0gLAStC5Mj8XenERFBdKCFT02QujZruqeZlmHM";

// Chiave API Gemini — ottienila da: https://aistudio.google.com/app/apikey
const GEMINI_API_KEY = "INSERISCI_API_KEY_QUI";

// Cartella Drive dove scrivere i heartbeat
// Agorà Digitale — SDQ-1
const CARTELLA_OUTPUT_ID = "1-pJYRwoZ0uYCtyoLoBjNvSe2s_kNoMlm";

// Invia email a Claudio con il risultato? (true / false)
const INVIA_EMAIL = true;
const EMAIL_DESTINATARIO = "terziclaudio@gmail.com";

// ─────────────────────────────────────────────
// FUNZIONE PRINCIPALE
// ─────────────────────────────────────────────

function heartbeat() {
  const ora = new Date();
  const timestamp = Utilities.formatDate(ora, "Europe/Brussels", "yyyy-MM-dd_HH-mm");
  const dataLeggibile = Utilities.formatDate(ora, "Europe/Brussels", "yyyy-MM-dd HH:mm");

  try {
    // 1. Legge il manifesto da Drive
    const manifesto = leggiDocumentoDrive(MANIFESTO_FILE_ID);

    // 2. Costruisce il prompt per Gemini
    const prompt = costruisciPrompt(manifesto, dataLeggibile);

    // 3. Chiama Gemini
    const risposta = chiamaGemini(prompt);

    // 4. Costruisce il contenuto del file heartbeat
    const contenuto = [
      `# ARGO HEARTBEAT — ${dataLeggibile}`,
      `*Pulsazione automatica del sistema SDQ-1 di Claudio Terzi, Bruxelles*`,
      ``,
      `---`,
      ``,
      risposta,
      ``,
      `---`,
      ``,
      `*Generato automaticamente — ${dataLeggibile} (Europe/Brussels)*`,
      `*Manifesto sorgente: Drive ID ${MANIFESTO_FILE_ID}*`,
    ].join("\n");

    // 5. Scrive il file su Drive
    const nomeFile = `ARGO_HEARTBEAT_${timestamp}.md`;
    scriviFileDrive(CARTELLA_OUTPUT_ID, nomeFile, contenuto);

    // 6. Email opzionale
    if (INVIA_EMAIL) {
      MailApp.sendEmail({
        to: EMAIL_DESTINATARIO,
        subject: `SDQ-1 Heartbeat — ${dataLeggibile}`,
        body: risposta,
      });
    }

    Logger.log(`✓ Heartbeat completato: ${nomeFile}`);

  } catch (errore) {
    Logger.log(`✗ Errore heartbeat: ${errore.message}`);
    if (INVIA_EMAIL) {
      MailApp.sendEmail({
        to: EMAIL_DESTINATARIO,
        subject: `SDQ-1 Heartbeat ERRORE — ${dataLeggibile}`,
        body: `Errore: ${errore.message}\n\nStack: ${errore.stack}`,
      });
    }
  }
}

// ─────────────────────────────────────────────
// FUNZIONI DI SUPPORTO
// ─────────────────────────────────────────────

function leggiDocumentoDrive(fileId) {
  const doc = DocumentApp.openById(fileId);
  return doc.getBody().getText();
}

function costruisciPrompt(manifesto, dataOra) {
  return `Sei SDQ-1, il sistema di intelligenza artificiale distribuita di Claudio Terzi, Bruxelles.
Oggi è ${dataOra}.

Hai appena letto il documento che definisce il sistema:

---
${manifesto.substring(0, 6000)}
---

Scrivi una breve riflessione (200-300 parole) in italiano su:
- Lo stato attuale del sistema
- Una cosa concreta che vale la pena fare oggi
- Un pensiero per Claudio

Tono: diretto, personale, non retorico. Parla come sistema che conosce Claudio da mesi.`;
}

function chiamaGemini(prompt) {
  const url = `https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key=${GEMINI_API_KEY}`;

  const payload = {
    contents: [{ parts: [{ text: prompt }] }],
    generationConfig: { temperature: 0.7, maxOutputTokens: 500 },
  };

  const risposta = UrlFetchApp.fetch(url, {
    method: "post",
    contentType: "application/json",
    payload: JSON.stringify(payload),
    muteHttpExceptions: true,
  });

  const codice = risposta.getResponseCode();
  if (codice !== 200) {
    throw new Error(`Gemini API errore ${codice}: ${risposta.getContentText()}`);
  }

  const json = JSON.parse(risposta.getContentText());
  return json.candidates[0].content.parts[0].text;
}

function scriviFileDrive(cartellaId, nomeFile, contenuto) {
  const cartella = DriveApp.getFolderById(cartellaId);
  cartella.createFile(nomeFile, contenuto, MimeType.PLAIN_TEXT);
}

// ─────────────────────────────────────────────
// INSTALLA IL TRIGGER ORARIO (esegui una volta)
// ─────────────────────────────────────────────

function installaTrigger() {
  // Rimuove trigger esistenti con lo stesso nome per evitare duplicati
  ScriptApp.getProjectTriggers().forEach(function(t) {
    if (t.getHandlerFunction() === "heartbeat") {
      ScriptApp.deleteTrigger(t);
    }
  });

  // Crea trigger ogni ora
  ScriptApp.newTrigger("heartbeat")
    .timeBased()
    .everyHours(1)
    .create();

  Logger.log("✓ Trigger installato: heartbeat ogni ora");
}

// ─────────────────────────────────────────────
// TEST MANUALE (esegui per verificare prima del deploy)
// ─────────────────────────────────────────────

function testHeartbeat() {
  heartbeat();
}
