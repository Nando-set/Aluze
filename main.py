"""
Punto de entrada de Aluze.
Ejecutar con: python main.py
"""
import tkinter as tk
from interfaz.ventana import AppAluze


if __name__ == "__main__":
    root = tk.Tk()
    app = AppAluze(root)
    root.mainloop()