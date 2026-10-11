/* Original illustrative scripts. Concept: Claudio Terzi. No real bookings. */
(() => {
  const a = (id, title, role, when, depends_on = [], search_query = '', draft = '') => ({id, title, role, when, depends_on, search_query, draft, status:'proposed'});
  const c = (text, detail) => ({text, detail});
  const scene = (title, goal, actions) => ({title, goal, actions});
  window.FABBRICA_LEVELS = [
    {name:'Essenziale', people:'Tu + un musicista', scope:'Un luogo, una prova',
      title:'Una canzone. Una stanza. Il primo passo.',
      summary:'Cominci da una prova riservata. Un musicista ti accompagna, scegliete una canzone e la portate fino in fondo. Il pubblico può aspettare.',
      conditions:[c('Uno spazio tranquillo','Una stanza disponibile, tempi e volume concordati.'),c('Un accompagnatore adatto','Disponibilità, compenso e capacità di accompagnare un principiante da verificare.'),c('Una scelta tua','Canzone e obiettivo della prova scelti insieme, senza obbligo di registrarti.')],
      scenes:[scene('Scegliere una piccola prima volta','Si definisce un obiettivo alla tua portata.',[
        a('A1','Scegliere canzone, durata e budget massimo','Tu','Prima dei contatti'),
        a('A2','Concordare una prova privata con un musicista','Tu e un musicista','Dopo una risposta e un prezzo accettato',['A1'],'musicista accompagnamento canto principianti prova privata','Buongiorno, cerco un accompagnamento per provare una sola canzone, senza pubblico. Possiamo concordare durata, disponibilità e costo?')]),
        scene('Dare spazio alla voce','Una prova, con la possibilità di fermarti e ricominciare.',[
        a('A3','Verificare lo spazio e provare la canzone insieme','Tu e il musicista','Nel momento concordato',['A2'])])],
      questions:['Quale canzone conosci bene?','Dove vorresti provare e con quale budget?'],
      alternative:'Se non trovi un accompagnatore, puoi iniziare da una lezione individuale. Se preferisci rimandare, la prenotazione segue le condizioni concordate.'},
    {name:'Curata',people:'Tu, un musicista e due persone fidate',scope:'Un piccolo palco',
      title:'La tua prima canzone, davanti a qualcuno.',
      summary:'Un locale tranquillo, una prova riservata e due persone che scegli tu. Il musicista aspetta il tuo segnale. Decidi fino all’ultimo se salire sul palco.',
      conditions:[c('Un contesto rassicurante','Numero di presenti, durata e possibilità di fermarti scelti da te.'),c('Locale e musicista disponibili','Data, costi, strumenti e autorizzazione del locale da confermare.'),c('Un segnale condiviso','Attacco, conclusione e possibilità di rinviare concordati nella prova.')],
      scenes:[scene('Trovare la misura giusta','Il tuo desiderio guida la preparazione.',[
        a('A1','Scegliere canzone, budget e persone da invitare','Tu','Prima di cercare disponibilità'),
        a('A2','Verificare un piccolo locale e un musicista','Tu, referente del locale e musicista','Prima di proporre una data definitiva',['A1'],'piccolo locale musica dal vivo serata open mic','Buongiorno, vorrei organizzare una prima esibizione di una sola canzone in un contesto tranquillo. Avete disponibilità per una prova e un breve momento dal vivo? Potete indicare condizioni e costi?')]),
        scene('Preparare il momento','Si conoscono tempi, costi e limiti.',[
        a('A3','Accettare data, durata e costi espliciti','Tu e i partecipanti','Dopo aver ricevuto le disponibilità',['A2']),
        a('A4','Fare la prova riservata e invitare le persone scelte','Tu e il musicista','Prima dell’esibizione',['A3'])]),
        scene('Scegliere di esserci','La regia accompagna la tua decisione.',[
        a('A5','Ricontrollare strumenti, presenze e disponibilità a esibirti','Tu, musicista e locale','15 minuti prima, come margine proposto',['A4']),
        a('A6','Dare il segnale quando ti senti pronto','Tu','All’orario concordato, con margine',['A5'])])],
      questions:['Quale canzone vorresti cantare?','Chi vorresti vicino?','In quale città e con quale budget?'],
      alternative:'La prova privata può diventare l’esperienza se preferisci fermarti lì. Gli inviti non autorizzano nessuno a metterti sotto pressione.'},
    {name:'Coordinata',people:'Una piccola squadra e i tuoi invitati',scope:'Una serata costruita intorno a una canzone',
      title:'Per una sera, quel piccolo palco è tuo.',
      summary:'La tua canzone diventa il centro di una serata: una sala raccolta, luci preparate, un accompagnamento dal vivo e gli invitati scelti da te. Ogni persona conosce il suo ingresso.',
      conditions:[c('Un evento sostenibile','Dimensione, costo totale, accessibilità e luogo adatto.'),c('Una squadra con ruoli chiari','Musicista, referente del locale e persona che segue luci e tempi.'),c('Una sequenza provata','Arrivo, prova, accoglienza e attacco della canzone con margini reali.')],
      scenes:[scene('Dare una forma alla serata','Il budget delimita la dimensione del progetto.',[
        a('A1','Definire ospiti, budget e cose da evitare','Tu','Prima dei preventivi'),
        a('A2','Raccogliere disponibilità e prezzi per locale e accompagnamento','Referente organizzativo','Prima di qualsiasi conferma',['A1'],'piccolo spazio eventi privati musica dal vivo')]),
        scene('Mettere d’accordo la squadra','Ogni incarico ha un titolare e una scadenza.',[
        a('A3','Approvare il costo totale e assegnare i ruoli','Tu e referente organizzativo','Prima degli accordi finali',['A2']),
        a('A4','Confermare presenze e provare scaletta, luci e suono','Squadra e invitati','Nelle ore e nei giorni concordati',['A3'])]),
        scene('Far scorrere il momento','La partenza segue un controllo delle condizioni.',[
        a('A5','Verificare che sala, accompagnamento e persona siano pronti','Referente sul posto','Prima dell’ingresso',['A4']),
        a('A6','Dare il via e seguire la scaletta con possibilità di pausa','Referente e partecipanti','All’orario concordato',['A5'])])],
      questions:['Quante persone vorresti presenti?','Quali dettagli renderebbero la serata tua?','Qual è il tetto di spesa?'],
      alternative:'Se manca un ruolo o una risorsa, si riduce l’allestimento prima di confermare la serata. Il momento centrale può restare una canzone con accompagnamento essenziale.'},
    {name:'Ambiziosa',people:'Persone care in tre città',scope:'Un palco, presenze vicine e lontane',
      title:'Le persone lontane trovano un posto in prima fila.',
      summary:'Canti nella tua città. Le persone che hai scelto partecipano da altri due luoghi: una presenza dal vivo, una dedica, una risposta musicale. La distanza diventa parte della serata.',
      conditions:[c('Disponibilità nei diversi fusi','Data e orari compatibili per tutti i gruppi.'),c('Collegamenti provati','Audio, video, connessione e un referente per luogo.'),c('Sorprese con un confine','Partecipanti autorizzati e limiti concordati; nessuna persona esclusa viene coinvolta.'),c('Un’alternativa al collegamento','Contributi registrati volontariamente, da presentare come registrazioni.')],
      scenes:[scene('Disegnare l’incontro','Le persone lontane scelgono come partecipare.',[
        a('A1','Scegliere i partecipanti e i confini delle sorprese','Tu','Prima degli inviti'),
        a('A2','Confermare tre referenti e una finestra oraria comune','Un referente per luogo','Dopo disponibilità esplicite',['A1'])]),
        scene('Provare la distanza','Si provano passaggi e tempi, non solo le apparecchiature.',[
        a('A3','Concordare luoghi, costi, collegamenti e autorizzazioni','Referenti e fornitori','Prima di prenotare',['A2']),
        a('A4','Fare una prova remota e preparare contributi di riserva','Musicisti e referenti','Prima della serata',['A3'])]),
        scene('Far incontrare le presenze','Gli interventi seguono una sequenza condivisa.',[
        a('A5','Ricevere il segnale di pronto da tutti i luoghi','Referente di regia','Prima dell’inizio',['A4']),
        a('A6','Alternare canzone, dediche e risposte musicali','Tu e partecipanti','Secondo i segnali della regia',['A5'])])],
      questions:['Quali persone vorresti coinvolgere?','In quali città si trovano?','Che cosa vuoi sapere prima e che cosa può sorprenderti?'],
      alternative:'Se una connessione cade, la scaletta passa al contributo successivo o a una registrazione autorizzata e dichiarata. Gli interventi musicali a distanza si alternano per evitare problemi di ritardo audio.'},
    {name:'Straordinaria',people:'Cinque città, cinque squadre',scope:'Un unico spettacolo costruito a distanza',
      title:'La tua canzone attraversa cinque città.',
      summary:'Tu inizi in una piccola sala. In un’altra città risponde una voce, in una terza entra un gruppo di musicisti. Cinque luoghi diventano capitoli dello stesso spettacolo, preparato intorno alla tua prima canzone.',
      conditions:[c('Un progetto condiviso e finanziato','Ruoli, partecipanti, costi e autorizzazioni espliciti per tutti i luoghi.'),c('Una regia centrale e cinque referenti','Ogni gruppo risponde delle proprie presenze, prove e tempi.'),c('Un brano e contributi utilizzabili','Si verificano permessi necessari per musica, luoghi, immagini ed eventuale diffusione.'),c('Una prova generale completa','Audio e video provati con passaggi sequenziali, margini e segnali di conferma.'),c('Un’alternativa per ogni collegamento','Nessun luogo deve essere indispensabile alla riuscita del momento centrale.')],
      scenes:[scene('Dare un perimetro all’improbabile','Una visione grande deve avere confini concreti.',[
        a('A1','Definire significato, cinque luoghi candidati e budget massimo','Tu e responsabile organizzativo','Prima di coinvolgere le squadre'),
        a('A2','Trovare un referente disponibile per ogni città','Responsabile organizzativo','Prima di fissare la data',['A1'])]),
        scene('Costruire gli accordi','Ogni sì deve coprire una parte verificabile.',[
        a('A3','Raccogliere disponibilità, costi e vincoli dei cinque luoghi','I cinque referenti','Prima degli impegni economici',['A2']),
        a('A4','Approvare budget, permessi e partecipazione di tutte le squadre','Tu e responsabili','Prima delle prenotazioni',['A3'])]),
        scene('Scrivere la partitura dei gesti','Le città si passano il testimone.',[
        a('A5','Assegnare un contributo e un segnale di ingresso a ogni luogo','Regia e musicisti','Durante la preparazione',['A4']),
        a('A6','Preparare collegamenti e alternative registrate autorizzate','Referenti tecnici','Prima della prova generale',['A5'])]),
        scene('Provare tutto, anche gli imprevisti','Una prova rivela le condizioni ancora mancanti.',[
        a('A7','Eseguire la prova generale con tutti i passaggi e i fusi orari','Tutte le squadre','Prima del giorno scelto',['A6']),
        a('A8','Correggere ritardi e provare il percorso senza una città','Regia e referenti','Dopo la prova generale',['A7'])]),
        scene('Far accadere l’incontro','Il via dipende dai segnali ricevuti.',[
        a('A9','Raccogliere le conferme di pronto e decidere la versione eseguibile','Responsabile della regia','Prima della partenza',['A8']),
        a('A10','Aprire la canzone e guidare il passaggio fra le cinque città','Tu, regia e partecipanti','Nella finestra concordata',['A9'])])],
      questions:['Chi dovrebbe dare un senso a questi cinque luoghi?','Quale budget può sostenere prove, persone e collegamenti?','Vuoi un’esperienza privata o una diffusione concordata?'],
      alternative:'Lo spettacolo è modulare: una città può essere saltata o sostituita da un contributo registrato e dichiarato. Si alternano gli interventi invece di promettere musica remota simultanea senza ritardi. Se budget o conferme mancano, la regia propone una versione con meno luoghi.'}
  ];
})();
