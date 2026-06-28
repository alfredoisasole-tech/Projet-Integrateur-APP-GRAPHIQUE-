"""
Thème Ttk Industrial Light — Design System natif Tkinter.

Traduit les spécifications de DESIGN.md en styles ttk.Style().
Base 'clam' choisie pour les coins nets (sharp corners) et le
contrôle maximal de l'apparence.
"""

import tkinter as tk
import tkinter.ttk as ttk

# ============================================================
# PALETTE DE COULEURS (Ttk Industrial Light — DESIGN.md)
# ============================================================
PRIMARY = "#00629d"
PRIMARY_CONTAINER = "#00a2ff"
ON_PRIMARY = "#ffffff"
SURFACE = "#f7f9fc"
SURFACE_DIM = "#d8dadd"
SURFACE_CONTAINER = "#eceef1"
SURFACE_CONTAINER_LOW = "#f2f4f7"
SURFACE_CONTAINER_HIGH = "#e6e8eb"
SURFACE_CONTAINER_HIGHEST = "#e0e3e6"
SURFACE_LOWEST = "#ffffff"
ON_SURFACE = "#191c1e"
ON_SURFACE_VARIANT = "#3f4852"
OUTLINE = "#6f7883"
OUTLINE_VARIANT = "#bec7d4"
SECONDARY = "#545f6f"
SECONDARY_CONTAINER = "#d8e3f6"
TERTIARY = "#505f76"
ERROR = "#ba1a1a"
ERROR_CONTAINER = "#ffdad6"
SUCCESS = "#2e7d32"
WARNING = "#f57c00"
INVERSE_SURFACE = "#2d3133"
INVERSE_ON_SURFACE = "#eff1f4"

# ============================================================
# TYPOGRAPHIE
# ============================================================
FONT_DISPLAY = ("Segoe UI", 42, "bold")
FONT_HEADLINE_LG = ("Segoe UI", 28, "bold")
FONT_HEADLINE_MD = ("Segoe UI", 22, "bold")
FONT_HEADLINE_SM = ("Segoe UI", 18, "bold")
FONT_BODY_LG = ("Segoe UI", 16)
FONT_BODY_MD = ("Segoe UI", 14)
FONT_BODY_SM = ("Segoe UI", 12)
FONT_LABEL_LG = ("Consolas", 14, "bold")
FONT_LABEL_MD = ("Consolas", 12)
FONT_LABEL_SM = ("Consolas", 10)
FONT_LABEL_SM_UPPER = ("Consolas", 10)


def apply_theme(root):
    """Applique le thème Ttk Industrial Light à l'application.

    Args:
        root: La fenêtre Tk racine.
    """
    style = ttk.Style(root)
    style.theme_use("clam")

    # ----------------------------------------------------------
    # FRAMES
    # ----------------------------------------------------------
    style.configure("TFrame", background=SURFACE)

    style.configure(
        "Card.TFrame", background=SURFACE_LOWEST, borderwidth=1, relief="solid"
    )

    style.configure("Header.TFrame", background=SURFACE_CONTAINER_HIGH)

    style.configure("Sidebar.TFrame", background=SURFACE_LOWEST)

    style.configure("Topbar.TFrame", background=SURFACE_LOWEST, borderwidth=0)

    style.configure("Footer.TFrame", background=INVERSE_SURFACE)

    style.configure("Primary.TFrame", background=PRIMARY)

    # ----------------------------------------------------------
    # LABELS
    # ----------------------------------------------------------
    style.configure(
        "TLabel", background=SURFACE, foreground=ON_SURFACE, font=FONT_BODY_MD
    )

    style.configure(
        "Display.TLabel",
        background=SURFACE_LOWEST,
        foreground=ON_SURFACE,
        font=FONT_DISPLAY,
    )

    style.configure(
        "Headline.TLabel",
        background=SURFACE_LOWEST,
        foreground=ON_SURFACE,
        font=FONT_HEADLINE_LG,
    )

    style.configure(
        "HeadlineMd.TLabel",
        background=SURFACE_LOWEST,
        foreground=ON_SURFACE,
        font=FONT_HEADLINE_MD,
    )

    style.configure(
        "HeadlineSm.TLabel",
        background=SURFACE_LOWEST,
        foreground=ON_SURFACE,
        font=FONT_HEADLINE_SM,
    )

    style.configure(
        "Body.TLabel",
        background=SURFACE_LOWEST,
        foreground=ON_SURFACE,
        font=FONT_BODY_MD,
    )

    style.configure(
        "BodySm.TLabel",
        background=SURFACE_LOWEST,
        foreground=ON_SURFACE_VARIANT,
        font=FONT_BODY_SM,
    )

    style.configure(
        "Label.TLabel",
        background=SURFACE_LOWEST,
        foreground=OUTLINE,
        font=FONT_LABEL_SM,
    )

    style.configure(
        "LabelUpper.TLabel",
        background=SURFACE_CONTAINER_HIGH,
        foreground=OUTLINE,
        font=FONT_LABEL_SM_UPPER,
    )

    style.configure(
        "Primary.TLabel",
        background=SURFACE_LOWEST,
        foreground=PRIMARY,
        font=FONT_LABEL_LG,
    )

    style.configure(
        "Inverse.TLabel",
        background=INVERSE_SURFACE,
        foreground=INVERSE_ON_SURFACE,
        font=FONT_BODY_SM,
    )

    style.configure(
        "Error.TLabel", background=ERROR_CONTAINER, foreground=ERROR, font=FONT_LABEL_MD
    )

    style.configure(
        "Success.TLabel",
        background=SURFACE_LOWEST,
        foreground=SUCCESS,
        font=FONT_LABEL_MD,
    )

    style.configure(
        "Warning.TLabel",
        background=SURFACE_LOWEST,
        foreground=WARNING,
        font=FONT_LABEL_MD,
    )

    style.configure(
        "Sidebar.TLabel",
        background=SURFACE_LOWEST,
        foreground=ON_SURFACE_VARIANT,
        font=FONT_BODY_SM,
    )

    style.configure(
        "SidebarActive.TLabel",
        background=SECONDARY_CONTAINER,
        foreground=ON_SURFACE,
        font=("Segoe UI", 12, "bold"),
    )

    # ----------------------------------------------------------
    # BOUTONS
    # ----------------------------------------------------------
    style.configure(
        "TButton",
        font=FONT_LABEL_MD,
        background=SURFACE_CONTAINER,
        foreground=ON_SURFACE,
        borderwidth=1,
        relief="solid",
        padding=(16, 8),
    )
    style.map(
        "TButton",
        background=[("active", SURFACE_CONTAINER_HIGH), ("pressed", OUTLINE_VARIANT)],
    )

    style.configure(
        "Primary.TButton",
        font=FONT_LABEL_LG,
        background=PRIMARY,
        foreground=ON_PRIMARY,
        borderwidth=0,
        relief="flat",
        padding=(20, 10),
    )
    style.map(
        "Primary.TButton", background=[("active", "#004a78"), ("pressed", "#003659")]
    )

    style.configure(
        "Secondary.TButton",
        font=FONT_LABEL_MD,
        background=SURFACE_LOWEST,
        foreground=ON_SURFACE,
        borderwidth=1,
        relief="solid",
        padding=(16, 8),
    )
    style.map(
        "Secondary.TButton",
        background=[("active", SURFACE_CONTAINER), ("pressed", SURFACE_CONTAINER_HIGH)],
    )

    style.configure(
        "Danger.TButton",
        font=FONT_LABEL_MD,
        background=ERROR,
        foreground=ON_PRIMARY,
        borderwidth=0,
        relief="flat",
        padding=(16, 8),
    )

    style.configure(
        "Sidebar.TButton",
        font=FONT_BODY_SM,
        background=SURFACE_LOWEST,
        foreground=ON_SURFACE_VARIANT,
        borderwidth=0,
        relief="flat",
        padding=(12, 10),
        anchor="w",
    )
    style.map("Sidebar.TButton", background=[("active", SURFACE_CONTAINER_LOW)])

    style.configure(
        "SidebarActive.TButton",
        font=("Segoe UI", 12, "bold"),
        background=SECONDARY_CONTAINER,
        foreground=ON_SURFACE,
        borderwidth=0,
        relief="flat",
        padding=(12, 10),
        anchor="w",
    )

    # ----------------------------------------------------------
    # ENTRY / COMBOBOX
    # ----------------------------------------------------------
    style.configure(
        "TEntry",
        font=FONT_BODY_MD,
        fieldbackground=SURFACE_LOWEST,
        borderwidth=1,
        relief="solid",
        padding=(8, 6),
    )

    style.configure(
        "TCombobox",
        font=FONT_BODY_MD,
        fieldbackground=SURFACE_LOWEST,
        borderwidth=1,
        padding=(8, 6),
    )

    # ----------------------------------------------------------
    # TREEVIEW (Tables de données haute densité)
    # ----------------------------------------------------------
    style.configure(
        "Treeview",
        font=FONT_BODY_SM,
        background=SURFACE_LOWEST,
        foreground=ON_SURFACE,
        fieldbackground=SURFACE_LOWEST,
        borderwidth=1,
        relief="solid",
        rowheight=32,
    )

    style.configure(
        "Treeview.Heading",
        font=FONT_LABEL_SM,
        background=SURFACE_CONTAINER_HIGH,
        foreground=OUTLINE,
        borderwidth=1,
        relief="solid",
        padding=(8, 6),
    )
    style.map("Treeview.Heading", background=[("active", SURFACE_CONTAINER_HIGHEST)])

    style.map(
        "Treeview",
        background=[("selected", SECONDARY_CONTAINER)],
        foreground=[("selected", ON_SURFACE)],
    )

    # ----------------------------------------------------------
    # PROGRESSBAR
    # ----------------------------------------------------------
    style.configure(
        "Primary.Horizontal.TProgressbar",
        background=PRIMARY,
        troughcolor=SURFACE_CONTAINER,
        borderwidth=0,
        thickness=8,
    )

    style.configure(
        "Success.Horizontal.TProgressbar",
        background=SUCCESS,
        troughcolor=SURFACE_CONTAINER,
        borderwidth=0,
        thickness=8,
    )

    style.configure(
        "Warning.Horizontal.TProgressbar",
        background=WARNING,
        troughcolor=SURFACE_CONTAINER,
        borderwidth=0,
        thickness=8,
    )

    style.configure(
        "Error.Horizontal.TProgressbar",
        background=ERROR,
        troughcolor=SURFACE_CONTAINER,
        borderwidth=0,
        thickness=8,
    )

    # ----------------------------------------------------------
    # LABELFRAME
    # ----------------------------------------------------------
    style.configure(
        "TLabelframe",
        background=SURFACE_LOWEST,
        foreground=ON_SURFACE,
        borderwidth=1,
        relief="solid",
    )
    style.configure(
        "TLabelframe.Label",
        background=SURFACE_LOWEST,
        foreground=OUTLINE,
        font=FONT_LABEL_SM,
    )

    # ----------------------------------------------------------
    # SEPARATOR
    # ----------------------------------------------------------
    style.configure("TSeparator", background=OUTLINE_VARIANT)

    # ----------------------------------------------------------
    # SCROLLBAR
    # ----------------------------------------------------------
    style.configure(
        "TScrollbar",
        background=SURFACE_CONTAINER,
        troughcolor=SURFACE,
        borderwidth=0,
        arrowsize=14,
    )

    # ----------------------------------------------------------
    # NOTEBOOK (tabs)
    # ----------------------------------------------------------
    style.configure("TNotebook", background=SURFACE, borderwidth=0)
    style.configure(
        "TNotebook.Tab",
        font=FONT_LABEL_MD,
        background=SURFACE_CONTAINER,
        foreground=OUTLINE,
        padding=(16, 8),
    )
    style.map(
        "TNotebook.Tab",
        background=[("selected", SURFACE_LOWEST)],
        foreground=[("selected", PRIMARY)],
    )
