"""
Servicio de sincronización con GitHub.
Subida de cambios con pull --rebase previo.
"""
import subprocess
from datetime import datetime

from config import BASE_DIR, GITHUB_BRANCH


def subir_a_github():
    try:
        subprocess.run(["git", "add", "."], cwd=BASE_DIR, check=True, capture_output=True)

        msg = f"Actualización {datetime.now().strftime('%d/%m/%Y %H:%M')}"
        r = subprocess.run(["git", "commit", "-m", msg], cwd=BASE_DIR, capture_output=True)
        commit_out = (r.stdout or b"").decode() + (r.stderr or b"").decode()
        if "nothing to commit" in commit_out or "nada para hacer commit" in commit_out:
            return True, "ℹ️ No había cambios nuevos que subir."

        pull = subprocess.run(["git", "pull", "--rebase", "origin", GITHUB_BRANCH],
                              cwd=BASE_DIR, capture_output=True)
        pull_out = (pull.stdout or b"").decode() + (pull.stderr or b"").decode()

        if pull.returncode != 0:
            subprocess.run(["git", "rebase", "--abort"], cwd=BASE_DIR, capture_output=True)
            return False, ("⚠️ No se pudo sincronizar con GitHub.\n\n"
                           "Puede que haya cambios en el repo remoto que choquen.\n\n"
                           f"Detalle:\n{pull_out[:500]}")

        subprocess.run(["git", "push", "origin", GITHUB_BRANCH],
                       cwd=BASE_DIR, check=True, capture_output=True)

        return True, "✅ Subido a GitHub correctamente."
    except subprocess.CalledProcessError as e:
        error = (e.stderr or b"").decode() if e.stderr else str(e)
        return False, f"❌ Error:\n{error}"
    except FileNotFoundError:
        return False, "❌ Git no está instalado o no está en el PATH."
    except Exception as e:
        return False, f"❌ Error inesperado:\n{e}"