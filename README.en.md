# rhb-video-unlock

*[Wersja polska: README.md](README.md)*

The script modifies the firmware of the **Uconnect 430N (RHB)** head unit from
update package **50.01.01**:

- **video while driving** on the front screen;
- **European market**: FM **87.5–108.0 MHz in 100 kHz steps** instead of
  87.7–107.9 in 200 kHz steps (a US unit cannot tune stations on 88.0, 92.6
  etc.).

## ⚠️ Read this first

- **No warranty**, MIT licence. Not affiliated with Stellantis, Chrysler or
  the manufacturer of the head unit.
- **This repository contains no firmware.** You need the official package
  `RHB-RBZ.50.01.01.zip`. It can be downloaded from
  [mygig-disk.com](https://mygig-disk.com/download-rhb.php), which also
  describes how to install it.

## What changes

| | USA (stock) | Patched |
|---|---|---|
| Video while driving | blocked | **unlocked** |
| FM | 87.7–107.9 MHz, 200 kHz | **87.5–108.0 MHz, 100 kHz** |
| AM | 530–1710 kHz, 10 kHz | 531–1611 kHz, 9 kHz |
| Menu languages | 3 (EN-US, FR-CA, ES) | **6** (EN-UK, FR, ES, DE, IT, NL) |
| RDS | US variant (RBDS) | European RDS, incl. PTY list |
| SiriusXM | present | **gone** (not available in Europe anyway) |
| Radio presets | — | reset on first start |

## How it works

The unit has two processors:

1. **Main SoC** (file `MAIN_APL_CPU1.mbi`). The function that decides whether
   video must be blocked returns its result in register `r2`. At offset
   `0x0B06F8` the bytes `52 F3` → `E2 00` (`mov #0,r2`) make it always return
   "not blocked", i.e. 0.
2. **Audio/CAN MCU** (files `*.aud`). It stores the radio market as an index
   (0 = Europe, 1 = USA, 2 = Japan, 3 = rest of world) and the stock firmware
   **forces USA on every start**. The tuner (FM/AM range and step) depends on
   this index, and the SoC gets the market from the MCU and switches its menus
   to the European version by itself. The script sets the index to 0.

The package has 4 `.aud` variants: `H_I` (CAN I-HS), `H_B` (CAN-B), `HSI` and
`HSB` (the same with SiriusXM). The unit picks its own, so the script patches
all four. Each of the 5 files is checked by SHA-256 before the change and after
writing; the result is byte-identical to the images tested in the car.

## Step by step (as tested)

**0. Power.** Keep the engine running for the whole update. Do not switch the
ignition off or pull the stick while it runs.

**1. Stick: MBR partition table, one FAT32 partition.** A stick with a GPT
table (e.g. one formatted on a Mac) is read by the unit, but no update dialog
appears.

**2. Original first.** Extract the official `RHB-RBZ.50.01.01.zip` to the
root of the stick and flash this **unmodified** package first:
- "Update baseline data files on HDD?" → **YES** (data for the unit's disk);
- application update → **YES**.

**3. Patch the stick with the script.** On the stick with the original
package, copy `rhb_europe_unlock.py` to the root, change to that directory and
run it (Python 3.9+):

```text
py rhb_europe_unlock.py          (Windows)
python3 rhb_europe_unlock.py     (Linux / macOS)
```

The script modifies the files in place, without backups, and verifies their
checksums. If any file is not the original 50.01.01 file, nothing is changed.
Then delete the script from the stick (the tested stick did not contain it).

**4. Flash the patched version.** The unit already runs 50.01.01 and so does
the package — that is fine:
- "Update baseline data files on HDD?" → **NO** (the data is already on the
  disk from step 2 and is not changed);
- application update 50.01.01 → 50.01.01 → **YES**. The unit flashes the
  application ("flash Application software") and the MCU firmware ("flash
  Audio CPU software");
- when it finishes and **offers the same update again** → **CANCEL**. Then
  remove the stick; the unit works.

**Going back to stock:** flash the unmodified 50.01.01 package again.
