import tkinter as tk
from tkinter import ttk
from ui.constants import HAS_TTKB

if HAS_TTKB:
    import ttkbootstrap as ttkb

# Base Classes
WindowBase = ttkb.Window if HAS_TTKB else tk.Tk

class ToplevelBase(ttkb.Toplevel if HAS_TTKB else tk.Toplevel):
    def __init__(self, master=None, **kwargs):
        super().__init__(master, **kwargs)
        if HAS_TTKB:
            self.attributes("-alpha", 0.0)
            self._fade_in()
    
    def _fade_in(self):
        alpha = self.attributes("-alpha")
        if alpha < 1.0:
            self.attributes("-alpha", alpha + 0.15)
            self.after(25, self._fade_in)

class UIFrame(ttkb.Frame if HAS_TTKB else tk.Frame):
    def __init__(self, master=None, **kwargs):
        if HAS_TTKB:
            for k in ['bg', 'fg', 'pady', 'padx', 'relief', 'bd', 'highlightbackground', 'highlightthickness']: kwargs.pop(k, None)
        super().__init__(master, **kwargs)

class UILabel(ttkb.Label if HAS_TTKB else tk.Label):
    def __init__(self, master=None, **kwargs):
        if HAS_TTKB:
            for k in ['bg', 'fg', 'activebackground', 'activeforeground', 'relief', 'bd', 'padx', 'pady']: kwargs.pop(k, None)
        super().__init__(master, **kwargs)

class UIButton(ttkb.Button if HAS_TTKB else tk.Button):
    def __init__(self, master=None, **kwargs):
        self.original_style = kwargs.get('bootstyle', 'primary')
        if HAS_TTKB:
            for k in ['bg', 'fg', 'activebackground', 'activeforeground', 'relief', 'bd', 'font', 'padx', 'pady']: kwargs.pop(k, None)
            txt = kwargs.get('text', '')
            if 'حذف' in txt or '🗑' in txt: kwargs.setdefault('bootstyle', 'danger')
            elif 'إلغاء' in txt: kwargs.setdefault('bootstyle', 'secondary')
            elif 'حفظ' in txt or 'إضافة' in txt or '➕' in txt: kwargs.setdefault('bootstyle', 'success')
            elif 'PDF' in txt: kwargs.setdefault('bootstyle', 'info')
            else: kwargs.setdefault('bootstyle', 'primary')
        super().__init__(master, **kwargs)
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)

    def _on_enter(self, e):
        if HAS_TTKB:
            try:
                curr = self.cget("bootstyle")
                if "-outline" not in str(curr):
                    self.configure(bootstyle=f"{curr}-outline")
            except tk.TclError: pass
            
    def _on_leave(self, e):
        if HAS_TTKB:
            try:
                self.configure(bootstyle=self.original_style)
            except tk.TclError: pass

class UIEntry(ttkb.Entry if HAS_TTKB else tk.Entry):
    def __init__(self, master=None, **kwargs):
        if HAS_TTKB:
            for k in ['bg', 'fg', 'insertbackground', 'relief', 'bd', 'highlightthickness', 'highlightbackground', 'padx', 'pady']: kwargs.pop(k, None)
        super().__init__(master, **kwargs)

class UILabelFrame(ttkb.Labelframe if HAS_TTKB else tk.LabelFrame):
    def __init__(self, master=None, **kwargs):
        if HAS_TTKB:
            for k in ['bg', 'fg', 'pady', 'padx', 'relief', 'bd', 'font', 'labelanchor']: kwargs.pop(k, None)
            kwargs.setdefault('bootstyle', 'primary')
        super().__init__(master, **kwargs)

def lbl_entry(parent, text, row, col, width=16, readonly=False, colspan=1):
    from ui.constants import CLR, FT_SMALL, FT_BODY
    UILabel(parent, text=text, font=FT_SMALL, bg=CLR["bg"], fg=CLR["text2"], anchor="e").grid(row=row, column=col, sticky="e", padx=(6,2), pady=8)
    v = tk.StringVar()
    state = "readonly" if readonly else "normal"
    bg = "#e9ecef" if readonly else CLR["white"]
    e = UIEntry(parent, textvariable=v, width=width, font=FT_BODY, state=state, bg=bg, relief="solid", highlightthickness=1, highlightbackground=CLR["border"])
    e.grid(row=row, column=col+1, sticky="ew", padx=(2,12), pady=8, columnspan=colspan)
    e.configure(justify="right")
    return v
