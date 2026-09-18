# GENESI-006 — CadQuery Esempi Pratici per Pocket NC V2-50
*Task autonomo SDQ-1 — completato 2026-06-20*

---

## Setup

```bash
pip install cadquery
# oppure con conda:
conda install -c cadquery -c conda-forge cadquery
```

Pocket NC V2-50CHK: fresatrice 5 assi, tavola rotante B + testa inclinante A.
Post-processor: LinuxCNC o Fusion 360 → G-code compatibile.

---

## Esempio 1 — Cubo semplice (verifica setup)

```python
import cadquery as cq

# Cubo 10x10x10mm con smusso
cubo = (
    cq.Workplane("XY")
    .box(10, 10, 10)
    .edges("|Z")
    .chamfer(1)
)

# Esporta STEP per Fusion 360 (che genera G-code per Pocket NC)
cubo.val().exportStep("cubo.step")
print("✓ cubo.step esportato")
```

---

## Esempio 2 — Cilindro con foro (operazione booleana)

```python
import cadquery as cq

# Cilindro D=20mm, H=15mm con foro centrale D=8mm
parte = (
    cq.Workplane("XY")
    .cylinder(15, 10)                    # raggio=10 → D=20
    .faces(">Z")
    .workplane()
    .hole(8)                             # foro D=8
)

parte.val().exportStep("cilindro_forato.step")
```

---

## Esempio 3 — Pezzo 5 assi: sfera con intaglio laterale

```python
"""
Questo esempio richiede la fresatrice 5 assi:
la sfera ha una tasca circolare laterale (asse B inclinato).
"""

import cadquery as cq
import math

# Sfera D=30mm
sfera_base = (
    cq.Workplane("XY")
    .sphere(15)
)

# Tasca laterale: cilindro sottratto con asse inclinato di 45°
# CadQuery usa trasformazioni per simulare l'orientamento 5 assi
tasca = (
    cq.Workplane("XZ")           # piano laterale
    .workplane(offset=0)
    .transformed(rotate=cq.Vector(0, 45, 0))   # inclina di 45° (asse B)
    .circle(5)
    .extrude(20, both=True)      # estrudi in entrambe le direzioni
)

# Differenza booleana
risultato = sfera_base.cut(tasca)
risultato.val().exportStep("sfera_5assi.step")

# Visualizzazione (richiede cq-editor o jupyter-cadquery)
# show_object(risultato)
```

---

## Esempio 4 — Profilo parametrico (utile per varianti)

```python
"""
Staffa parametrica: cambia le dimensioni senza riscrivere il codice.
"""

import cadquery as cq

def staffa(
    larghezza: float = 30.0,
    altezza: float   = 20.0,
    spessore: float  = 4.0,
    diam_foro: float = 5.0,
) -> cq.Workplane:
    return (
        cq.Workplane("XY")
        .box(larghezza, altezza, spessore)
        .faces(">Z")
        .workplane()
        # Fori agli angoli
        .rect(larghezza - 10, altezza - 10, forConstruction=True)
        .vertices()
        .hole(diam_foro)
    )

# Esporta tre varianti
staffa(30, 20, 4).val().exportStep("staffa_s.step")
staffa(60, 40, 6).val().exportStep("staffa_m.step")
staffa(90, 60, 8).val().exportStep("staffa_l.step")
print("✓ Tre varianti esportate")
```

---

## Esempio 5 — Export diretto G-code (CNC Path)

```python
"""
CadQuery non genera G-code nativamente, ma può essere usato con
cq-cam (libreria aggiuntiva) o esportare STEP → Fusion 360 → G-code.

Alternativa: FreeCAD con Python binding per generare G-code direttamente.
"""

# Via FreeCAD (installato separatamente)
# import FreeCAD, Path, PathScripts.PathJob as PathJob

# Via STEP → Fusion 360:
# 1. Esporta .step da CadQuery
# 2. Importa in Fusion 360
# 3. Manufacturing workspace → Setup → Contour/Pocket operations
# 4. Post-process con "LinuxCNC" o "Generic Fanuc"
# 5. Output .ngc → carica su Pocket NC

# Pocket NC accetta G-code standard Fanuc/LinuxCNC
# Unità: mm, feed in mm/min, speed in RPM
```

---

## Pipeline completa per SDQ-1/WAVE-003 → Pocket NC

```
WAVE-003 genera descrizione geometria
    ↓
CadQuery Python: modella pezzo
    ↓
Esporta .step
    ↓
Fusion 360 (post-processor): genera .ngc G-code
    ↓
[VERIFICA MANUALE OBBLIGATORIA — Claudio approva prima di eseguire]
    ↓
Upload su Pocket NC V2-50CHK
    ↓
Esecuzione fisica
```

**Regola permanente CLAUDE.md:** la conferma manuale di Claudio è obbligatoria
prima di qualsiasi esecuzione fisica sulla macchina CNC.

---

## Parametri Pocket NC V2-50CHK di riferimento

| Parametro | Valore |
|---|---|
| Corsa X | 101.6 mm |
| Corsa Y | 101.6 mm |
| Corsa Z | 152.4 mm |
| Rotazione A | -30° a +135° |
| Rotazione B | 360° continuo |
| Velocità mandrino | 500-10.000 RPM |
| Feed rate max | 1524 mm/min |
| Controller | LinuxCNC |

---

## Installazione cq-editor (GUI per sviluppo)

```bash
# cq-editor: IDE visuale per CadQuery
pip install cq-editor
cq-editor  # avvia l'interfaccia

# Oppure via Jupyter:
pip install jupyter-cadquery
# → visualizzazione 3D interattiva nel notebook
```

---

*GENESI-006 completato — 2026-06-20*
*SDQ-1 / Claudio Terzi, Bruxelles*
