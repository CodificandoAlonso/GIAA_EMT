import json
import os

BASE = "/home/hectoralv22/Desktop/CATEDRA/FILES/Lines_details/ROUTES/"

def split_toA_toB(filename):
    try:
        with open(BASE + filename, "r", encoding="utf-8") as f:
            raw = f.read().strip()
    except FileNotFoundError:
        print(f"[!] No se encontró el archivo: {filename}")
        return

    # Extraer la parte JSON después de la 6ª coma
    json_part = raw.split(",", 6)[-1]

    if json_part.startswith('"') and json_part.endswith('"'):
        json_part = json_part[1:-1]

    # Guardar depuración para ver qué se está intentando parsear
    dbg_file = BASE + os.path.splitext(filename)[0] + "_DEBUG.json"
    with open(dbg_file, "w", encoding="utf-8") as dbg:
        dbg.write(json_part[:2000])
    print(f"[DEBUG] Guardado extracto en {dbg_file}")

    # Intentar parsear
    try:
        data = json.loads(json_part)
    except json.JSONDecodeError as e:
        print(f"[!] Error JSON en {filename}: {e}")
        return

    # Mostrar claves encontradas
    print(f"[INFO] {filename} contiene claves: {list(data.keys())}")

    base_out = os.path.splitext(filename)[0]

    if "toA" in data:
        outA = BASE + base_out + "_toA.geojson"
        with open(outA, "w", encoding="utf-8") as f:
            json.dump(data["toA"], f, ensure_ascii=False, indent=2)
        print(f"[✓] Generado {outA}")

    if "toB" in data:
        outB = BASE + base_out + "_toB.geojson"
        with open(outB, "w", encoding="utf-8") as f:
            json.dump(data["toB"], f, ensure_ascii=False, indent=2)
        print(f"[✓] Generado {outB}")


def procesar_lista(lista_txt):
    try:
        with open(lista_txt, "r", encoding="utf-8") as f:
            archivos = [line.strip() for line in f if line.strip()]
    except FileNotFoundError:
        print(f"[!] No se encontró el archivo de lista: {lista_txt}")
        return

    for archivo in archivos:
        split_toA_toB(archivo)


if __name__ == "__main__":
    procesar_lista(BASE + "input.txt")
