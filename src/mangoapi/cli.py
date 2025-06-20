# mangoapi/cli.py
import argparse
import os
import subprocess

import uvicorn

def new():
    name = input("📁 Nombre del proyecto: ")
    subprocess.run(["django-admin", "startproject", name])
    print(f"✅ Proyecto creado: {name}")
    print(f"👉 cd {name} && mangoapi run")

def run():
    # Busca el nombre del directorio del proyecto Django
    current_dir = os.getcwd()
    project_dirs = [d for d in os.listdir(current_dir) if os.path.isdir(d) and os.path.isfile(os.path.join(d, "asgi.py"))]

    if not project_dirs:
        print("❌ No se encontró un archivo asgi.py en ningún subdirectorio.")
        return

    project_name = project_dirs[0]
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", f"{project_name}.settings")

    # Añade el directorio al sys.path para evitar problemas de importación
    import sys
    sys.path.insert(0, current_dir)

    import django
    django.setup()

    uvicorn.run(f"{project_name}.asgi:application", host="0.0.0.0", port=8000, reload=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=["new", "run", "scaffold"])
    args = parser.parse_args()

    if args.command == "new":
        new()
    elif args.command == "run":
        run()

if __name__ == "__main__":
    main()
