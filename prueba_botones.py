import tkinter as tk
from interfaz.botones import boton_principal, boton_secundario, boton_peligro

root = tk.Tk()
root.title("Prueba de botones")
root.geometry("500x400")
root.configure(bg="#1e293b")

frame = tk.Frame(root, bg="#1e293b", padx=20, pady=20)
frame.pack(fill=tk.BOTH, expand=True)

boton_principal(frame, "✨  Generar cotización",
                lambda: print("Principal")).pack(fill=tk.X, pady=(0, 10))

fila = tk.Frame(frame, bg="#1e293b")
fila.pack(fill=tk.X, pady=(0, 10))
boton_secundario(fila, "🌐  Panel", lambda: print("Panel")).pack(side=tk.LEFT, padx=(0, 5))
boton_secundario(fila, "☁️  Subir", lambda: print("Subir")).pack(side=tk.LEFT)

fila2 = tk.Frame(frame, bg="#1e293b")
fila2.pack(fill=tk.X, pady=(0, 10))
boton_secundario(fila2, "🔄  Actualizar", lambda: print("Actualizar")).pack(side=tk.LEFT, padx=(0, 5))
boton_secundario(fila2, "🔁  Regenerar", lambda: print("Regenerar")).pack(side=tk.LEFT)

boton_peligro(frame, "🗑️  Borrar todo",
              lambda: print("Borrar")).pack(fill=tk.X)

root.mainloop()