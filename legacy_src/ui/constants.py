import os
import sys
import tkinter as tk

# Library Availability Flags
try:
    import ttkbootstrap as ttkb
    HAS_TTKB = True
except ImportError:
    HAS_TTKB = False

try:
    import matplotlib
    HAS_MATPLOTLIB = True
except ImportError:
    HAS_MATPLOTLIB = False

try:
    from fpdf import FPDF
    HAS_FPDF = True
except ImportError:
    HAS_FPDF = False

try:
    import arabic_reshaper
    from bidi.algorithm import get_display
    HAS_ARABIC = True
except ImportError:
    HAS_ARABIC = False

try:
    import openpyxl
    HAS_OPENPYXL = True
except ImportError:
    HAS_OPENPYXL = False

# Application Paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DB_PATH  = os.path.join(BASE_DIR, "poultry_data.db")
ASSETS_DIR = os.path.join(BASE_DIR, "assets")

# UI Constants - "Classic Plus" (Microsoft Fluent Palette)
CLR = {
    "bg":       "#F3F2F1", # رمادي ناعم جداً
    "header":   "#005A9E", # أزرق احترافي
    "nav":      "#F3F2F1",
    "white":    "#FFFFFF",
    "profit":   "#107C10", # أخضر فورست
    "loss":     "#A80000", # أحمر غامق
    "warn":     "#847545",
    "profit_bg":"#DFF6DD",
    "loss_bg":  "#FDE7E9",
    "warn_bg":  "#FFF4CE",
    "info_bg":  "#EFF6FC",
    "border":   "#EDEBE9",
    "text":     "#323130", # فحم داكن
    "text2":    "#605E5C", # رمادي النصوص الثانوية
    "accent":   "#0078D4", # لون التفاعل الرئيسي
    "daily_bg": "#FFFFFF",
}

# Typography
FN = "Segoe UI" if sys.platform == "win32" else "Arial"
FT_TITLE  = (FN, 14, "bold")
FT_HEADER = (FN, 11, "bold")
FT_BODY   = (FN, 10)
FT_SMALL  = (FN, 9)
FT_TINY   = (FN, 8)
