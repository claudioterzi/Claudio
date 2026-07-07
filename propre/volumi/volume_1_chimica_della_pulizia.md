# Volume 1 — Chimica della Pulizia

> Fondamenti. Ogni scheda del Volume 2 presuppone questi concetti:
> qui si spiegano una volta sole, per bene.

## Indice

1. [Tensioattivo](#tensioattivo)
2. [Enzima](#enzima)
3. [Solvente](#solvente)
4. [Acido](#acido)
5. [Base](#base)
6. [pH](#ph)
7. [Durezza dell'acqua](#durezza-dellacqua)
8. [Schiuma](#schiuma)
9. [Compatibilità](#compatibilità)

---

## Tensioattivo

Molecola anfifilica: una testa idrofila (ama l'acqua) e una coda
idrofoba (fugge l'acqua, ama il grasso). In soluzione riduce la
tensione superficiale dell'acqua e forma micelle — sferette che
inglobano lo sporco grasso al centro (dove sta la coda idrofoba) e lo
tengono disperso in acqua grazie alle teste idrofile rivolte
all'esterno. Senza tensioattivo, acqua e grasso non si mescolano;
con il tensioattivo, l'acqua "porta via" il grasso.

Famiglie: anionici (pulenti, schiumogeni: es. LAS, SLES), non ionici
(delicati, sgrassanti, poco schiumogeni: es. alcoli grassi etossilati),
cationici (ammorbidenti, antistatici, spesso incompatibili con gli
anionici), anfoteri (delicati, si comportano da anionici o cationici
a seconda del pH: es. betaine).

→ vedi: `volume_2/sostanze` (categoria `tensioattivo`)

## Enzima

Proteina catalizzatrice: accelera la rottura di specifiche macchie
senza essere consumata. Ogni enzima è specifico per un tipo di
sporco: le **proteasi** rompono le proteine (sangue, uovo, erba), le
**lipasi** i grassi, le **amilasi** gli amidi (salse, pasta), le
**cellulasi** agiscono sulla fibra cellulosica stessa (ravvivano il
colore rimuovendo i micro-pilling). Lavorano in una finestra di pH e
temperatura precisa (tipicamente pH 7-10, 20-40 °C): fuori da quella
finestra si denaturano e smettono di funzionare. Per questo gli
enzimi sono incompatibili con acidi forti, alcali forti e
ossidanti energici, che li distruggono.

## Solvente

Liquido che scioglie una sostanza senza reagire chimicamente con
essa (a differenza di un acido o una base, che *reagiscono*). I
solventi si dividono per polarità: l'acqua è il solvente polare per
eccellenza; i solventi organici (isopropanolo, acetone, percloroetilene)
coprono lo spettro da polare a apolare e sciolgono ciò che l'acqua non
tocca — oli, cere, resine, alcuni inchiostri. "Il simile scioglie il
simile" è la regola pratica.

→ vedi: `isopropanolo`

## Acido

Sostanza che in acqua libera ioni H⁺ (o, definizione di Brønsted,
dona protoni). Più è forte, più dissocia completamente. Gli acidi
usati nel tessile sono quasi sempre **deboli** (citrico, acetico,
lattico): agiscono in modo graduale e reversibile, ideali per
riportare le fibre proteiche al loro pH naturale.

→ vedi: `acido_citrico`, `acido_acetico`

## Base

Sostanza che in acqua libera ioni OH⁻ (o accetta protoni). Le basi
saponificano i grassi (li trasformano in sapone, solubile in acqua) e
gonfiano le fibre cellulosiche aprendole ai tensioattivi. Sulle fibre
proteiche (lana, seta) l'alcalinità è invece dannosa: scioglie
parzialmente la cheratina e la fibroina.

→ vedi: `ammoniaca`, `bicarbonato_di_sodio`

## pH

Scala logaritmica (0-14) che misura la concentrazione di ioni H⁺.
7 = neutro, <7 = acido, >7 = basico. Essendo logaritmica, un pH 3 è
10 volte più acido di un pH 4. Regola pratica per il tessile:

| Fibra | pH ideale di lavoro |
|---|---|
| Lana, seta (proteiche) | 4,5 – 6,5 (leggermente acido) |
| Cotone, lino (cellulosiche) | 6 – 9 (tollerano l'alcalino) |
| Sintetiche (poliestere, poliammide) | 5 – 9 (ampia tolleranza) |

## Durezza dell'acqua

Concentrazione di ioni calcio e magnesio disciolti. L'acqua dura:
riduce l'efficacia dei tensioattivi anionici (formano sali insolubili
col calcio — i "sali di calce" che opacizzano i tessuti), inibisce
parzialmente gli enzimi, favorisce il calcare sulle macchine. Si
corregge con sequestranti/chelanti (es. `acido_citrico`,
polifosfonati, zeoliti) che legano il calcio impedendogli di
interferire.

## Schiuma

Non è un indicatore di potere pulente (è un mito diffuso): dipende
dal tipo di tensioattivo, non dalla sua efficacia. Gli anionici
schiumano molto, i non ionici pochissimo pur pulendo altrettanto
bene. Nelle macchine ad iniezione-estrazione la schiuma eccessiva è
un problema meccanico (riduce l'aspirazione): si usano tensioattivi
a bassa schiuma o antischiuma dedicati (siliconici).

## Compatibilità

Principio guida trasversale a tutto il Volume 2: prima di mescolare
due prodotti, verificare sempre la sezione `incompatibilita` di
ENTRAMBE le schede. Le combinazioni pericolose ricorrenti da
memorizzare a memoria:

- **Ipoclorito + acido** (qualsiasi) → cloro gassoso.
- **Ipoclorito + ammoniaca** → clorammine.
- **Perossido + metalli/ruggine** → reazione di Fenton, rischio buchi.
- **Ossidanti + riducenti** → si annullano (spreco, non pericolo).

→ tabella completa delle incompatibilità: generata automaticamente
dalle schede del Volume 2 (campo `incompatibilita`, `pericolo: true`).
