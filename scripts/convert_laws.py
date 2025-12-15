"""import pymupdf4llm
import pathlib

# Define your source PDF paths
files = {
    "laboral": "Codigo-de-Trabajo-ecuador.pdf",
    "transito": "LOTAIP_6_Ley-Organica-de-Transporte-Terrestre-Transito-y-Seguridad-Vial-2021.pdf",
    "pensiones": "TABLA DE PENSIONES ALIMENTICIAS MINIMAS 2025.pdf"
}

# Create output folder
output_dir = pathlib.Path("data")
output_dir.mkdir(exist_ok=True)

for key, filename in files.items():
    print(f"Converting {filename}...")

    # 1. Convert PDF to Markdown (LlamaIndex compatible format)
    md_text = pymupdf4llm.to_markdown(filename)

    # 2. Save as .md
    output_path = output_dir / f"{key}.md"
    output_path.write_text(md_text, encoding="utf-8")

    print(f"✔ Saved: {output_path}")

print("All laws converted successfully!")"""