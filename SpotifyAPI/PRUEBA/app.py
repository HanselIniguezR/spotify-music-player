# -*- coding: utf-8 -*-
# app.py

import csv
import threading
import tkinter as tk
import os
try:
    import customtkinter as ctk
    HAS_CUSTOMTK = True
except Exception:
    ctk = None
    HAS_CUSTOMTK = False

from tkinter import messagebox, filedialog
from typing import Optional, Tuple
import sys
# Allow forcing the use of plain tkinter instead of customtkinter.
# You can set the environment variable SPOTI_FORCE_TK=1 or run with the
# command-line flag --tk to force the fallback UI.
force_tk = os.environ.get('SPOTI_FORCE_TK') in ('1', 'true', 'True') or any(arg == '--tk' for arg in sys.argv[1:])
if force_tk:
    HAS_CUSTOMTK = False
    ctk = None
import ctypes
import webbrowser
import urllib.parse

# Import constants - prefer package-qualified import when running as module
try:
    from PRUEBA.constants import *
except ModuleNotFoundError:
    from constants import *
# Ensure project root is on sys.path so package imports (PRUEBA.*) work
from pathlib import Path
_script_dir = Path(__file__).resolve().parent
_project_root = _script_dir.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))
# Import UI implementation using package-qualified imports so resolution works
# whether running from project root or from inside the package.
try:
    if HAS_CUSTOMTK:
        from PRUEBA.ui import AppUI
    else:
        from PRUEBA.ui_tk import AppUI
    # Centralized spotify client utilities (in the PRUEBA package)
    from PRUEBA.spoti_client import read_credentials, create_spotify_client
except ModuleNotFoundError:
    # Fallback to local module imports when running the script directly from inside PRUEBA/
    if HAS_CUSTOMTK:
        from ui import AppUI
    else:
        from ui_tk import AppUI
    from spoti_client import read_credentials, create_spotify_client

def ms_to_minsec(ms: int) -> str:
    total_seconds = max(0, ms // 1000)
    minutes = total_seconds // 60
    seconds = total_seconds % 60
    return f"{minutes}:{seconds:02d}"

def seconds_to_hms(total_seconds: int) -> str:
    h = total_seconds // 3600
    m = (total_seconds % 3600) // 60
    s = total_seconds % 60
    if h > 0:
        return f"{h}:{m:02d}:{s:02d}"
    return f"{m}:{s:02d}"

# read_credentials and create_spotify_client are provided by PRUEBA/spoti_client.py

BaseApp = ctk.CTk if HAS_CUSTOMTK else tk.Tk

class SpotifySearchApp(BaseApp):
    def __init__(self):
        # If using customtkinter, initialize as before. For tk.Tk this also works.
        super().__init__()
        self.title(APP_TITLE)
        self.geometry(f"{APP_DEF_SIZE[0]}x{APP_DEF_SIZE[1]}")
        self.minsize(*APP_MIN_SIZE)

        self.query_var = tk.StringVar(value="")
        self.limit_var = tk.StringVar(value="10")
        self.type_var = tk.StringVar(value="track")
        self.status_var = tk.StringVar(value="Listo.")
        
        # --- DOS VARIABLES DE ORDENAMIENTO INDEPENDIENTES ---
        self.search_sort_var = tk.StringVar(value="Más Popular")
        self.playlist_sort_var = tk.StringVar(value="Nombre A-Z")

        self._checked_rows: set[str] = set()
        self._row_meta: dict[str, dict] = {}
        self._list_items: list[dict] = []
        self._stats_var = tk.StringVar(value="En lista: 0  —  Total: 0:00 minutos")

        self.sp = self._init_app_client()
        self.ui = AppUI(self, self)
        self.bind("<Return>", lambda _e: self.start_search())

    def _init_app_client(self) -> spotipy.Spotify:
        try:
            return create_spotify_client()
        except Exception as e:
            messagebox.showerror("Error de Spotify", f"No se pudo inicializar el cliente:\n{e}")
            self.after(100, self.destroy)
            raise SystemExit

    # --- LÓGICA DE ORDENAMIENTO ---
    def _sort_treeview(self, tree, col, reverse):
        """Función genérica que ordena una tabla específica."""
        source_data = self._row_meta if tree == self.ui.tree else {item['track_id']: item for item in self._list_items}
        children = tree.get_children('')
        data_list = []
        
        for item_id in children:
            data_id = tree.item(item_id, "tags")[0] if tree == self.ui.playlist_tree else item_id
            
            if col == "duration_secs":
                sort_key = source_data.get(data_id, {}).get("duration_secs", 0)
            elif col == "popularity":
                sort_key = source_data.get(data_id, {}).get("popularity", 0)
            else:
                sort_key = source_data.get(data_id, {}).get("title", "").lower()
            
            data_list.append((sort_key, item_id))

        data_list.sort(key=lambda t: t[0], reverse=reverse)

        for index, (val, item_id) in enumerate(data_list):
            tree.move(item_id, '', index)

    def _get_sort_params(self, choice):
        """Convierte la opción del menú en parámetros de ordenamiento."""
        sort_map = {
            "Más Popular": ("popularity", True), "Menos Popular": ("popularity", False),
            "Nombre A-Z": ("title", False), "Nombre Z-A": ("title", True),
            "Mayor Duración": ("duration_secs", True), "Menor Duración": ("duration_secs", False)
        }
        return sort_map.get(choice)

    def _on_search_sort_change(self, choice):
        """Se activa al cambiar el orden de la tabla de búsqueda."""
        col, reverse = self._get_sort_params(choice)
        self._sort_treeview(self.ui.tree, col, reverse)

    def _on_playlist_sort_change(self, choice):
        """Se activa al cambiar el orden de la tabla de playlist."""
        col, reverse = self._get_sort_params(choice)
        self._sort_treeview(self.ui.playlist_tree, col, reverse)

    # ... (el resto de los métodos como _on_tree_click, _on_item_double_click, etc., se quedan igual) ...

    def _on_tree_click(self, event):
        region = self.ui.tree.identify("region", event.x, event.y)
        row = self.ui.tree.identify_row(event.y)
        if region not in ("cell", "tree") or not row: return
        column = self.ui.tree.identify_column(event.x)
        if column != "#0": return
        if row in self._checked_rows:
            self._checked_rows.remove(row)
            if self.ui.unchecked_img: self.ui.tree.item(row, image=self.ui.unchecked_img)
        else:
            self._checked_rows.add(row)
            if self.ui.checked_img: self.ui.tree.item(row, image=self.ui.checked_img)

    def _on_item_double_click(self, event):
        tree = event.widget
        selected_item = tree.selection()
        if not selected_item: return
        item_id = selected_item[0]
        
        if tree == self.ui.tree:
            meta = self._row_meta.get(item_id)
            if not meta: return
            title, artist = meta.get("title"), meta.get("artist")
        else:
            values = tree.item(item_id, "values")
            if not values or len(values) < 2: return
            title, artist = values[0], values[1]

        query = f"{artist} {title}"
        search_query = urllib.parse.quote_plus(query)
        url = f"https://music.youtube.com/search?q={search_query}"
        webbrowser.open_new_tab(url)

    def start_search(self):
        query = self.query_var.get().strip()
        if not query:
            messagebox.showinfo("Atención", "Escribe un término de búsqueda.")
            return
        try:
            limit_val = int(self.limit_var.get())
        except (ValueError, TypeError): limit_val = 10
        limit = max(1, min(50, limit_val))
        self.status_var.set(f"Buscando “{query}”...")
        self.ui.tree.delete(*self.ui.tree.get_children())
        self._checked_rows.clear()
        self._row_meta.clear()
        search_type = self.type_var.get()
        threading.Thread(target=self._do_search, args=(query, limit, search_type), daemon=True).start()

    def _do_search(self, query: str, limit: int, search_type: str):
        try:
            results = self.sp.search(q=query, limit=limit, type=search_type)
            self.after(0, lambda: self._populate_results(results, search_type, query))
        except Exception as e:
            self.after(0, lambda: self._on_search_error(e))

    def _on_search_error(self, e: Exception):
        messagebox.showerror("Error al buscar", str(e))
        self.status_var.set("Ocurrió un error.")

    def _populate_results(self, results: dict, search_type: str, query: str):
        if search_type != "track":
            messagebox.showinfo("Info", "La tabla detallada solo funciona para el tipo 'track'.")
            self.status_var.set("Listo.")
            return
        items = results.get("tracks", {}).get("items", [])
        for track in items:
            title, artists, album = track.get("name") or "—", ", ".join([a.get("name", "") for a in (track.get("artists") or [])]) or "—", (track.get("album") or {}).get("name") or "—"
            duration_ms, duration = track.get("duration_ms", 0), ms_to_minsec(track.get("duration_ms", 0))
            row_values = (title, artists, album, duration)
            iid = self.ui.tree.insert("", "end", image=self.ui.unchecked_img, values=row_values, tags=(track.get("id"),))
            self._row_meta[iid] = {
                "artist": artists, "title": title, "album": album, "duration": duration,
                "duration_secs": max(0, duration_ms // 1000), "popularity": track.get("popularity", 0),
                "url": (track.get("external_urls") or {}).get("spotify", ""), "track_id": track.get("id", ""),
            }
        self.status_var.set(f"Mostrando {len(items)} resultado(s).")
        self._on_search_sort_change(self.search_sort_var.get())

    def add_selected_to_text_list(self):
        if not self._checked_rows:
            messagebox.showinfo("Sin selección", "Marca al menos una canción para añadir.")
            return
        added_count = 0
        current_playlist_ids = {self.ui.playlist_tree.item(item, "tags")[0] for item in self.ui.playlist_tree.get_children()}
        for iid in list(self._checked_rows):
            meta = self._row_meta.get(iid)
            track_id = meta.get("track_id")
            if not meta or track_id in current_playlist_ids: continue
            row_values = (meta["title"], meta["artist"], meta["duration"])
            self.ui.playlist_tree.insert("", "end", values=row_values, tags=(track_id,))
            self._list_items.append(meta)
            added_count += 1
        for iid in list(self._checked_rows):
            self.ui.tree.item(iid, image=self.ui.unchecked_img)
        self._checked_rows.clear()
        self.status_var.set(f"Añadidas {added_count} canción(es) a la lista.")
        self._update_stats()
        self._on_playlist_sort_change(self.playlist_sort_var.get())

    def list_remove_selected(self):
        selected_items = self.ui.playlist_tree.selection()
        if not selected_items: return
        selected_track_ids = {self.ui.playlist_tree.item(item, "tags")[0] for item in selected_items}
        self._list_items = [item for item in self._list_items if item.get("track_id") not in selected_track_ids]
        for item in selected_items:
            self.ui.playlist_tree.delete(item)
        self.status_var.set(f"Eliminadas {len(selected_items)} canción(es).")
        self._update_stats()

    def list_clear(self):
        if not self.ui.playlist_tree.get_children() or not messagebox.askyesno("Vaciar lista", "¿Seguro?"):
            return
        self.ui.playlist_tree.delete(*self.ui.playlist_tree.get_children())
        self._list_items.clear()
        self.status_var.set("Lista vaciada.")
        self._update_stats()

    def _update_stats(self):
        count = len(self._list_items)
        total_secs = sum(int(item.get("duration_secs", 0)) for item in self._list_items)
        self._stats_var.set(f"En lista: {count}  —  Total: {seconds_to_hms(total_secs)} minutos")

if __name__ == "__main__":
    try:
        if sys.platform == "win32":
            ctypes.windll.shcore.SetProcessDpiAwareness(2)
    except Exception as e:
        print(f"No se pudo establecer DPI Awareness: {e}")
    from PIL import Image, ImageTk
    app = SpotifySearchApp()
    app.mainloop()