# Optimized Tree Indexer (Cold Storage v2)

Detta verktyg scannar hårddiskar eller mappar, skapar en indexfil (JSON) för import till databaser och genererar automatiskt utskriftsvänliga etiketter med QR-koder.

## 🛠 Installation

För att undvika felmeddelanden som `externally-managed-environment` eller `zsh: no matches found`, följ dessa steg för att installera allt i en isolerad miljö.

### 1. Förbered miljön (Rekommenderas)

Öppna terminalen, gå till mappen där scriptet ligger och kör följande kommandon för att skapa en "virtuell miljö". Detta isolerar installationen från resten av din dator.

```bash
# 1. Skapa en virtuell miljö som heter "venv"
python3 -m venv venv

# 2. Aktivera miljön
# (Du måste göra detta varje gång du öppnar en ny terminal för att köra scriptet)
source venv/bin/activate
```

*När miljön är aktiv ser du `(venv)` i början på din kommandorad.*

### 2. Installera bibliotek

När miljön är aktiverad, installera de nödvändiga paketen.
**OBS:** Citattecknen runt `"qrcode[pil]"` är viktiga för att det ska fungera på Mac (zsh).

```bash
pip install "qrcode[pil]" pillow tqdm
```

---

## 🚀 Användning

### Grundläggande scanning

Det enklaste sättet att köra scriptet är att ange sökvägen till disken eller mappen du vill indexera:

```bash
python3 enhanced_tree_indexer.py /Volumes/MinHårddisk
```

### Vanliga flaggor och inställningar

| Flagga | Beskrivning | Exempel |
| :--- | :--- | :--- |
| `--foto-only` | Ignorerar systemfiler/dokument. Indexerar bara media (RAW, JPG, MOV, MP4 etc). | `python3 enhanced_tree_indexer.py /Path --foto-only` |
| `-o [filnamn]` | Bestämmer namnet på output-filen. | `python3 enhanced_tree_indexer.py /Path -o ProjektX.json` |
| `--no-label` | Stänger av generering av etiketter (JPG). | `python3 enhanced_tree_indexer.py /Path --no-label` |
| `--no-resume` | Tvingar scriptet att börja om från början (ignorerar sparad checkpoint). | `python3 enhanced_tree_indexer.py /Path --no-resume` |

---

## 📋 Interaktivt läge (Kundmappar)

När scriptet har scannat klart filerna kommer det att pausa och fråga dig om **mappstrukturen**. Detta görs för att etiketten ska bli snygg och lista rätt "Kunder" eller "Projekt".

Exempel på dialog:

```text
🔍 Analyserar nivå 1...
1. Kund A
2. Kund B
3. Projekt X
❓ Är nivå 1 din grundnivå för kunder/projekt? (j/n/skip):
```

* **Svara `j` (ja):** Om listan ser korrekt ut.
* **Svara `n` (nej):** För att gå djupare i mappstrukturen och se nästa nivå.
* **Svara `skip`:** För att hoppa över kundlistan på etiketten.

---

## 📂 Vad genereras?

När scriptet är klart hittar du tre filer i mappen:

1. **`[Namn].json`** – Själva indexet med all data.
2. **`[Namn]_label.jpg`** – Etikett (50x80mm) med QR-kod och innehållsförteckning.
3. **`[Namn]_label_header.jpg`** – Roterad toppetikett för diskens rygg.

---

## ❓ Felsökning

### Fel: `zsh: no matches found: qrcode[pil]`

* **Orsak:** Terminalen försöker tolka klamrarna `[]`.
* **Lösning:** Du glömde citattecken. Skriv `pip install "qrcode[pil]"` istället.

### Fel: `ModuleNotFoundError: No module named 'PIL'` eller `tqdm`

* **Orsak:** Biblioteken hittas inte.
* **Lösning:** Du har troligen inte aktiverat din virtuella miljö. Kör `source venv/bin/activate` och försök igen.

### Fel: `Permission denied`

* **Orsak:** Scriptet har inte rättigheter att läsa disken.
* **Lösning:** 1. Kontrollera att din terminal har "Full Disk Access" i Systeminställningar på Mac.
  2. Eller kör kommandot med `sudo` före (t.ex. `sudo python3 ...`).
