"""
Punto de entrada de Aluze.
Ejecutar con: python main.py
"""
import customtkinter as ctk
import tkinter as tk

from interfaz.ventana import AppAluze


if __name__ == "__main__":
    # Configurar tema global de customtkinter
    ctk.set_appearance_mode("dark")           # modo oscuro
    ctk.set_default_color_theme("dark-blue")  # tema azul oscuro

    root = ctk.CTk()  # ← usar CTk en vez de tk.Tk
    app = AppAluze(root)
    root.mainloop()