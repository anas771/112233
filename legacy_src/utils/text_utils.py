import tkinter as tk
from ui.constants import HAS_ARABIC, FT_SMALL, FT_BODY, CLR

if HAS_ARABIC:
    import arabic_reshaper
    from bidi.algorithm import get_display

def prepare_text(text):
    if not text: 
        return ""
    if HAS_ARABIC: 
        try:
            return get_display(arabic_reshaper.reshape(str(text)))
        except:
            return str(text)
    return str(text)

def fmt_num(n, dec=0):
    try:
        if n is None or n == "": return "0"
        n = float(n)
        if dec == 0:
            return f"{int(n):,}"
        else:
            return f"{n:,.{dec}f}"
    except: 
        return "—"

def lbl_entry(parent, text, row, col, width=16, readonly=False, colspan=1):
    from ui.widgets import UILabel, UIEntry
    UILabel(parent, text=text, font=FT_SMALL, bg=CLR["bg"], fg=CLR["text2"], anchor="e").grid(row=row, column=col, sticky="e", padx=(6,2), pady=8)
    v = tk.StringVar()
    state = "readonly" if readonly else "normal"
    bg = "#e9ecef" if readonly else CLR["white"]
    e = UIEntry(parent, textvariable=v, width=width, font=FT_BODY, state=state, bg=bg, relief="solid", highlightthickness=1, highlightbackground=CLR["border"])
    e.grid(row=row, column=col+1, sticky="ew", padx=(2,12), pady=8, columnspan=colspan)
    e.configure(justify="right")
    return v
