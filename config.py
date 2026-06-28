"""
WMS-CLAM-PRO — Configuration Globale
Société Amazones et Centaures (SAC)
"""


class Config:
    """Configuration de l'application WMS-CLAM-PRO."""

    # --- Serveur Flask API ---
    FLASK_HOST = "127.0.0.1"
    FLASK_PORT = 5001
    API_BASE_URL = f"http://{FLASK_HOST}:{FLASK_PORT}"
    DEBUG = False
    SECRET_KEY = "sge-sac-wms-clam-pro-2024"

    # --- Fenêtre Tkinter ---
    WINDOW_TITLE = "WMS-CLAM-PRO | SAC LOGISTICS"
    WINDOW_WIDTH = 1400
    WINDOW_HEIGHT = 900
    WINDOW_MIN_WIDTH = 1200
    WINDOW_MIN_HEIGHT = 800

    # --- Thème Ttk Industrial Light (extrait de DESIGN.md) ---
    COLORS = {
        "primary": "#00629d",
        "primary_container": "#00a2ff",
        "on_primary": "#ffffff",
        "on_primary_container": "#003659",
        "primary_fixed": "#cfe5ff",
        "primary_fixed_dim": "#99cbff",
        "on_primary_fixed": "#001d34",
        "on_primary_fixed_variant": "#004a78",
        "inverse_primary": "#99cbff",
        "surface": "#f7f9fc",
        "surface_dim": "#d8dadd",
        "surface_bright": "#f7f9fc",
        "surface_container_lowest": "#ffffff",
        "surface_container_low": "#f2f4f7",
        "surface_container": "#eceef1",
        "surface_container_high": "#e6e8eb",
        "surface_container_highest": "#e0e3e6",
        "surface_variant": "#e0e3e6",
        "on_surface": "#191c1e",
        "on_surface_variant": "#3f4852",
        "inverse_surface": "#2d3133",
        "inverse_on_surface": "#eff1f4",
        "outline": "#6f7883",
        "outline_variant": "#bec7d4",
        "error": "#ba1a1a",
        "on_error": "#ffffff",
        "error_container": "#ffdad6",
        "on_error_container": "#93000a",
        "secondary": "#545f6f",
        "on_secondary": "#ffffff",
        "secondary_container": "#d8e3f6",
        "on_secondary_container": "#5a6575",
        "secondary_fixed": "#d8e3f6",
        "secondary_fixed_dim": "#bcc7d9",
        "tertiary": "#505f76",
        "on_tertiary": "#ffffff",
        "tertiary_container": "#8d9db5",
        "on_tertiary_container": "#253449",
        "tertiary_fixed": "#d3e4fe",
        "background": "#f7f9fc",
        "on_background": "#191c1e",
        "success": "#2e7d32",
        "warning": "#f57c00",
    }

    # --- Typographie ---
    FONTS = {
        "display_lg": ("Hanken Grotesk", 48, "bold"),
        "headline_lg": ("Hanken Grotesk", 32, "bold"),
        "headline_md": ("Hanken Grotesk", 24),
        "headline_sm": ("Hanken Grotesk", 20),
        "body_lg": ("Hanken Grotesk", 18),
        "body_md": ("Hanken Grotesk", 16),
        "body_sm": ("Hanken Grotesk", 14),
        "label_lg": ("JetBrains Mono", 16),
        "label_md": ("JetBrains Mono", 14),
        "label_sm": ("JetBrains Mono", 12),
    }

    # --- Spacing (base 4px) ---
    SPACING = {
        "xs": 4,
        "sm": 8,
        "md": 16,
        "lg": 24,
        "xl": 40,
        "gutter": 20,
        "margin": 24,
    }

    # --- Dimensions UI ---
    SIDEBAR_WIDTH = 256
    TOPBAR_HEIGHT = 48
    FOOTER_HEIGHT = 32
    

# ---------------------------
# Configuration Base de Donnees
# ---------------------------
# Parametres de connexion a PostgreSQL
DATABASE = {
    "host": "localhost",
    "port": 5432,
    "dbname": "sge_db",
    "user": "sge_user",
    "password": "sge_pass",
    "schema": "sge",
    "options": "-c search_path=sge,public",
}
