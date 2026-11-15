import hashlib, os, struct, sys
from pathlib import Path

ROOT = Path.cwd()                               # biezacy katalog = katalog glowny pendrive'a
sha = lambda b: hashlib.sha256(b).hexdigest()


def patch_cpu1(d):
    # Funkcja "czy blokowac wideo?" konczy sie `mov.l @(12,r15),r2` ... `rtv/n r2`.
    # Zamiana na `mov #0,r2` (E2 00): zawsze "bez blokady".
    d[0xB06F8:0xB06FA] = b"\xE2\x00"
    s = lambda b: ~sum(struct.unpack(">%dI" % (len(b) // 4), b)) & 0xFFFFFFFF
    struct.pack_into(">I", d, 0x28, s(d[0x40:]))   # suma danych MBI (najpierw) ...
    struct.pack_into(">I", d, 0x38, s(d[:0x38]))   # ... potem suma naglowka (obejmuje 0x28)


def patch_aud(changes):
    def fn(d):
        for off, old, new in changes:
            assert d[off] == old
            d[off] = new
        # suma .aud: u32 big-endian pod 0x10 = suma wszystkich bajtow od 0x14 do konca
        struct.pack_into(">I", d, 0x10, sum(d[0x14:]) & 0xFFFFFFFF)
    return fn


def aud(tab212c, tab3338, us, consts):
    # tablice rynku [1] "USA" -> wartosc Europy, para tunera "US" -> "UT",
    # 9 x stala `MOV.B/CMP.B #1` -> `#0` (indeks rynku, flaga, region startowy tunera)
    return patch_aud([(tab212c, 0x01, 0x08), (tab3338, 0x00, 0x14), (us, 0x53, 0x54)]
                     + [(o, 0x2B, 0x0B) for o in consts])


# plik: (SHA-256 oryginalu, SHA-256 wyniku, zmiana)
FILES = {
    "MAIN_APL_CPU1.mbi": ("0a9f6023059c20b1a2d09f55d0b1f0948b29fa4337f20471ecfb52f253558383",
                          "7624433f6ec89c9549f424528dc94b91fc2be15b4ee7824e888efd0ebc6e7762", patch_cpu1),
    "H_I02210.aud": ("2ce4d6fe24554bc08715b4c665bdc1926d3f714de5efb087735d062dd78d34cd",
                     "731ce52367fa1e017c37ed9ba13fbe59419f52b59fe7341a04c9b1dd42f0647f",
                     aud(0x212D, 0x3339, 0xF60F, (0x19BB4, 0x3C8F3, 0x4709B, 0x470A2, 0x3B2D6,
                                                  0x3F659, 0x3CE0A, 0x5242A, 0x52D91))),
    "HSI02211.aud": ("48c2db0cff0d56e743642e3114afc53d2c2dcf7ee9366aa3c6c4b6f501674829",
                     "6a39479188bfb52e3b19885ca8591e352100701fffd5a9f6685d8fddf046e59f",
                     aud(0x212D, 0x3339, 0x10F03, (0x1B526, 0x3E353, 0x48B1B, 0x48B22, 0x3CD1E,
                                                   0x410D1, 0x3E86A, 0x53F1A, 0x54881))),
    "H_B02210.aud": ("087541075c64cf13a6a0b60cb694dcab13e11f2ce74fbe0b7eba2de7bee239ef",
                     "405200d16a10eb0fb203beaec5ffc1a54682a30ed84e7b289d5b08e7a16c7132",
                     aud(0x26E5, 0x38F1, 0xF13B, (0x1DC14, 0x4063B, 0x4B183, 0x4B18A, 0x3F01E,
                                                  0x433A1, 0x40B52, 0x5708A, 0x579F1))),
    "HSB02211.aud": ("4e38f0e339a919658516816d745b7c5904cbaa13659f49467dca3d27011f5faa",
                     "884b287c4c25195f781803087c4f2176aa46a8db0cc954345d45b103b5646ccb",
                     aud(0x26E5, 0x38F1, 0x10A2F, (0x1F586, 0x42097, 0x4CBFF, 0x4CC06, 0x40A62,
                                                   0x44E15, 0x425AE, 0x58B76, 0x594DD))),
}

# 1. sprawdz wszystkie 5 plikow, zanim cokolwiek zostanie zmienione
todo = []
for name, (h_in, h_out, fn) in FILES.items():
    f = ROOT / name
    if not f.is_file():
        sys.exit("Brak %s - uruchom skrypt w katalogu glownym pendrive'a z pakietem 50.01.01." % name)
    h = sha(f.read_bytes())
    if h == h_out:
        print("%-18s juz zmieniony" % name)
    elif h == h_in:
        todo.append((name, h_out, fn))
    else:
        sys.exit("%s to nie oryginal 50.01.01 ani wersja zmieniona - rozpakuj oryginalny ZIP od nowa." % name)

# 2. zmien w miejscu: wynik w pamieci musi miec znany SHA-256, potem zapis i wymuszenie zapisu na nosnik
for name, h_out, fn in todo:
    f = ROOT / name
    d = bytearray(f.read_bytes())
    fn(d)
    assert sha(d) == h_out, name
    with open(f, "r+b") as w:
        w.write(d)
        w.flush()
        os.fsync(w.fileno())
    print("%-18s zmieniony" % name)

# 3. kontrola koncowa: odczyt wszystkich 5 plikow z pendrive'a i porownanie SHA-256
bad = [n for n, (_, h_out, _) in FILES.items() if sha((ROOT / n).read_bytes()) != h_out]
if bad:
    sys.exit("BLAD: suma SHA-256 po zapisie niezgodna: %s - rozpakuj oryginalny ZIP od nowa." % ", ".join(bad))
print("OK - sumy kontrolne zgodne, pendrive gotowy. Bezpiecznie odlacz pendrive.")
