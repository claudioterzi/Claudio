# TERZI PARFUMS — AURA-50 — MASTER

## Concept + Database Essenze + Operazioni — documento unico

> "Costruire davvero, non fingere insieme." — Protocollo Rosso Rosso Rosso

**Autore:** Claudio Terzi — Bruxelles · **Stato:** master operativo / revisionabile · **Data:** giugno 2026
*Questo documento fonde e sostituisce CONCEPT_AURA-50 ed ESSENZE_AURA-50.*

---

# PARTE I — CONCEPT

## 1. La frase sola

Un atelier che non ti vende un profumo: ti aiuta a **scoprire la tua formula**, te la costruisce davvero, e te la consegna scritta — tua, tracciata, ripetibile. La concorrenza vende un flacone e una storia. Noi vendiamo il flacone, **la formula esatta** (per numero di essenza) e l'esperienza che l'ha generata.

## 2. Il problema reale

La "personalizzazione" oggi è quasi sempre finta: scegli tra flaconi già fatti e ci incidi il nome. La nicchia è cara e opaca: non sai cosa indossi, non puoi rifarlo, non è tuo. Lo spazio vuoto: *esperienza guidata + creazione reale su misura + trasparenza totale della formula*. Lì entriamo.

## 3. La promessa — e cosa NON promettiamo

**Promettiamo:** intervista che parte da memoria e desiderio; formula costruita su 158 essenze (motore IA propone, naso umano decide); prodotto fisico + scheda con la formula in percentuali + tracciabilità.

**NON promettiamo (categoria C — igiene epistemica):**

- Niente "feromoni che ti fanno desiderare" — nessuna prova scientifica.
- Niente "frequenze", "DNA che vibra", "aura". Vendiamo chimica e percezione.
- Niente "IA che legge l'anima". L'IA traduce parole in famiglie olfattive; sceglie l'esperto.

Il nucleo vero (A) basta: **l'olfatto è il senso più legato a memoria ed emozione.** Su quello costruiamo, senza barare.

## 4. IL PONTE — i 10 registri emozionali

Questo è il cuore del sistema: il meccanismo che lega l'**intervista** (cattura emozione/desiderio) al **database** (essenze taggate per emozione). Ogni essenza porta uno o due registri. Il motore mappa: *risposte del cliente → registri dominanti → pool di essenze per numero → piramide*.

| Codice | Registro                   | Cosa dice addosso                    |
|--------|----------------------------|--------------------------------------|
| **SLA** | Slancio / Energia         | apertura, ottimismo lucido, partenza |
| **ARI** | Aria / Purezza            | pulizia, leggerezza, distanza nobile |
| **GIO** | Gioco / Leggerezza        | allegria, freschezza, non-serietà    |
| **SEN** | Sensualità / Carne        | desiderio, pelle, vicinanza          |
| **MIS** | Mistero / Profondità      | non-detto, profondità che attrae     |
| **FOR** | Forza / Autorità          | presenza, comando, sicurezza         |
| **CON** | Conforto / Calore         | abbraccio, casa, dolcezza            |
| **MEM** | Memoria / Malinconia      | nostalgia, tempo, eleganza triste    |
| **TER** | Terra / Radice            | radicamento, verità, natura          |
| **VIT** | Vitalità verde / Risveglio| lucidità, primavera, taglio fresco   |

## 5. Il flusso (con esempi numerati)

1. **Intervista AURA** — 6–8 domande di scavo (l'odore che ti ferma, il ricordo, cosa vuoi che senta chi ti avvicina, cosa odi).
2. **Motore** — traduce in registri. Es.: cliente "mistero + pelle calda" → MIS+SEN → pool {#128 oud, #134 labdano, #141 ambroxan, #146 muschio bianco, #122 vetiver, #158 tabacco}.
3. **Composizione** — piramide testa/cuore/fondo, il naso valida e firma.
4. **Creazione fisica** — miscela, macerazione, filtraggio, imbottigliamento.
5. **Consegna trasparente** — flacone + scheda formula (per numero) + QR firma olfattiva.

## 6. Architettura del prodotto (3 livelli)

| Livello | Nome               | Cosa è                                                  | Funzione                        |
|---------|--------------------|---------------------------------------------------------|---------------------------------|
| Entry   | **OLFACTO DROP**   | kit scoperta: campioni per registro + quiz              | far entrare, educare, profilare |
| Core    | **AURA-50**        | fragranza firma 50 ml su misura                         | il prodotto vero, il margine    |
| Premium | **Bespoke Atelier**| sessione completa, macerazione lunga, formula riservata | alto prezzo, alta relazione     |

- **Refill** della stessa formula → margine ricorrente.

## 7. Architettura tecnica (SDQ-1)

Quiz interattivo (HTML/JS, esiste) · database 158 essenze (questo file) · motore di suggerimento come agente dentro SDQ-1 (RAFFA intento → DECOMP profilo → GEN piramide → SENTIN blocca i claim falsi) · generatore etichette SVG · scheda tecnica HTML auto-generata · controllo IFRA per ogni formula.

## 8. Esperienza / unboxing

Flacone (vetro scuro, etichetta minimale col nome-formula) + scheda formula in percentuali e numeri + una riga di racconto *accanto* al dato + QR firma olfattiva. Il rito comunica la promessa: **sai cosa indossi.**

## 9. Modello di business

OLFACTO DROP a basso prezzo d'ingresso, scontabile sul core (converte, non guadagna). AURA-50 premium ma sotto la nicchia opaca: il valore è trasparenza + bespoke, non i millilitri. Bespoke alto/relazione. Refill ricorrente. *Si prezza il tempo del naso, la conformità e l'esperienza — non l'essenza.*

## 10. Posizionamento

Terzi Parfums, Bruxelles. Artigianato + onestà radicale. Nemico: la nicchia cara e opaca. Vessillo: **la formula è tua.**

## 11. Criterio di verità (H2 — non negoziabile)

Il progetto è vivo solo se esiste `contatti.jsonl` con clienti reali paganti:

```json
{ "nome":"...", "data":"...", "prodotto":"AURA-50", "pagato":true, "formula":"CLAUDIO-001", "verifica":"ricevuta/foto/testimonianza" }
```

1000 commit e un quiz bellissimo, file vuoto = **morto**. La domanda è "qualcuno ha pagato e indossato?", non "è bello?".

## 12. Roadmap

| Fase  | Obiettivo                                     | Superamento                    |
|-------|-----------------------------------------------|--------------------------------|
| 0 ora | concept+quiz+158+motore                       | esiste (✓ parziale)            |
| 1 MVP | **1 cliente reale pagante**                   | prima riga in `contatti.jsonl` |
| 2     | 10 clienti, motore raffinato, formule IFRA-ok | 10 righe, 0 problemi sicurezza |
| 3     | sito + OLFACTO DROP spedibile + refill        | primo ordine online evaso      |
| 4     | piccola produzione, bespoke su appuntamento   | margine ricorrente positivo    |

---

# PARTE II — DATABASE ESSENZE (158)

Formato: `N. Nome — famiglia/ruolo · tipo(IFRA) · carattere · EMO: registro`. N = Naturale, S = Sintetico.

## A. Agrumi / Esperidati — testa (001–016)

1. Bergamotto Calabria — agrume/testa · N(FCF) · frizzante-amaro elegante · EMO: SLA, ARI
2. Limone Sicilia — agrume/testa · N(FCF) · pulito tagliente · EMO: SLA, VIT
3. Mandarino rosso — agrume/testa · N · dolce solare · EMO: GIO, SLA
4. Mandarino verde — agrume/testa · N · aspro verde · EMO: VIT, SLA
5. Arancia dolce — agrume/testa · N · succosa allegra · EMO: GIO
6. Arancia amara (bigarade) — agrume/testa · N · secca nobile · EMO: ARI, SLA
7. Pompelmo — agrume/testa · S/N · amaro scintillante · EMO: SLA, VIT
8. Lime — agrume/testa · N(fototox.) · verde-acido · EMO: VIT, GIO
9. Cedro (citron) — agrume/testa · N · tenue, carta · EMO: ARI
10. Petitgrain — agrume/testa · N · legnoso-foglia amara · EMO: VIT, ARI
11. Neroli — agrume-fiore/testa-cuore · N · miele bianco · EMO: SEN, ARI
12. Yuzu — agrume/testa · S/N · orientale vibrante · EMO: SLA, GIO
13. Clementina — agrume/testa · N · morbida dolce · EMO: GIO, CON
14. Kumquat — agrume/testa · S · buccia amara brillante · EMO: GIO, VIT
15. Aldeide C-10 — agrume astratto/testa · S · brillantezza buccia · EMO: SLA, ARI
16. Accordo Cologne — esperidato astratto/testa · S · classico fresco · EMO: ARI, SLA

## B. Aromatiche / Erbe — testa-cuore (017–030)

17. Lavanda — aromatica/testa-cuore · N · pulita barbiere · EMO: ARI, MEM
18. Lavandina — aromatica/testa · N · canforata · EMO: ARI, VIT
19. Rosmarino — aromatica/testa · N · fresco eucaliptico · EMO: VIT, SLA
20. Salvia sclarea — aromatica/cuore · N · ambrata-sudore nobile · EMO: SEN, TER
21. Menta piperita — aromatica/testa · N · gelo vivace · EMO: VIT, SLA
22. Basilico — aromatica/testa · N · verde-anice · EMO: VIT, GIO
23. Timo — aromatica/testa · N · caldo medicinale · EMO: FOR, VIT
24. Artemisia — aromatica/testa · N · amara, assenzio · EMO: MIS, VIT
25. Eucalipto — aromatica/testa · N · canfora, respiro · EMO: VIT, ARI
26. Anice / Anetolo — aromatica/testa · N/S · liquirizia dolce · EMO: GIO, CON
27. Estragone — aromatica/testa · N · anice fine · EMO: VIT, GIO
28. Geranio — fiore-aromatica/cuore · N · rosato-mentolato (ponte) · EMO: VIT, SEN
29. Menta verde — aromatica/testa · N · dolce gomma · EMO: GIO, VIT
30. Fava tonka (cumarina) — gourmand/fondo · N/S(limite) · fieno-mandorla-tabacco · EMO: CON, MEM

## C. Spezie — cuore (031–046)

31. Pepe nero — spezia/cuore · N · secco pungente · EMO: FOR, MIS
32. Pepe rosa — spezia/testa-cuore · N · frizzante rosato · EMO: GIO, SLA
33. Cardamomo — spezia/cuore · N · fresco elegante · EMO: ARI, MIS
34. Zenzero — spezia/testa-cuore · N · caldo frizzante · EMO: SLA, FOR
35. Noce moscata — spezia/cuore · N · dolce-legnosa avvolgente · EMO: CON, FOR
36. Chiodi di garofano — spezia/cuore · N(limite) · caldo denso · EMO: FOR, CON
37. Cannella corteccia — spezia/cuore · N(limite) · rossa calda · EMO: CON, FOR
38. Coriandolo — spezia/testa-cuore · N · speziato-agrumato soft · EMO: ARI, GIO
39. Cumino — spezia/cuore · N(prudenza) · sudato-animalico · EMO: SEN, FOR
40. Curcuma — spezia/cuore · S · terrosa-dorata · EMO: TER, MIS
41. Zafferano (safraleine) — spezia-cuoio/cuore · S · cuoio dorato · EMO: MIS, FOR
42. Peperoncino accordo — spezia/cuore · S · caldo astratto · EMO: FOR
43. Bacche di ginepro — spezia/testa · N · gin resinoso · EMO: VIT, ARI
44. Pimento (allspice) — spezia/cuore · N · mista calda · EMO: CON, FOR
45. Cuoio-zafferano accordo — cuoio/cuore-fondo · S · moderno caldo · EMO: MIS, FOR
46. Cumino tostato accordo — spezia/cuore · S · pelle calda · EMO: SEN, FOR

## D. Fiori bianchi — cuore (047–060)

47. Gelsomino grandiflorum — fiore bianco/cuore · N · solare indolico carnale · EMO: SEN
48. Gelsomino sambac — fiore bianco/cuore · N · verde-tè · EMO: SEN, ARI
49. Tuberosa — fiore bianco/cuore · N · cremosa narcotica · EMO: SEN, FOR
50. Fiori d'arancio (assoluta) — fiore bianco/cuore · N · miele-cera sensuale · EMO: SEN, CON
51. Gardenia (accordo) — fiore bianco/cuore · S · verde-cremosa · EMO: SEN, ARI
52. Ylang-ylang — fiore/cuore · N · banana-fiore esotico · EMO: SEN, GIO
53. Frangipane — fiore/cuore · S · solare lattiginoso · EMO: GIO, SEN
54. Magnolia — fiore/cuore · S/N · agrume-petalo fresca · EMO: ARI, GIO
55. Mughetto — fiore/cuore · S(no Lilial) · verde-acquoso pulito · EMO: ARI, VIT
56. Caprifoglio — fiore/cuore · S · miele-nettare · EMO: GIO, CON
57. Fior di loto — fiore/cuore · S · acquatico-fiorito · EMO: ARI
58. Champaca — fiore/cuore · N/S · tè-fiorito dorato · EMO: MIS, SEN
59. Osmanthus — fiore-frutto/cuore · N · albicocca-cuoio-fiore · EMO: MEM, SEN
60. Narciso — fiore/cuore · N · fieno-verde animalico · EMO: MEM, MIS

## E. Fiori — cuore (061–082)

61. Rosa damascena — fiore/cuore · N · miele-vino regina · EMO: SEN, MEM
62. Rosa centifolia — fiore/cuore · N · fresca verde-petalo · EMO: ARI, MEM
63. Rosa ossido (damascenone) — fiore astratto/cuore · S · frizzante-rosato · EMO: SLA, SEN
64. Geranio rosa — fiore/cuore · N · rosato-mentolato · EMO: VIT, SEN
65. Violetta foglia — verde/testa-cuore · N · acquosa, cetriolo · EMO: VIT, MEM
66. Violetta fiore (ionone) — fiore cipriato/cuore · S · dolce retro · EMO: MEM, CON
67. Iris / Orris — radice cipriata/cuore · N(caro) · fredda lussuosa · EMO: MEM, ARI
68. Iris (irone) — radice cipriata/cuore · S · accessibile · EMO: MEM, ARI
69. Peonia (accordo) — fiore/cuore · S · rosa-acquosa fresca · EMO: GIO, ARI
70. Lillà — fiore/cuore · S · fiorito-verde primavera · EMO: VIT, MEM
71. Fiori di ciliegio — fiore/cuore · S · soft cipriato · EMO: GIO, MEM
72. Eliotropio — fiore-gourmand/cuore · S · mandorla-cipria-vaniglia · EMO: CON, MEM
73. Mimosa — fiore/cuore · N · polverosa-verde gialla · EMO: MEM, GIO
74. Garofano fiore — fiore-spezia/cuore · N/S · pepato eugenolo · EMO: FOR, MEM
75. Lavanda assoluta — fiore/cuore · N · densa miele · EMO: MEM, CON
76. Camomilla blu — aromatica-fiore/cuore · N · mela-erbacea · EMO: CON, VIT
77. Loto rosa — fiore/cuore · S · fiorito-fruttato · EMO: ARI, GIO
78. Fresia — fiore/cuore · S · pulita pera-fiore · EMO: ARI, GIO
79. Ibisco accordo — fiore/cuore · S · tropicale · EMO: GIO
80. Cera d'api (assoluta) — fiore-animalico/cuore-fondo · N · miele-fieno · EMO: SEN, MEM
81. Immortelle — aromatica/cuore-fondo · N · curry-miele-fieno · EMO: MEM, CON
82. Verbena odorosa — agrume-fiore/testa · N · agrume-erba · EMO: SLA, VIT

## F. Frutta / fruttate — testa-cuore (083–096)

83. Pera — frutto/testa · S · succosa moderna · EMO: GIO, ARI
84. Mela verde — frutto/testa · S · croccante-acida · EMO: VIT, GIO
85. Pesca (lattone) — frutto/cuore · S · vellutata carnale · EMO: SEN, CON
86. Albicocca (lattone) — frutto/cuore · S · dorata morbida · EMO: CON, SEN
87. Litchi — frutto/testa · S · rosato-acquoso · EMO: GIO, ARI
88. Ribes nero (cassis) — frutto/testa · S · verde-intenso · EMO: VIT, SLA
89. Fragola — frutto/cuore · S · caramellata rossa · EMO: GIO, CON
90. Lampone — frutto/cuore · S · dolce-acido · EMO: GIO
91. Fico (foglia+frutto) — verde-frutto/cuore · S · lattiginoso-legnoso · EMO: TER, CON
92. Frutto della passione — frutto/testa · S · tropicale-acido · EMO: GIO, SLA
93. Prugna / susina — frutto scuro/cuore-fondo · S · ambrata · EMO: SEN, MIS
94. Mela cotta — frutto/cuore · S · caramello-frutto · EMO: CON
95. Cocco (lattone) — frutto/cuore · S · cremoso solare · EMO: CON, GIO
96. Melone / anguria — frutto/testa · S · acquoso-dolce · EMO: GIO, ARI

## G. Verde / foglie — testa (097–104)

97. Galbano — verde/testa · N · tagliente amaro resinoso · EMO: VIT, TER
98. Foglia di violetta (verde) — verde/testa · N · acquosa amara · EMO: VIT, MEM
99. Erba tagliata (cis-3-esenolo) — verde/testa · S · acquoso fresco · EMO: VIT, SLA
100. Tè verde — verde/testa · S · astringente · EMO: ARI, VIT
101. Edera / foglia accordo — verde/testa · S · fresco-amaro · EMO: VIT
102. Bambù — verde-acquatico/testa · S · acquatico-verde · EMO: ARI, VIT
103. Pomodoro foglia — verde/testa · S · amaro particolare · EMO: TER, VIT
104. Menta-eucalipto accordo — verde/testa · S · gelo verde · EMO: VIT, ARI

## H. Marino / acquatico / ozonico — testa (105–110)

105. Calone (marino) — acquatico/testa · S · brezza-oceano · EMO: ARI
106. Note ozoniche — acquatico/testa · S · aria pulita · EMO: ARI, SLA
107. Sale / accordo salino — acquatico/testa-cuore · S · pelle marina · EMO: SEN, ARI
108. Alga — acquatico/cuore · S · iodato-verde · EMO: TER, ARI
109. Accordo acquoso — acquatico/testa · S · trasparenza · EMO: ARI
110. Petrichor (pioggia) — terra/cuore · S · terra bagnata · EMO: TER, MEM

## I. Tè / aromatici particolari (111–116)

111. Tè nero — aromatico/cuore · S/N · affumicato-secco · EMO: MIS, FOR
112. Mate — aromatico/cuore · N · erbaceo-tostato · EMO: TER, VIT
113. Caffè — gourmand-aromatico/cuore-fondo · N/S · tostato-amaro · EMO: FOR, CON
114. Cacao / cioccolato — gourmand/fondo · N/S · secco-amaro · EMO: CON, SEN
115. Rabarbaro — verde-frutto/testa · S · verde-acido rosato · EMO: VIT, GIO
116. Accordo minerale / inchiostro — astratto/cuore · S · freddo · EMO: MIS, ARI

## J. Legni — fondo (117–130)

117. Sandalo Mysore — legno/fondo · N(raro) · cremoso-lattiginoso · EMO: CON, SEN
118. Sandalo australiano — legno/fondo · N · più secco · EMO: CON, TER
119. Sandalo sintetico (Javanol) — legno/fondo · S · cremoso accessibile · EMO: CON, SEN
120. Cedro Atlas — legno/fondo · N · secco, matita · EMO: FOR, TER
121. Cedro Virginia — legno/fondo · N · morbido legnoso · EMO: CON, TER
122. Vetiver Haiti — legno-radice/fondo · N · terroso-fumé · EMO: TER, MIS
123. Vetiver Java — legno-radice/fondo · N · più affumicato · EMO: MIS, TER
124. Patchouli — legno-terra/fondo · N · cioccolato-canfora terroso · EMO: TER, SEN
125. Iso E Super — legno astratto/fondo · S · velluto "seconda pelle" · EMO: ARI, SEN
126. Cashmeran — muschio-legno/fondo · S · caldo avvolgente · EMO: CON, SEN
127. Guaiaco — legno/fondo · N · affumicato-dolce rosa-fumo · EMO: MIS, CON
128. Oud / Agarwood — legno/fondo · N(raro)/S · animalico-balsamico · EMO: MIS, FOR
129. Betulla (cuoio) — cuoio/fondo · N(limite) · affumicato · EMO: FOR, MIS
130. Cipresso / pino — legno/testa-fondo · N · resinoso-fresco · EMO: VIT, TER

## K. Resine / balsami — fondo (131–140)

131. Incenso (olibano) — resina/fondo · N · sacro fumé-agrumato · EMO: MIS, ARI
132. Mirra — resina/fondo · N · balsamica-amara · EMO: MIS, MEM
133. Benzoino — balsamo/fondo · N · vaniglia-balsamo caldo · EMO: CON
134. Labdano / cisto — resina/fondo · N · ambra-cuoio-miele denso · EMO: MIS, FOR
135. Elemi — resina/testa-fondo · N · agrumato-pepato · EMO: ARI, MIS
136. Opoponax — resina/fondo · N · balsamico-polveroso · EMO: CON, MEM
137. Storace — resina/fondo · N · cuoio-cannella balsamico · EMO: FOR, MIS
138. Copale / dammar — resina/fondo · N · secca · EMO: TER, MIS
139. Galbano resinoide (fondo) — resina-verde/fondo · N · verde-resina · EMO: TER, VIT
140. Pino mugo / abete balsamo — resina/fondo · N · foresta-resina · EMO: TER, VIT

## L. Ambra / ambrati — fondo (141–145)

141. Ambroxan — ambra moderna/fondo · S · minerale-pelle, scia · EMO: SEN, MIS
142. Accordo ambrato classico — ambra/fondo · S/N · caldo-dolce · EMO: CON, SEN
143. Ambrette (semi) — muschio vegetale/fondo · N · pera-ambra · EMO: SEN, MEM
144. Cetalox — ambra pulita/fondo · S · persistente · EMO: MIS, ARI
145. Ambra grigia (accordo) — ambra/fondo · S · salino-animalico minerale · EMO: SEN, MIS

## M. Muschi / muschiati — fondo (146–150)

146. Muschio bianco (Galaxolide) — muschio/fondo · S · pulito-bucato soffice · EMO: ARI, SEN
147. Muschio (Habanolide) — muschio/fondo · S · vellutato-metallico · EMO: ARI, SEN
148. Muschio (Muscenone) — muschio/fondo · S · caldo-animalico pulito · EMO: SEN, CON
149. Ambrette assoluta — muschio naturale/fondo · N · vegetale soffice · EMO: SEN, MEM
150. Muschio "pelle" (Helvetolide) — muschio/fondo · S · fruttato-soffice · EMO: SEN, GIO

## N. Animalici (puliti / sintetici) — fondo (151–154)

151. Castoreum accordo — cuoio-animalico/fondo · S · caldo · EMO: FOR, SEN
152. Civetta accordo — animalico/fondo · S · sporco-fiorito caldo · EMO: SEN, MIS
153. Hyraceum accordo — animalico/fondo · S/N · miele-urinoso · EMO: SEN, MIS
154. Cuoio accordo — cuoio/fondo · S · pelle conciata fumé · EMO: FOR, MIS

## O. Gourmand / dolci — fondo (155–158)

155. Vaniglia bourbon (assoluta) — gourmand/fondo · N(pregiata) · calda cremosa · EMO: CON, SEN
156. Vaniglia (vanillina) — gourmand/fondo · S · caramello accessibile · EMO: CON, GIO
157. Caramello / etil maltolo — gourmand/fondo · S · zucchero filato · EMO: GIO, CON
158. Tabacco (assoluta) — gourmand/fondo · N · miele-fieno-secco · EMO: CON, FOR

---

# PARTE III — FORMULA CLAUDIO-001 "Mistero Corporeo"

Registri target: **MIS + SEN** (con tocco FOR/TER). Percentuali sul concentrato.

**Testa** — #001 Bergamotto 6% · #032 Pepe rosa 4% · #033 Cardamomo 4%
**Cuore** — #146 Muschio bianco 12% *(il "pelle calda", non feromone)* · #141 Ambroxan 10% · #158 Tabacco 8% · #031 Pepe nero 3%
**Fondo** — #122 Vetiver Haiti 25% · #120 Cedro Atlas 16% · #125 Iso E Super 12%

**Totale concentrato 100%.** Lettura emotiva: apertura fresco-pepata (SLA), cuore caldo-fumé carnale (SEN+MIS), fondo radicato e lungo (TER). **IFRA:** verificare #146, #001, #158 prima della vendita. Nessun materiale vietato.

---

# PARTE IV — OPERAZIONI: kit, fornitori, pesi, costi

*Tutti i costi sono STIME d'ordine di grandezza da verificare sui listini reali al momento dell'ordine. Non sono prezzi confermati.*

## A. Fornitori reali (verificati come esistenti, giugno 2026)

**Materie prime — piccole quantità, Europa**

- **De Hekserij** (Paesi Bassi) — eng.hekserij.nl — vende quantità molto piccole anche ai privati e spedisce in Olanda e **Belgio**. Ideale per l'MVP da Bruxelles.
- **DirectPCW / Parfum Cosmetics World** (Grasse, FR) — directpcw.com — D2C, materiali ordinati per famiglia/CAS, in francese; fa anche il kit didattico "La Mallette du Parfumeur".
- **The Fragrance Foundry** (UE shipping) — thefragrancefoundry.com — prezzi corretti, ottimo packaging e documentazione, vende flaconcini campione (Winchester 15 ml).
- **Fraterworks** (spedisce globale) — fraterworks.com — naturali e *basi/accordi* pronti (oud, muschi, cassis) che accorciano il lavoro.
- **PerfumersWorld** (Bangkok, spedizione gratis 180+ paesi) — perfumersworld.com — aromachemicals, naturali, **kit di creazione**, check IFRA.

**Naturali pregiati:** Eden Botanicals (US). **Scala / private label (Grasse):** Bastide Fragrances, Sozio (casa di creazione dal 1758), Eurofragance (Spagna, B2B). Questi servono quando passi dalla mano alla produzione.

**Strumenti:** bilancia di precisione (le formule si pesano, non si contano a gocce). Riferimento: MyWeigh iBalance 101 (fino a 500 g, 0,01 g). Più alcol del profumiere (rettificato), pipette, becher, guanti nitrile.

## B. Pesi — la matematica reale

**AURA-50 (50 ml, Eau de Parfum ~18% concentrato)**

- Concentrato: 18% di 50 ml ≈ **9 ml** (≈ 8 g, secondo densità). È la somma delle essenze ai pesi della formula.
- Alcol: ≈ **41 ml**. (+ eventuale 1–3% acqua demineralizzata per stabilità.)
- Esempio CLAUDIO-001 su 9 g di concentrato: Vetiver 2,25 g (25%) · Cedro 1,44 g (16%) · Iso E 1,08 g (12%) · Muschio 1,08 g (12%) · Ambroxan 0,90 g (10%) · Tabacco 0,72 g (8%) · Bergamotto 0,54 g (6%) · Cardamomo 0,36 g · Pepe rosa 0,36 g · Pepe nero 0,27 g.
- Processo: pesa concentrato → aggiungi alcol → **macera** (48 h minimo; 2–4 settimane per i bespoke) → filtra (carta/garza) → imbottiglia.

**OLFACTO DROP (kit scoperta)** — proposta: 10 campioni da 2 ml per registro + 5 mouillettes + carta con QR e codice quiz. Totale juice ≈ 20 ml.

## C. Costi — stima d'ordine di grandezza (DA VERIFICARE)

**AURA-50 (per unità da 50 ml)**

| Voce                                       | Stima        |
|--------------------------------------------|--------------|
| Concentrato (9 g, media materiali)         | €8–35        |
| Alcol del profumiere (~41 ml)              | €2–5         |
| Flacone + atomizzatore + tappo             | €1,5–4       |
| Scatola + scheda formula + etichetta       | €3–6         |
| Manodopera (macerazione, filtro, fill, QC) | €10–20       |
| **COGS stimato**                           | **≈ €30–55** |
| Prezzo di vendita target                   | €120–220     |

**OLFACTO DROP (per kit)**

| Voce                                | Stima        |
|-------------------------------------|--------------|
| Juice campioni (~20 ml)             | €8–25        |
| 10 vials 2 ml + 5 mouillettes       | €4–8         |
| Scatola + stampa + carta QR         | €4–8         |
| Manodopera pack                     | €5           |
| **COGS stimato**                    | **≈ €21–46** |
| Prezzo target (scontabile sul core) | €39–69       |

**Costi una-tantum / ricorrenti:** valutazione sicurezza (CPSR), notifica **CPNP**, Responsabile (RP) UE, conformità **IFRA** e **GMP ISO 22716**, etichettatura allergeni (CLP). Ogni formula venduta in UE richiede copertura di sicurezza — va progettato (formule modulari pre-valutate, o assessor convenzionato), non ignorato.

## D. Il passo fisico (questa settimana)

Niente altro codice. **Una persona reale**, l'intervista AURA, una formula vera costruita a mano con i materiali (ordine di prova da Hekserij, che spedisce in Belgio), consegna con la scheda per numero. Poi: prima riga in `contatti.jsonl`.

---

*Funziona? Si misura quando #CLAUDIO-001 esiste in un flacone vero, sulla pelle di una persona vera, e quella persona ha pagato.*

© Claudio Terzi, 2026
