# rhb-video-unlock

*[English version: README.en.md](README.en.md)*

Skrypt zmienia oprogramowanie radia **Uconnect 430N (RHB)** z pakietu **50.01.01**:
Radio ma obsługiwać 50.01.01, nie róbcie downgrade z nowszych wersji. W nowszych wersjach zmiania sie obsluga dysku i wersja 50.01.01 nie zawiera wymaganych zmian wiecej: https://mygig-disk.com/index-rhb.php

- **wideo w czasie jazdy** na przednim ekranie;
- **rynek europejski**: FM **87,5–108,0 MHz co 100 kHz** zamiast
  87,7–107,9 co 200 kHz (radio z USA nie łapie stacji na 88,0, 92,6 itd.).

## ⚠️ Najpierw przeczytaj

- **Bez gwarancji**, licencja MIT. Projekt nie jest powiązany ze Stellantis,
  Chryslerem ani producentem radia.
- **Repozytorium nie zawiera oprogramowania radia.** Potrzebny jest
  oficjalny pakiet `RHB-RBZ.50.01.01.zip`. Można go pobrać z
  [mygig-disk.com](https://mygig-disk.com/download-rhb.php); tam jest też opis
  wgrywania oprogramowania.

## Co się zmienia

| | USA (oryginał) | Po zmianie |
|---|---|---|
| Wideo w czasie jazdy | zablokowane | **odblokowane** |
| FM | 87,7–107,9 MHz co 200 kHz | **87,5–108,0 MHz co 100 kHz** |
| AM | 530–1710 kHz co 10 kHz | 531–1611 kHz co 9 kHz |
| Języki menu | 3 (EN-US, FR-CA, ES) | **6** (EN-UK, FR, ES, DE, IT, NL) |
| RDS | wersja amerykańska (RBDS) | europejska (RDS), w tym lista PTY |
| SiriusXM | jest | **znika** (w Europie i tak nie działa) |
| Presety radia | — | zerowane przy pierwszym starcie |

## Jak to działa

Radio ma dwa procesory:

1. **Główny SoC** (plik `MAIN_APL_CPU1.mbi`). Funkcja decydująca o blokadzie
   wideo zwraca swój wynik w rejestrze `r2`. Pod offsetem `0x0B06F8` zamiana
   `52 F3` → `E2 00` (`mov #0,r2`) sprawia, że zawsze zwraca „bez blokady”,
   czyli 0.
2. **MCU audio-CAN** (pliki `*.aud`). Przechowuje rynek radia jako
   indeks (0 = Europa, 1 = USA, 2 = Japonia, 3 = reszta świata) i w
   oryginale **przy każdym starcie wymusza USA**. Od tego indeksu zależy
   tuner (zakres i krok FM/AM), a SoC dostaje od MCU informację o rynku i
   sam przełącza menu na wersję europejską. Skrypt ustawia indeks na 0.

Pakiet ma 4 warianty `.aud`: `H_I` (CAN I-HS), `H_B` (CAN-B), `HSI` i `HSB`
(to samo z SiriusXM). Radio samo wybiera właściwy, więc skrypt zmienia
wszystkie cztery. Każdy z 5 plików jest sprawdzany sumą SHA-256 przed
zmianą i po zapisie; wynik jest bajt w bajt taki, jak przetestowany w aucie.

## Instrukcja krok po kroku (sprawdzona)

**0. Zasilanie.** Przez całą aktualizację silnik pracuje. Nie wyłączaj
zapłonu i nie wyjmuj pendrive'a w trakcie.

**1. Pendrive: tablica MBR, jedna partycja FAT32.** Pendrive z tablicą GPT
(np. sformatowany kiedyś na Macu) radio czyta, ale nie pokazuje okna
aktualizacji.

**2. Najpierw oryginał.** Rozpakuj oryginalny `RHB-RBZ.50.01.01.zip` do
głównego katalogu pendrive'a i wgraj najpierw ten **niezmieniony** pakiet:
- „Update baseline data files on HDD?” → **YES** (dane na dysk radia);
- aktualizacja aplikacji → **YES**.

**3. Zmiana pendrive'a skryptem.** Na pendrive z oryginalnym pakietem
skopiuj `rhb_europe_unlock.py` do katalogu głównego, przejdź do tego
katalogu i uruchom skrypt (Python 3.9+):

```text
py rhb_europe_unlock.py          (Windows)
python3 rhb_europe_unlock.py     (Linux / macOS)
```

Skrypt zmienia pliki na miejscu, bez kopii zapasowych, i sprawdza ich sumy
kontrolne. Jeśli któryś plik nie jest oryginałem 50.01.01, nic nie zmienia.
Na koniec usuń skrypt z pendrive'a (testowany nośnik go nie zawierał).

**4. Wgranie wersji zmienionej.** Radio ma już 50.01.01 i pakiet też —
to nie przeszkadza:
- „Update baseline data files on HDD?” → **NO** (dane są już na dysku z
  kroku 2 i nie są zmieniane);
- aktualizacja aplikacji 50.01.01 → 50.01.01 → **YES**. Radio wgrywa
  aplikację („flash Application software”) i oprogramowanie MCU („flash
  Audio CPU software”);
- gdy po zakończeniu radio **ponownie zaproponuje** tę samą aktualizację →
  **CANCEL**. Potem wyjmij pendrive; radio działa.

**Powrót do oryginału:** wgraj ponownie niezmieniony pakiet 50.01.01.
