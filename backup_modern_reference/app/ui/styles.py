class DesignTokens:
    # Colors
    PRIMARY = "#0F172A"       # Deep Navy
    SECONDARY = "#334155"     # Slate
    ACCENT = "#3B82F6"        # Bright Blue
    SUCCESS = "#10B981"       # Emerald
    DANGER = "#EF4444"        # Red
    WARNING = "#F59E0B"       # Amber
    INFO = "#06B6D4"          # Cyan
    
    # Backgrounds
    BG_DARK = "#0F172A"
    BG_CARD = "#1E293B"
    BG_APP = "#020617"
    
    # Text
    TEXT_MAIN = "#F8FAFC"
    TEXT_MUTED = "#94A3B8"
    BORDER = "#334155"

def apply_modern_style(app):
    style = f"""
        QMainWindow {{ background-color: {DesignTokens.BG_APP}; }}
        QWidget {{ color: {DesignTokens.TEXT_MAIN}; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; }}
        QPushButton#PrimaryButton {{
            background-color: {DesignTokens.ACCENT};
            border-radius: 8px;
            padding: 10px 20px;
            font-weight: bold;
        }}
        /* Add more styles as needed */
    """
    app.setStyleSheet(style)
