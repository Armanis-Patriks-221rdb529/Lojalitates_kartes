import tkinter as tk
import sqlite3 as sq3
import qrcode  as qr
import barcode as bc
import re
import os
import hashlib
from datetime import date, datetime
from PIL import ImageTk
from enum import Enum

WIDTH = 360
HEIGHT = 800

class State(Enum):
    MAIN_SCREEN = 0
    CARD_INFO = 1
    ADD_CARD = 2
    SETTINGS = 3

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
                date DATE
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
        self.connection.commit()
        #self.screen.create_window(WIDTH/2, 110, window=tk.Entry(self.ctx, font=("Arial", 12)), width=200, height=40, anchor="center")
        self.display_info = self.cursor.execute("SELECT color, display_name FROM card_display").fetchall()
        self.cards = self.cursor.execute("SELECT * FROM card_info").fetchall()
        self.current_index = 0
        self.current_state = State.MAIN_SCREEN
        self.screen.bind("<Up>", lambda _: self.curr_index(1))
        self.screen.bind("<Down>", lambda _: self.curr_index(-1))
        self.update()


    def curr_index(self, value):
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
        self.display_info = self.cursor.execute("SELECT color, display_name FROM card_display").fetchall()
        self.cards = self.cursor.execute("SELECT * FROM card_info").fetchall()
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
            WIDTH/2, 100,
            text=self.current_index,
            font=("Arial", 10, "bold"),
            anchor="center"
        )

    def card_info(self):
        card_info = self.cards[self.current_index-1]
        print(card_info)
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
            WIDTH/2, 100,
            text=card_info[1],
            font=("Arial", 24, "bold"),
            width=int(WIDTH*0.7),
            justify='center',
            anchor="center"
        )
        
        self.screen.create_window(
            WIDTH/2, HEIGHT-120,
            window=tk.Button(
                self.ctx,
                text="Atcelt",
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

            self.cursor.execute("INSERT INTO card_info (card_name, code, date) VALUES (?, ?, ?)", (card_title, card_code, valid))

            card_uuid = self.cursor.lastrowid

            self.cursor.execute("""
                INSERT INTO card_display
                (card_uuid, display_name, color)
                VALUES (?, ?, ?)
            """, (card_uuid, card_title, used_color))
            
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
            WIDTH/2, HEIGHT-120,
            window=tk.Button(
                self.ctx,
                text="Atcelt",
                font=("Arial", 18),
                anchor='center',
                command=lambda: self.switch_state(State.MAIN_SCREEN)
            )
        )

    def switch_state(self, state):
        self.current_state = state
        print(f"state switched to: {state}")
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
        window.title = "debug"
        window.resizable(False, False)
        window.transient(self.ctx)
        window.grab_set()

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