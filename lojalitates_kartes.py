"""Lojalitātes karšu prototips: cikliska kaudzīte ar ritināšanu un vilkšanu.

Palaišana: python lojalitates_kartes.py
Izmanto Python standarta bibliotēku: tkinter un json.
"""

import json
import random
import re
import time
import tkinter as tk
from datetime import date, datetime
from pathlib import Path
from tkinter import messagebox, ttk

MAPE = Path(__file__).resolve().parent
KARTU_FAILS = MAPE / "kartes.json"


class LojalitatesKartes:
    def __init__(self, logs):
        self.logs = logs
        logs.title("Lojalitātes kartes")
        logs.resizable(False, False)
        logs.configure(bg="white")

        # Sākotnējais attēls rāda lielo '+'. Otrajā attēlā kartes ir
        # noņemtas, lai aiz jaunajām kartēm nepaliktu uzzīmētās vecās.
        self.fons = tk.PhotoImage(file=MAPE / "telefons.png")
        self.tirs_fons = tk.PhotoImage(file=MAPE / "telefons_tirs.png")
        self.ekrans = tk.Canvas(logs, width=350, height=688,
                                highlightthickness=0, bg="white")
        self.ekrans.pack()
        self.fona_attels = self.ekrans.create_image(
            0, 0, image=self.fons, anchor="nw"
        )

        # Peles ritenītis/skārienpaliktnis + karšu vilkšana (swipe).
        # Linux izmanto Button-4/5, Windows/macOS izmanto MouseWheel.
        self.vilksanas_sakums = None
        self.pedejais_ritinajums = 0.0
        self.ekrans.bind("<ButtonPress-1>", self.peles_nospiesana)
        self.ekrans.bind("<B1-Motion>", self.peles_vilksana)
        self.ekrans.bind("<ButtonRelease-1>", self.peles_atlaisana)
        self.ekrans.bind("<Motion>", self.peles_kustiba)
        self.ekrans.bind("<MouseWheel>", self.peles_ritenis)
        self.ekrans.bind("<Button-4>", lambda _e: self.ritinat(-1))
        self.ekrans.bind("<Button-5>", lambda _e: self.ritinat(1))
        logs.bind("<Control-n>", lambda _e: self.pievienot_karti())
        logs.bind("<Left>", lambda _e: self.parslegt(-1))
        logs.bind("<Right>", lambda _e: self.parslegt(1))
        logs.bind("<Up>", lambda _e: self.parslegt(-1))
        logs.bind("<Down>", lambda _e: self.parslegt(1))

        try:
            dati = json.loads(KARTU_FAILS.read_text(encoding="utf-8"))
            if not isinstance(dati, list):
                raise ValueError("Nederīgs karšu fails")
            self.kartes = [
                karte for karte in dati
                if isinstance(karte, dict)
                and isinstance(karte.get("nosaukums"), str)
                and isinstance(karte.get("numurs"), str)
            ]
        except (FileNotFoundError, OSError, ValueError):
            self.kartes = []

        self.izveleta = len(self.kartes) - 1
        self.zimet_kartes()

    @staticmethod
    def isaks(teksts, limits):
        return teksts if len(teksts) <= limits else teksts[:limits - 1] + "…"

    def noapaļots_taisnsturis(self, x1, y1, x2, y2, rad, krasa,
                              kontura="#666666", tags="kartes"):
        """Noapaļots taisnstūris uz tkinter Canvas."""
        punkti = [
            x1 + rad, y1, x2 - rad, y1, x2, y1, x2, y1 + rad,
            x2, y2 - rad, x2, y2, x2 - rad, y2, x1 + rad, y2,
            x1, y2, x1, y2 - rad, x1, y1 + rad, x1, y1,
        ]
        return self.ekrans.create_polygon(
            punkti, smooth=True, splinesteps=18,
            fill=krasa, outline=kontura, width=1.7, tags=tags
        )

    def aizmugures_karte(self, indekss, x1, y1, x2, y2,
                          krasa, teksts_y, gaišs=False):
        """Uzzīmē karti aiz centrālās; redzama paliek tikai tās maliņa."""
        self.noapaļots_taisnsturis(x1, y1, x2, y2, 22, krasa)
        vards = self.isaks(self.kartes[indekss]["nosaukums"], 24)
        self.ekrans.create_text(
            175, teksts_y, text=vards,
            fill="#eeeeee" if gaišs else "#363636",
            font=("Arial", 10, "bold"), anchor="center", tags="kartes"
        )

    def galvena_karte(self):
        """Uzzīmē aktīvo karti ar tās nosaukumu un dekoratīvu svītrkodu."""
        dati = self.kartes[self.izveleta]
        c = self.ekrans
        self.noapaļots_taisnsturis(38, 260, 312, 426, 23, "#ababab")
        c.create_text(
            54, 289, text=self.isaks(dati["nosaukums"], 29),
            anchor="w", font=("Arial", 13), fill="#222222", tags="kartes"
        )

        c.create_rectangle(53, 320, 298, 377,
                           fill="white", outline="", tags="kartes")
        # Svītrkods ir tikai vizuāls makets, nevis īsts EAN/Code128 kods.
        generator = random.Random(dati["numurs"])
        x = 60
        while x < 290:
            platums = generator.choice((1, 1, 2, 3, 4))
            c.create_rectangle(x, 328, min(x + platums, 290), 355,
                               fill="black", outline="", tags="kartes")
            x += platums + generator.choice((1, 2, 3))
        c.create_text(
            175, 367, text=self.isaks(dati["numurs"], 35),
            font=("Arial", 9), fill="#111111", tags="kartes"
        )
        # Derīguma termiņu attēlojam uz kartes (vecām kartēm tas var nebūt).
        termins = dati.get("deriguma_termins")
        try:
            termins_datums = date.fromisoformat(termins) if termins else None
        except (TypeError, ValueError):
            termins_datums = None
        if termins_datums:
            beigusies = termins_datums < date.today()
            prefikss = "Beidzās:" if beigusies else "Derīga līdz:"
            teksts = f"{prefikss} {termins_datums:%d.%m.%Y}"
            krasa = "#9c2525" if beigusies else "#333333"
        else:
            teksts = "Derīguma termiņš nav norādīts"
            krasa = "#555555"
        c.create_text(53, 403, text=teksts, anchor="w",
                      font=("Arial", 9), fill=krasa, tags="kartes")

        c.create_oval(286, 394, 304, 412,
                      outline="#555555", tags="kartes")
        c.create_text(295, 403, text="i", font=("Arial", 10), tags="kartes")

    def zimet_kartes(self):
        c = self.ekrans
        c.delete("kartes")
        c.itemconfigure(self.fona_attels,
                        image=self.tirs_fons if self.kartes else self.fons)
        if not self.kartes:
            return  # Izmanto oriģinālā attēla '+' pogu.

        n = len(self.kartes)
        i = self.izveleta

        # Zīmējam no aizmugures uz priekšu. Indeksi ir cikliski:
        # pēc pēdējās kartes atkal nāk pirmā, un otrādi.
        if n >= 4:
            self.aizmugures_karte((i - 2) % n, 62, 200, 288, 357,
                                   "#626262", 213, gaišs=True)
        if n >= 5:
            self.aizmugures_karte((i + 2) % n, 62, 328, 288, 487,
                                   "#626262", 474, gaišs=True)
        if n >= 2:
            self.aizmugures_karte((i - 1) % n, 50, 229, 300, 405,
                                   "#909090", 242)
            self.aizmugures_karte((i + 1) % n, 50, 294, 300, 461,
                                   "#909090", 445)

        self.galvena_karte()
        if n > 1:
            c.create_text(175, 523, text=f"{i + 1} / {n}",
                          font=("Arial", 13, "bold"), fill="#444444",
                          tags="kartes")
            c.create_text(175, 549,
                          text="Ritini vai velc kartes uz augšu/leju",
                          font=("Arial", 10), fill="#555555", tags="kartes")
            c.create_text(175, 571,
                          text="Spied arī uz maliņām vai izmanto ↑ ↓",
                          font=("Arial", 10), fill="#555555", tags="kartes")

    def solis_no_klikšķa(self, x, y):
        """Atgriež soli pa apli, ja nospiesta redzama aizmugures karte."""
        if not 48 <= x <= 302 or len(self.kartes) < 2:
            return 0
        n = len(self.kartes)
        if 200 <= y < 229 and n >= 4:
            return -2
        if 229 <= y < 260:
            return -1
        if 426 < y <= 461:
            return 1
        if 461 < y <= 488 and n >= 5:
            return 2
        return 0

    def klikskis(self, notikums):
        x, y = notikums.x, notikums.y
        if 29 <= x <= 320 and 26 <= y <= 101:
            self.pievienot_karti()
        elif not self.kartes and 130 <= x <= 225 and 292 <= y <= 396:
            self.pievienot_karti()
        elif self.kartes and 285 <= x <= 306 and 392 <= y <= 414:
            self.radit_informaciju()
        else:
            solis = self.solis_no_klikšķa(x, y)
            if solis:
                self.parslegt(solis)

    def peles_nospiesana(self, notikums):
        """Atceras vietu, no kuras lietotājs sāk vilkt ar peli/pirkstu."""
        self.vilksanas_sakums = (notikums.x, notikums.y)

    def peles_vilksana(self, notikums):
        """Vilkt drīkst kartes zonā; pārslēgšana notiek pēc atlaišanas."""
        if self.vilksanas_sakums is None:
            return
        x0, y0 = self.vilksanas_sakums
        if 35 <= x0 <= 315 and 195 <= y0 <= 490 and self.kartes:
            self.ekrans.configure(cursor="fleur")

    def peles_atlaisana(self, notikums):
        """Pietiek ar ~40 pikseļu vertikālu vilcienu, lai mainītu karti."""
        if self.vilksanas_sakums is None:
            return
        x0, y0 = self.vilksanas_sakums
        self.vilksanas_sakums = None
        dx, dy = notikums.x - x0, notikums.y - y0
        kartes_zona = 35 <= x0 <= 315 and 195 <= y0 <= 490

        if kartes_zona and len(self.kartes) >= 2 and abs(dy) >= 40 and abs(dy) > abs(dx):
            # Uz augšu: nākamā karte. Uz leju: iepriekšējā.
            # Garāks vilciens pāršķir vairākas kartes (maksimums 3).
            skaits = min(3, max(1, round(abs(dy) / 110)))
            self.parslegt(skaits if dy < 0 else -skaits)
        elif abs(dx) < 12 and abs(dy) < 12:
            # Īss klikšķis joprojām darbojas kā agrāk.
            self.klikskis(notikums)
        self.peles_kustiba(notikums)

    def peles_kustiba(self, notikums):
        x, y = notikums.x, notikums.y
        galvene = 29 <= x <= 320 and 26 <= y <= 101
        plus = not self.kartes and 130 <= x <= 225 and 292 <= y <= 396
        info = bool(self.kartes) and 285 <= x <= 306 and 392 <= y <= 414
        self.ekrans.configure(cursor="hand2" if
                              galvene or plus or info or self.solis_no_klikšķa(x, y)
                              else "")

    def peles_ritenis(self, notikums):
        if notikums.delta:
            self.ritinat(-1 if notikums.delta > 0 else 1)

    def ritinat(self, solis):
        """Pārslēdz vienu karti ar ritentiņu; filtrē strauju notikumu plūsmu."""
        tagad = time.monotonic()
        if tagad - self.pedejais_ritinajums < 0.11:
            return
        self.pedejais_ritinajums = tagad
        self.parslegt(solis)

    def parslegt(self, solis):
        if len(self.kartes) < 2:
            return
        self.izveleta = (self.izveleta + solis) % len(self.kartes)
        self.zimet_kartes()

    def radit_informaciju(self):
        """Rāda aktīvās kartes datus, tostarp abus datumus."""
        if not self.kartes:
            return
        dati = self.kartes[self.izveleta]

        def radit_datumu(atslega):
            vertiba = dati.get(atslega)
            if not vertiba:
                return "Nav norādīts (vecā karte)"
            try:
                return date.fromisoformat(vertiba).strftime("%d.%m.%Y")
            except (TypeError, ValueError):
                return str(vertiba)

        messagebox.showinfo(
            "Kartes informācija",
            f"Nosaukums: {dati['nosaukums']}\n"
            f"Numurs: {dati['numurs']}\n"
            f"Derīga līdz: {radit_datumu('deriguma_termins')}\n"
            f"Pievienota: {radit_datumu('pievienosanas_datums')}",
            parent=self.logs,
        )

    def pievienot_karti(self):
        forma = tk.Toplevel(self.logs)
        forma.title("Pievienot jaunu karti")
        forma.resizable(False, False)
        forma.transient(self.logs)
        forma.grab_set()

        saturs = ttk.Frame(forma, padding=20)
        saturs.pack(fill="both", expand=True)
        ttk.Label(saturs, text="Kartes nosaukums:").pack(anchor="w")
        nosaukums = ttk.Entry(saturs, width=35)
        nosaukums.pack(fill="x", pady=(4, 13))
        ttk.Label(saturs, text="Kartes numurs:").pack(anchor="w")
        numurs = ttk.Entry(saturs, width=35)
        numurs.pack(fill="x", pady=(4, 13))
        ttk.Label(saturs, text="Derīguma termiņš (DD.MM.GGGG):").pack(anchor="w")
        deriguma_termins = ttk.Entry(saturs, width=35)
        deriguma_termins.pack(fill="x", pady=(4, 5))
        ttk.Label(saturs, text="Piemērs: 31.12.2027").pack(anchor="w", pady=(0, 16))

        def saglabat():
            vards = nosaukums.get().strip()
            kods = numurs.get().strip()
            termins_teksts = deriguma_termins.get().strip()
            if not vards or not kods or not termins_teksts:
                messagebox.showwarning(
                    "Trūkst datu",
                    "Ievadi kartes nosaukumu, numuru un derīguma termiņu!",
                    parent=forma,
                )
                return

            try:
                # Pārbauda precīzu formātu un to, vai datums eksistē.
                if not re.fullmatch(r"\d{2}\.\d{2}\.\d{4}", termins_teksts):
                    raise ValueError("Nepareizs datuma formāts")
                termins = datetime.strptime(termins_teksts, "%d.%m.%Y").date()
            except ValueError:
                messagebox.showwarning(
                    "Nepareizs datums",
                    "Derīguma termiņu ievadi formātā DD.MM.GGGG, "
                    "piemēram, 31.12.2027.",
                    parent=forma,
                )
                deriguma_termins.focus_set()
                return

            # Datumu, kad karte pievienota, nosaka automātiski datorā.
            jauna_karte = {
                "nosaukums": vards,
                "numurs": kods,
                "deriguma_termins": termins.isoformat(),
                "pievienosanas_datums": date.today().isoformat(),
            }
            self.kartes.append(jauna_karte)
            self.izveleta = len(self.kartes) - 1
            self.zimet_kartes()
            try:
                KARTU_FAILS.write_text(
                    json.dumps(self.kartes, ensure_ascii=False, indent=2),
                    encoding="utf-8",
                )
            except OSError:
                messagebox.showwarning(
                    "Uzmanību",
                    "Karte pievienota, bet neizdevās saglabāt failā.",
                    parent=forma,
                )
            forma.destroy()

        ttk.Button(saturs, text="Pievienot karti", command=saglabat).pack(fill="x")
        forma.bind("<Return>", lambda _e: saglabat())
        nosaukums.focus_set()


if __name__ == "__main__":
    sakne = tk.Tk()
    LojalitatesKartes(sakne)
    sakne.mainloop()
