import subprocess
import os

lingo_executable = r"C:\LINGO64_19\Lingo64_19.exe" 
lingo_command_file = "ModelLINGO2.lng"

def run_lingo_model():
    """Exécute automatiquement le modèle LINGO et enregistre les résultats."""
    try:
        current_directory = os.path.dirname(os.path.abspath(__file__))
        command = [lingo_executable, os.path.join(current_directory, lingo_command_file)]
        
        # Rediriger la sortie standard et d'erreur pour éviter les blocages
        process = subprocess.Popen(command, cwd=current_directory, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        process.wait(timeout=600)

    except subprocess.TimeoutExpired:
        process.kill()
        print("ERREUR : Le processus LINGO a dépassé le délai et a été interrompu.")
    except Exception as e:
        print(f"Une erreur est survenue : {e}")
        

        if process.returncode == 0:
            print("✅ LINGO terminé avec succès !")
        else:
            print(f"❌ Erreur : LINGO s'est terminé avec le code {process.returncode}")

        # Optionnel : sauvegarder la sortie brute dans un fichier texte
        with open("Lingo_output_console.txt", "w", encoding="utf-8") as f:
            f.write(process.stdout)
            if process.stderr:
                f.write("\n--- ERREURS ---\n")
                f.write(process.stderr)

    except subprocess.TimeoutExpired:
        print("⏰ Temps d'exécution dépassé (LINGO a été arrêté automatiquement).")
    except Exception as e:
        print(f"⚠️ Erreur lors de l'exécution du modèle LINGO : {e}")

