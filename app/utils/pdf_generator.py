import os
from fpdf import FPDF
from datetime import datetime

class PDF(FPDF):
    def header(self):
        self.set_font('Times', 'B', 16)
        self.cell(0, 10, 'Reporte de Asesoría Legal - AbogadoEC', 0, 1, 'C')
        self.ln(5)

    def footer(self):
        self.set_y(-15)
        self.set_font('Times', 'I', 8)
        self.cell(0, 10, f'Página {self.page_no()}', 0, 0, 'C')

def generar_pdf_pension(nombre_archivo, salario, hijos, porcentaje, total_estimado, nivel="N/A"):
    """
    Genera un PDF con el cálculo detallado y lo guarda en la carpeta 'static'.
    """

    output_folder = "static"
    os.makedirs(output_folder, exist_ok=True)

    filepath = os.path.join(output_folder, nombre_archivo)

    pdf = PDF()
    pdf.add_page()
    pdf.set_font("Times", size=12)

    texto = [
        f"Fecha: {datetime.now().strftime('%d/%m/%Y %H:%M')}",
        "-------------------------------------------------------------",
        f"CÁLCULO DE PENSIÓN ALIMENTICIA (Estimado)",
        "-------------------------------------------------------------",
        f"Salario Base Reportado: ${salario}",
        f"Número de Hijos: {hijos}",
        f"Nivel de Tabla MIES: {nivel}",
        f"Porcentaje Aplicable (Tabla 2025): {porcentaje}",
        "-------------------------------------------------------------",
        f"TOTAL MENSUAL A PAGAR: ${total_estimado}",
        "-------------------------------------------------------------",
        "",
        "NOTA LEGAL:",
        "Este cálculo es referencial basado en la Tabla de Pensiones",
        "Alimenticias Mínimas 2025 del MIES.",
        "Para fijar este valor legalmente, debe acudir a un Juez de la Familia."
    ]

    for linea in texto:
        pdf.cell(0, 10, linea.encode('latin-1', 'replace').decode('latin-1'), 0, 1)

    pdf.output(filepath)
    return filepath