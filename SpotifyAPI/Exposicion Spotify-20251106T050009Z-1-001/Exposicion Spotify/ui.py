# -*- coding: utf-8 -*-
# ui.py
import tkinter as tk
from tkinter import ttk
import customtkinter as ctk
from PIL import Image, ImageTk

# --- Paleta de Colores ---
COLOR_BG = "#121212"
COLOR_SURFACE = "#1E1E1E"
COLOR_ACCENT = "#3F51B5"
COLOR_TEXT = "#FFFFFF"
COLOR_TEXT_MUTED = "#B3B3B3"

class AppUI:
    def __init__(self, master, controller):
        self.master = master
        self.controller = controller

        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        try:
            unchecked_img_data = Image.open("images/unchecked.png").resize((18, 18), Image.Resampling.LANCZOS)
            checked_img_data = Image.open("images/checked.png").resize((18, 18), Image.Resampling.LANCZOS)
            self.unchecked_img = ImageTk.PhotoImage(unchecked_img_data)
            self.checked_img = ImageTk.PhotoImage(checked_img_data)
        except FileNotFoundError:
            print("Advertencia: No se encontraron las imágenes para los checkboxes en la carpeta /images.")
            self.unchecked_img = None
            self.checked_img = None

        self._setup_treeview_style()
        self._build_layout()

    def _setup_treeview_style(self):
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Treeview",
                        background=COLOR_SURFACE,
                        fieldbackground=COLOR_SURFACE,
                        foreground=COLOR_TEXT,
                        rowheight=35,
                        borderwidth=0,
                        relief="flat")
        style.map("Treeview", background=[("selected", COLOR_ACCENT)])
        style.configure("Treeview.Heading",
                        background=COLOR_BG,
                        foreground=COLOR_TEXT_MUTED,
                        font=("Segoe UI", 10, "bold"),
                        relief="flat")
        style.map("Treeview.Heading", background=[("active", COLOR_BG)])

    def _build_layout(self):
        self.master.grid_columnconfigure(0, weight=1)
        self.master.grid_rowconfigure(0, weight=1)

        paned_window = ttk.PanedWindow(self.master, orient=tk.HORIZONTAL)
        paned_window.grid(row=0, column=0, sticky="nsew", padx=12, pady=12)

        left = ctk.CTkFrame(paned_window, fg_color=COLOR_BG)
        right = ctk.CTkFrame(paned_window, fg_color=COLOR_BG, width=450)

        paned_window.add(left, weight=1)
        paned_window.add(right)

        self._build_header(left)
        self._build_table(left)
        self._build_footer(left)
        self._build_text_list_panel(right)

    def _build_header(self, parent):
        parent.grid_columnconfigure(0, weight=1)
        header = ctk.CTkFrame(parent, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=10, pady=(10, 5))
        
        ctk.CTkLabel(header, text="Buscar canciones en Spotify", font=("Segoe UI", 20, "bold")).grid(row=0, column=0, columnspan=6, sticky="w", pady=(0, 10))
        
        # --- Fila 1: Etiquetas ---
        ctk.CTkLabel(header, text="Inserta el artista a buscar").grid(row=1, column=0, sticky="w")
        ctk.CTkLabel(header, text="Límite").grid(row=1, column=1, sticky="w")
        ctk.CTkLabel(header, text="Tipo").grid(row=1, column=2, sticky="w")
        
        # --- NUEVA ETIQUETA PARA ORDENAR ---
        ctk.CTkLabel(header, text="Ordenar por").grid(row=1, column=3, sticky="w")

        # --- Fila 2: Controles ---
        ctk.CTkEntry(header, textvariable=self.controller.query_var, width=300).grid(row=2, column=0, sticky="ew", padx=(0, 8))
        ctk.CTkEntry(header, textvariable=self.controller.limit_var, width=50).grid(row=2, column=1, sticky="w", padx=(0, 8))
        ctk.CTkComboBox(header, variable=self.controller.type_var, values=["track", "album", "artist", "playlist", "show", "episode"], width=120, state="readonly").grid(row=2, column=2, sticky="w", padx=(0, 8))

        # --- NUEVO MENÚ DESPLEGABLE MOVIDO AQUÍ ---
        sort_options = ["Más Popular", "Menos Popular", "Nombre A-Z", "Nombre Z-A", "Mayor Duración", "Menor Duración"]
        ctk.CTkComboBox(header, variable=self.controller.search_sort_var, values=sort_options, width=140, state="readonly", command=self.controller._on_search_sort_change).grid(row=2, column=3, sticky="w", padx=(0, 8))
        
        header.grid_columnconfigure(4, weight=1) # Espacio flexible
        
        ctk.CTkButton(header, text="Añadir a lista", command=self.controller.add_selected_to_text_list, fg_color=COLOR_SURFACE, hover_color="#2E2E2E").grid(row=2, column=5, sticky="e", padx=(0, 8))
        ctk.CTkButton(header, text="Buscar", command=self.controller.start_search).grid(row=2, column=6, sticky="e")


    def _build_table(self, parent):
        # --- AJUSTES EN LAS FILAS DEL GRID ---
        parent.grid_rowconfigure(1, weight=1) # La tabla ahora ocupa la fila 1

        # --- EL FRAME DE ORDENAMIENTO FUE ELIMINADO DE AQUÍ ---

        container = ctk.CTkFrame(parent, fg_color="transparent")
        container.grid(row=1, column=0, sticky="nsew", padx=10, pady=5) # La tabla ahora está en la fila 1
        container.grid_columnconfigure(0, weight=1)
        container.grid_rowconfigure(0, weight=1)

        columns = ("title", "artist", "album", "duration")
        self.tree = ttk.Treeview(container, columns=columns, show="tree headings", selectmode="browse")
        
        self.tree.column("#0", width=40, anchor="center", stretch=False)
        self.tree.heading("#0", text="✓")
        self.tree.heading("title", text="Título")
        self.tree.heading("artist", text="Artista")
        self.tree.heading("album", text="Álbum")
        self.tree.heading("duration", text="Duración")

        self.tree.column("title", width=320, anchor="w")
        self.tree.column("artist", width=220, anchor="w")
        self.tree.column("album", width=220, anchor="w")
        self.tree.column("duration", width=90, anchor="center")
        
        self.tree.grid(row=0, column=0, sticky="nsew")
        scrollbar = ctk.CTkScrollbar(container, command=self.tree.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        self.tree.bind("<Button-1>", self.controller._on_tree_click)
        self.tree.bind("<Double-1>", self.controller._on_item_double_click)

    def _build_footer(self, parent):
        footer = ctk.CTkFrame(parent, fg_color="transparent")
        footer.grid(row=2, column=0, sticky="ew", padx=10, pady=(5, 10)) # El footer ahora está en la fila 2
        ctk.CTkLabel(footer, textvariable=self.controller.status_var, text_color=COLOR_TEXT_MUTED).pack(side="left")

    def _build_text_list_panel(self, parent):
        parent.grid_rowconfigure(2, weight=1)
        parent.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(parent, text="Lista de Reproduccion", font=("Segoe UI", 20, "bold")).grid(row=0, column=0, sticky="w", padx=10, pady=10)
        
        sort_frame = ctk.CTkFrame(parent, fg_color="transparent")
        sort_frame.grid(row=1, column=0, sticky="e", padx=10, pady=(5, 0))
        ctk.CTkLabel(sort_frame, text="Ordenar por:").pack(side="left", padx=(0, 8))
        sort_options = ["Nombre A-Z", "Nombre Z-A", "Mayor Duración", "Menor Duración", "Más Popular", "Menos Popular"]
        ctk.CTkComboBox(sort_frame, variable=self.controller.playlist_sort_var, values=sort_options, width=140, state="readonly", command=self.controller._on_playlist_sort_change).pack(side="left")

        list_container = ctk.CTkFrame(parent, fg_color="transparent")
        list_container.grid(row=2, column=0, sticky="nsew", padx=10, pady=5)
        list_container.grid_columnconfigure(0, weight=1)
        list_container.grid_rowconfigure(0, weight=1)

        playlist_cols = ("title", "artist", "duration")
        self.playlist_tree = ttk.Treeview(list_container, columns=playlist_cols, show="headings", selectmode="extended")

        self.playlist_tree.heading("title", text="Título")
        self.playlist_tree.heading("artist", text="Artista")
        self.playlist_tree.heading("duration", text="Duración")
        self.playlist_tree.column("title", width=150, anchor="w")
        self.playlist_tree.column("artist", width=120, anchor="w")
        self.playlist_tree.column("duration", width=60, anchor="center")
        
        self.playlist_tree.grid(row=0, column=0, sticky="nsew")
        playlist_scrollbar = ctk.CTkScrollbar(list_container, command=self.playlist_tree.yview)
        playlist_scrollbar.grid(row=0, column=1, sticky="ns")
        self.playlist_tree.configure(yscrollcommand=playlist_scrollbar.set)
        self.playlist_tree.bind("<Double-1>", self.controller._on_item_double_click)
        
        controls = ctk.CTkFrame(parent, fg_color="transparent")
        controls.grid(row=3, column=0, sticky="ew", padx=10, pady=5)
        ctk.CTkButton(controls, text="Eliminar", command=self.controller.list_remove_selected, fg_color=COLOR_SURFACE, hover_color="#2E2E2E").pack(side="left")
        ctk.CTkButton(controls, text="Vaciar", command=self.controller.list_clear, fg_color=COLOR_SURFACE, hover_color="#2E2E2E").pack(side="left", padx=8)
        
        bottom = ctk.CTkFrame(parent, fg_color="transparent")
        bottom.grid(row=4, column=0, sticky="ew", padx=10, pady=10)
        ctk.CTkLabel(bottom, textvariable=self.controller._stats_var, text_color=COLOR_TEXT_MUTED).pack(side="right")