import tkinter as tk
import sqlite3 as sq3
import qrcode  as qr
import re
import os
import hashlib
from datetime import datetime
from PIL import ImageTk
from enum import Enum
from tkinter import ttk

WIDTH = 360
HEIGHT = 800

class State(Enum):
    MAIN_SCREEN = 0
    CARD_INFO = 1
    ADD_CARD = 2
    EDIT_CARD = 3

class Ordering(Enum):
    NO_ORDER = 0
    BY_LOCAT = 1
    BY_USAGE = 2
    BY_NAMES = 3

order_queries = [
    """SELECT *
    FROM card_info
    WHERE active = 1""",
    """SELECT *
    FROM card_info
    WHERE active = 1""",
    """select ci.uuid, ci.card_name, ci.code, ci.date
    from card_info as ci,card_stats as cs
    where ci.uuid = cs.card_uuid
    and ci.active = 1
    order by cs.times_used desc""",
    """SELECT *
    FROM card_info
    WHERE active = 1
    ORDER BY card_name ASC"""
    ]

display_queries = [
    """SELECT cd.color, cd.display_name
    FROM card_display AS cd, card_info AS ci, card_stats AS cs
    WHERE cd.card_uuid = ci.uuid
    AND ci.uuid = cs.card_uuid
    AND ci.active = 1""",
    """SELECT cd.color, cd.display_name
    FROM card_display AS cd, card_info AS ci, card_stats AS cs
    WHERE cd.card_uuid = ci.uuid
    AND ci.uuid = cs.card_uuid
    AND ci.active = 1""",
    """SELECT cd.color, cd.display_name
    FROM card_display AS cd, card_info AS ci, card_stats AS cs
    WHERE cd.card_uuid = ci.uuid
    AND ci.uuid = cs.card_uuid
    AND ci.active = 1
    ORDER BY cs.times_used DESC""",
    """SELECT cd.color, cd.display_name
    FROM card_display AS cd, card_info AS ci, card_stats AS cs
    WHERE cd.card_uuid = ci.uuid
    AND ci.uuid = cs.card_uuid
    AND ci.active = 1
    ORDER BY ci.card_name ASC"""
]

class App:
    def __init__(self, context: tk.Tk):
        self.ctx = context
        self.screen = tk.Canvas(context, width=WIDTH, height=HEIGHT)
        self.screen.pack()
        self.screen.focus_set()

        self.connection = sq3.connect("database.db")
        self.cursor = self.connection.cursor()
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS card_info (
                uuid INTEGER PRIMARY KEY, 
                card_name TEXT NOT NULL,
                code TEXT NOT NULL,
                date DATE,
                active BOOL DEFAULT 1
            )"""
        )
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS card_display (
                display_id INTEGER PRIMARY KEY,
                card_uuid INTEGER,
                display_name TEXT NOT NULL,
                color TEXT NOT NULL,
                FOREIGN KEY (card_uuid) REFERENCES card_info(uuid)
            );
        """)
        self.cursor.execute("""
            INSERT OR IGNORE INTO card_display
            (display_id, card_uuid, display_name, color)
            VALUES (0, NULL, 'Pievienot Karti', '#A1A1A1')
        """)
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS card_stats (
                card_uuid INTEGER PRIMARY KEY,
                times_used INTEGER DEFAULT 0,
                last_used DATE,
                FOREIGN KEY (card_uuid) REFERENCES card_info(uuid)
            );
        """)
        self.connection.commit()
        
        self.current_index = 0
        self.current_state = State.MAIN_SCREEN
        self.ordering = Ordering.NO_ORDER
        self.priority = []
        
        self.screen.bind("<Up>", lambda _: self.change_index(1))
        self.screen.bind("<Down>", lambda _: self.change_index(-1))
        
        self.update()


    def change_index(self, value):
        if self.current_state != State.MAIN_SCREEN:
            return
        self.current_index += value
        if self.current_index == len(self.display_info):
            self.current_index = 0
        elif self.current_index == -1:
            self.current_index = len(self.display_info)-1
        self.update()
    
    def squircle(self, x, y, width, height, radius, colour, outline="#666666", tag=''):
        points = [
            x+radius, y, x+width-radius, y, x+width, y, x+width, y+radius,
            x+width, y+height-radius, x+width, y+height, x+width-radius, y+height,
            x+radius, y+height, x, y+height, x, y+height-radius, x, y+radius, x, y,
        ]
        self.screen.create_polygon(
            points, smooth=True, splinesteps=10,
            fill=colour, outline=outline, width=1.7,
            tags=tag
        )

    def clicked_on_card(self):
        if self.current_index == 0:
            self.switch_state(State.ADD_CARD)
        else:
            self.switch_state(State.CARD_INFO)
    
    def main_screen(self):
        self.screen.focus_set()

        self.display_info = []
        self.display_info.extend(self.cursor.execute("""
            SELECT color, display_name FROM card_display WHERE display_id = 0
        """).fetchall())
        if self.ordering == Ordering.BY_LOCAT and not len(self.priority) == 0:
            self.display_info.extend(
                self.cursor.execute(
                    display_queries[0]
                ).fetchall()
            )
            self.cards = self.cursor.execute(
                order_queries[0]
            ).fetchall()

            self.cards.sort(
                key=lambda x: self.priority.index(x[1])
                if x[1] in self.priority else 999
            )
            self.display_info[1:] = sorted(
                self.display_info[1:],
                key=lambda x: self.priority.index(x[1])
                if x[1] in self.priority else 999
            )
        else:
            self.display_info.extend(
                self.cursor.execute(
                    display_queries[self.ordering.value]
                ).fetchall()
            )
            self.cards = self.cursor.execute(
                order_queries[self.ordering.value]
            ).fetchall()
        
        self.screen.create_rectangle(0, 0, 360, 80, fill="#818181", outline="#818181")
        for i in [-2, 2, -1, 1, 0]:
            card_height = 180 - (25*abs(i))
            card_index = (self.current_index + i) % len(self.display_info)
            self.squircle(
                WIDTH*(0.1+(abs(i)*0.05)),
                (HEIGHT-card_height)/2 + (40*(-i)),
                WIDTH*(1.0-0.2-(0.1*abs(i))),
                card_height,
                25,
                self.display_info[card_index][0],
                tag = f"karte_({i})"
                )
            self.screen.create_text(
                        WIDTH/2, HEIGHT/2,
                        text=self.display_info[card_index][1],
                        font=("Arial", 24, "bold"),
                        anchor="center",
                        width=int(WIDTH*(1.0-0.2-(0.1*abs(i)))),
                        justify='center',
                        tags=f"karte_({i})"
                    )
            self.screen.tag_bind(f"karte_({i})", "<Button-1>", lambda e: self.clicked_on_card())
        
        self.screen.create_text(
            WIDTH/2, HEIGHT-200,
            text=f"{self.current_index+1}/{len(self.display_info)}",
            font=("Arial", 16, "bold"),
            anchor="center"
        )

        def inc_enum():
            self.ordering = Ordering((self.ordering.value + 1)%4)
            self.update()
        
        self.screen.create_window(
            50, 100,
            window=tk.Button(
                self.ctx,
                text=self.ordering.name,
                font=("Ariel", 10),
                anchor='w',
                command=inc_enum
            )
        )
    
    def card_info(self):
        card_info = self.cards[self.current_index-1]
        card_stats = self.cursor.execute("""
            SELECT * FROM card_stats WHERE card_uuid = ?
        """, (card_info[0], )).fetchone()

        qr_code = qr.make(card_info[2])
        rgb_qr = qr_code.convert("RGB")
        rgb_qr.thumbnail((400, 250))
        rgb_qr.save("temp.png")
        self.card_code = ImageTk.PhotoImage(file=os.path.abspath("temp.png"))
        self.screen.create_image(
            WIDTH/2, HEIGHT/2,
            image=self.card_code,
            anchor="center",
            tags="code"
        )
        
        self.screen.create_text(
            WIDTH/2, 50,
            text=card_info[1],
            font=("Arial", 24, "bold"),
            width=int(WIDTH*0.7),
            justify='center',
            anchor="center"
        )
        self.screen.create_text(
            WIDTH/2, 80,
            text="Derīga līdz:",
            font=("Arial", 16),
            width=int(WIDTH*0.7),
            justify='center',
            anchor="center"
        )
        self.screen.create_text(
            WIDTH/2, 110,
            text= datetime.strptime(card_info[3], "%Y-%m-%d").strftime("%d.%m.%Y") if card_info[3] else "Nav norādīts",
            font=("Arial", 20),
            width=int(WIDTH*0.7),
            justify='center',
            anchor="center"
        )
        self.screen.create_text(
            WIDTH/2, 150,
            text=f"Reizes izmantots: {card_stats[1]}",
            font=("Arial", 12),
            width=int(WIDTH*0.7),
            justify='center',
            anchor="center"
        )
        self.screen.create_text(
            WIDTH/2, 175,
            text="Pēdējo reizi izmantota:",
            font=("Arial", 16),
            width=int(WIDTH*0.7),
            justify='center',
            anchor="center"
        )
        self.screen.create_text(
            WIDTH/2, 200,
            text = datetime.strptime(card_stats[2], "%Y-%m-%d %H:%M:%S").strftime("%d.%m.%Y %H:%M") if card_stats[2] else "Nav izmantota",
            font=("Arial", 16),
            width=int(WIDTH*0.7),
            justify='center',
            anchor="center"
        )
        

        self.cursor.execute("""
            UPDATE card_stats
            SET times_used = times_used + 1, last_used = datetime('now')
            WHERE card_uuid = ?
        """, (card_info[0], )),
        
        self.screen.create_window(
            WIDTH/2, HEIGHT-240,
            window=tk.Button(
                self.ctx,
                text="Dzēst",
                font=("Arial", 18),
                anchor='center',
                command=lambda : (
                    self.cursor.execute("""
                        UPDATE card_info
                        SET active = 0
                        WHERE uuid = ?
                    """, (card_info[0],)),
                    self.switch_state(State.MAIN_SCREEN),
                    self.change_index(-1)
                )
            )
        )

        self.screen.create_window(
            WIDTH/2, HEIGHT-180,
            window=tk.Button(
                self.ctx,
                text="Rediģēt",
                font=("Arial", 18),
                anchor='center',
                command=lambda: self.switch_state(State.EDIT_CARD)
            )
        )
        
        self.screen.create_window(
            WIDTH/2, HEIGHT-120,
            window=tk.Button(
                self.ctx,
                text="Atpakaļ",
                font=("Arial", 18),
                anchor='center',
                command=lambda: self.switch_state(State.MAIN_SCREEN)
            )
        )

    def add_card(self):
        error_msg = self.screen.create_text(
            WIDTH/2, HEIGHT-250,
            text="",
            font=("Arial", 16, "bold"),
            anchor="center",
            tags="message"
        )

        self.screen.create_text(
            WIDTH/2, 100,
            text="Pievienot Jaunu Karti",
            font=("Arial", 24, "bold"),
            anchor="center"
        )
        self.screen.create_text(
                    WIDTH/2, 150,
                    text="Nosaukums",
                    font=("Arial", 16, "bold"),
                    anchor="center"
                )
        title = tk.Entry(
                    self.ctx,
                    font=("Arial", 16, "normal"),
        )
        self.screen.create_window(
            WIDTH/2, 200,
            window=title,
            tags="title"
        )

        self.screen.create_text(
                    WIDTH/2, 250,
                    text="Kartes informācija",
                    font=("Arial", 16, "bold"),
                    anchor="center"
                )
        code = tk.Entry(
                    self.ctx,
                    font=("Arial", 16, "normal"),
        )
        self.screen.create_window(
            WIDTH/2, 300,
            window=code,
            tags="code"
        )

        self.screen.create_text(
                    WIDTH/2, 350,
                    text="Derīguma termiņš (formāts dd.mm.gggg)",
                    font=("Arial", 12, "bold"),
                    anchor="center"
                )
        date = tk.Entry(
                    self.ctx,
                    font=("Arial", 16, "normal"),
        )
        self.screen.create_window(
            WIDTH/2, 400,
            window=date,
            tags="date"
        )

        self.screen.create_text(
                    WIDTH/2, 450,
                    text="Krāsa (pimēras: #ff1212)",
                    font=("Arial", 12, "bold"),
                    anchor="center"
                )
        color = tk.Entry(
                    self.ctx,
                    font=("Arial", 16, "normal"),
        )
        self.screen.create_window(
            WIDTH/2, 500,
            window=color,
            tags="color"
        )

        def save(event=None):
            card_title = title.get().strip()
            card_code = code.get().strip()
            card_date = date.get().strip()
            card_color = color.get().strip()
            if not card_title or not card_code:
                self.screen.itemconfig(error_msg, text="Pietrūkst datu")
                return

            try:
                if card_date == "":
                    valid = None
                elif re.fullmatch(r"\d{2}\.\d{2}\.\d{4}", card_date):
                    valid = datetime.strptime(card_date, "%d.%m.%Y").date()
                else:
                    raise ValueError("Nepareizs datuma formāts")
            except ValueError:
                self.screen.itemconfig(error_msg, text="Nepareizs datuma formāts")
                return

            try:
                if card_color == "":
                    used_color = "#" + hashlib.sha256(card_code.encode()).hexdigest()[:6]
                elif re.fullmatch(r"#[0-9A-Fa-f][0-9A-Fa-f][0-9A-Fa-f][0-9A-Fa-f][0-9A-Fa-f][0-9A-Fa-f]", card_color):
                    used_color = card_color
                else:
                    raise ValueError("Nepareizs krāsas formāts")
            except ValueError:
                self.screen.itemconfig(error_msg, text="Nepareizs krāsas formāts")
                return

            exists = bool(self.cursor.execute("SELECT EXISTS (SELECT 1 FROM card_info WHERE card_name = ? AND code = ?)", (card_title, card_code)).fetchone()[0])
            if exists:
                if valid:
                    self.cursor.execute("""
                        UPDATE card_info
                        SET active = 1, date = ?
                        WHERE card_name = ? AND code = ?
                    """, (valid, card_title, card_code))
                else:
                    self.cursor.execute("""
                        UPDATE card_info
                        SET active = 1
                        WHERE card_name = ? AND code = ?
                    """, (card_title, card_code))
                card_uuid = self.cursor.lastrowid

                self.cursor.execute("""
                    UPDATE card_display
                    SET display_name = ?, color = ?
                    WHERE card_uuid = ?
                """, (card_title, used_color, card_uuid))
            else:
                if valid:
                    self.cursor.execute("INSERT INTO card_info (card_name, code, date) VALUES (?, ?, ?)", (card_title, card_code, valid))
                else:
                    self.cursor.execute("INSERT INTO card_info (card_name, code) VALUES (?, ?)", (card_title, card_code))
                
                card_uuid = self.cursor.lastrowid
                
                self.cursor.execute("""
                    INSERT INTO card_display
                    (card_uuid, display_name, color)
                    VALUES (?, ?, ?)
                """, (card_uuid, card_title, used_color))

            self.cursor.execute("""
                INSERT INTO card_stats
                (card_uuid)
                VALUES (?)
            """, (card_uuid,))
            
            self.screen.itemconfig(error_msg, text="Karte veiksmīgi pievienota")
            title.delete(0, tk.END)
            code.delete(0, tk.END)
            date.delete(0, tk.END)
            color.delete(0, tk.END)
            return

        self.screen.create_window(
            WIDTH/2, HEIGHT-180,
            window=tk.Button(
                self.ctx,
                text="Pievienot",
                font=("Arial", 18),
                anchor='center',
                command=save
            )
        )

        self.screen.create_window(
            WIDTH/2, HEIGHT-130,
            window=tk.Button(
                self.ctx,
                text="Pievienot no attēla",
                font=("Arial", 18),
                anchor='center',
                state="disabled"
            )
        )
        
        self.screen.create_window(
            WIDTH/2, HEIGHT-80,
            window=tk.Button(
                self.ctx,
                text="Atcelt",
                font=("Arial", 18),
                anchor='center',
                command=lambda: self.switch_state(State.MAIN_SCREEN)
            )
        )

    def edit_card(self):
        error_msg = self.screen.create_text(
            WIDTH/2, HEIGHT-250,
            text="",
            font=("Arial", 16, "bold"),
            anchor="center",
            tags="message"
        )

        self.screen.create_text(
            WIDTH/2, 100,
            text="Rediģēt Kartes Informāciju",
            font=("Arial", 24, "bold"),
            width= WIDTH,
            justify="center",
            anchor="center"
        )

        self.screen.create_text(
                    WIDTH/2, 150,
                    text="Nosaukums",
                    font=("Arial", 16, "bold"),
                    anchor="center"
                )
        title = tk.Entry(
                    self.ctx,
                    font=("Arial", 16, "normal"),
        )
        self.screen.create_window(
            WIDTH/2, 200,
            window=title,
            tags="title"
        )

        self.screen.create_text(
                    WIDTH/2, 250,
                    text="Kartes informācija",
                    font=("Arial", 16, "bold"),
                    anchor="center"
                )
        code = tk.Entry(
                    self.ctx,
                    font=("Arial", 16, "normal"),
        )
        self.screen.create_window(
            WIDTH/2, 300,
            window=code,
            tags="code"
        )

        self.screen.create_text(
                    WIDTH/2, 350,
                    text="Derīguma termiņš (formāts dd.mm.gggg)",
                    font=("Arial", 12, "bold"),
                    anchor="center"
                )
        date = tk.Entry(
                    self.ctx,
                    font=("Arial", 16, "normal"),
        )
        self.screen.create_window(
            WIDTH/2, 400,
            window=date,
            tags="date"
        )

        self.screen.create_text(
                    WIDTH/2, 450,
                    text="Krāsa (pimēras: #ff1212)",
                    font=("Arial", 12, "bold"),
                    anchor="center"
                )
        color = tk.Entry(
                    self.ctx,
                    font=("Arial", 16, "normal"),
        )
        self.screen.create_window(
            WIDTH/2, 500,
            window=color,
            tags="color"
        )

        card_info = self.cards[self.current_index-1]

        title.insert(0, card_info[1])
        code.insert(0, card_info[2])
        date.insert(0, datetime.strptime(card_info[3], "%Y-%m-%d").strftime("%d.%m.%Y") if card_info[3] else '')

        color.insert(0, self.cursor.execute(
            "SELECT color FROM card_display WHERE card_uuid = ?", (card_info[0],)
        ).fetchone()[0])

        def save(event=None):
            card_title = title.get().strip()
            card_code = code.get().strip()
            card_date = date.get().strip()
            card_color = color.get().strip()
            if not card_title or not card_code:
                self.screen.itemconfig(error_msg, text="Pietrūkst datu")
                return

            try:
                if card_date == "":
                    valid = None
                elif re.fullmatch(r"\d{2}\.\d{2}\.\d{4}", card_date):
                    valid = datetime.strptime(card_date, "%d.%m.%Y").date()
                else:
                    raise ValueError("Nepareizs datuma formāts")
            except ValueError:
                self.screen.itemconfig(error_msg, text="Nepareizs datuma formāts")
                return

            try:
                if card_color == "":
                    used_color = "#" + hashlib.sha256(card_code.encode()).hexdigest()[:6]
                elif re.fullmatch(r"#[0-9A-Fa-f][0-9A-Fa-f][0-9A-Fa-f][0-9A-Fa-f][0-9A-Fa-f][0-9A-Fa-f]", card_color):
                    used_color = card_color
                else:
                    raise ValueError("Nepareizs krāsas formāts")
            except ValueError:
                self.screen.itemconfig(error_msg, text="Nepareizs krāsas formāts")
                return

            if valid:
                self.cursor.execute("""
                    UPDATE card_info
                    SET card_name = ?, code = ?, date = ?
                    WHERE uuid = ?
                """, (card_title, card_code, valid, card_info[0]))
            else:
                self.cursor.execute("""
                    UPDATE card_info
                    SET card_name = ?, code = ?
                    WHERE uuid = ?
                """, (card_title, card_code, card_info[0]))

            self.cursor.execute("""
                UPDATE card_display
                SET display_name = ?, color = ?
                WHERE card_uuid = ?
            """, (card_title, used_color, card_info[0]))
            
            self.screen.itemconfig(error_msg, text="Karte veiksmīgi pievienota")
            title.delete(0, tk.END)
            code.delete(0, tk.END)
            date.delete(0, tk.END)
            color.delete(0, tk.END)
            return

        self.screen.create_window(
            WIDTH/2, HEIGHT-130,
            window=tk.Button(
                self.ctx,
                text="Atjaunot",
                font=("Arial", 18),
                anchor='center',
                command=save
            )
        )
        
        self.screen.create_window(
            WIDTH/2, HEIGHT-80,
            window=tk.Button(
                self.ctx,
                text="Atcelt",
                font=("Arial", 18),
                anchor='center',
                command=lambda: self.switch_state(State.CARD_INFO)
            )
        )

    def switch_state(self, state):
        self.current_state = state
        print(f"state switched to: {state}")
        self.connection.commit()
        self.update()

    def update(self):
        self.screen.delete("all")
        match (self.current_state):
            case State.MAIN_SCREEN:
                self.cursor.execute("SELECT * FROM card_info")
                self.main_screen()
            case State.CARD_INFO:
                self.card_info()
            case State.ADD_CARD:
                self.add_card()
            case State.EDIT_CARD:
                self.edit_card()

        self.screen.create_window(
            WIDTH-50, 50,
            window=tk.Button(
                self.ctx,
                text="DEBUG",
                anchor='w',
                command=self.debug_window
            )
        )
    
    def debug_window(self):
        window = tk.Toplevel(self.ctx)
        window.title("Tuvākie veikali")
        window.resizable(False, False)
        window.transient(self.ctx)
        window.grab_set()

        ctx = ttk.Frame(window, padding=20)
        ctx.pack(fill="both", expand=True)

        ttk.Label(
            ctx,
            text="Tuvākie veikali",
            font=("Arial", 16, "bold")
        ).pack(anchor="center")
        ttk.Label(
            ctx,
            text="Pirmais (pats tuvākais)",
            font=("Arial", 12)
        ).pack(anchor="w")
        first = ttk.Entry(ctx)
        first.pack(fill='x')
        ttk.Label(
            ctx,
            text="Otrais",
            font=("Arial", 12)
        ).pack(anchor="w")
        second = ttk.Entry(ctx)
        second.pack(fill='x')
        ttk.Label(
            ctx,
            text="Trešais",
            font=("Arial", 12)
        ).pack(anchor="w")
        third = ttk.Entry(ctx)
        third.pack(fill='x')
        ttk.Label(
            ctx,
            text="Ceturtais",
            font=("Arial", 12)
        ).pack(anchor="w")
        forth = ttk.Entry(ctx)
        forth.pack(fill='x')
        ttk.Label(
            ctx,
            text="Piektais",
            font=("Arial", 12)
        ).pack(anchor="w")
        fifth = ttk.Entry(ctx)
        fifth.pack(fill='x')

        def save(event=None):
            self.priority = []
            if first.get().strip() != '':
                self.priority.append(first.get().strip())
            if second.get().strip() != '':
                self.priority.append(second.get().strip())
            if third.get().strip() != '':
                self.priority.append(third.get().strip())
            if forth.get().strip() != '':
                self.priority.append(forth.get().strip())
            if fifth.get().strip() != '':
                self.priority.append(fifth.get().strip())
            self.ordering = Ordering.BY_LOCAT
            self.update()
            
        ttk.Button(
            ctx,
            text="Saglabat",
            command=save
        ).pack(anchor='center')

    def on_close(self):
        self.connection.commit()
        self.connection.close()
        self.ctx.destroy()


def main():    
    window = tk.Tk()
    window.title("Prototips")
    window.resizable(False, False)
    window.configure(bg="white")
    app = App(window)
    window.protocol("WM_DELETE_WINDOW", app.on_close)
    window.mainloop()

if (__name__ == "__main__"):
    main()