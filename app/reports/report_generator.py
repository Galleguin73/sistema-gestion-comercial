# Archivo: app/reports/report_generator.py

from fpdf import FPDF
from app.database import articulos_db
from datetime import datetime

class ReportPDF(FPDF):
    """Clase personalizada para crear PDFs con cabecera y pie de página."""
    def header(self):
        self.set_font('Helvetica', 'B', 15)
        self.cell(0, 10, self.title, 0, 1, 'C')
        self.set_font('Helvetica', '', 10)
        self.cell(0, 10, f"Generado el: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}", 0, 1, 'C')
        self.ln(5)

    def footer(self):
        self.set_y(-15)
        self.set_font('Helvetica', 'I', 8)
        self.cell(0, 10, f'Página {self.page_no()}/{{nb}}', 0, 0, 'C')

def generar_listado_articulos(path):
    """Crea un PDF con la lista completa de artículos."""
    try:
        pdf = ReportPDF('P', 'mm', 'A4')
        pdf.set_title("Listado General de Artículos")
        pdf.alias_nb_pages()
        pdf.add_page()
        
        pdf.set_font('Helvetica', 'B', 10)
        # Anchos de columna: Código(35), Nombre(75), Marca(30), Stock(30)
        pdf.cell(35, 10, 'Código', 1, 0, 'C')
        pdf.cell(75, 10, 'Nombre', 1, 0, 'C')
        pdf.cell(30, 10, 'Marca', 1, 0, 'C')
        pdf.cell(30, 10, 'Stock', 1, 1, 'C')

        pdf.set_font('Helvetica', '', 9)
        # Usamos la función que ya teníamos, incluyendo inactivos.
        articulos = articulos_db.obtener_articulos(incluir_inactivos=True)
        for articulo in articulos:
            # articulo = (id, codigo, marca, nombre, stock, precio, estado, unidad)
            codigo = articulo[1] if articulo[1] else ''
            marca = articulo[2] if articulo[2] else ''
            nombre = articulo[3]
            stock_formateado = f"{articulo[4]} {articulo[7] if articulo[7] else 'Un.'}"

            # Usamos "latin-1" para evitar errores con caracteres especiales
            pdf.cell(35, 10, codigo.encode('latin-1', 'replace').decode('latin-1'), 1, 0)
            pdf.cell(75, 10, nombre.encode('latin-1', 'replace').decode('latin-1'), 1, 0)
            pdf.cell(30, 10, marca.encode('latin-1', 'replace').decode('latin-1'), 1, 0)
            pdf.cell(30, 10, stock_formateado, 1, 1, 'R')

        pdf.output(path)
        return True, "Reporte de Artículos generado exitosamente."
    except Exception as e:
        return False, f"Error al generar el reporte: {e}"

def generar_listado_reposicion(path):
    """Crea un PDF con la lista de artículos con stock bajo."""
    try:
        pdf = ReportPDF('P', 'mm', 'A4')
        pdf.set_title("Listado de Reposición de Stock")
        pdf.alias_nb_pages()
        pdf.add_page()
        
        pdf.set_font('Helvetica', 'B', 10)
        pdf.cell(95, 10, 'Producto a Reponer', 1, 0, 'C')
        pdf.cell(40, 10, 'Stock Actual', 1, 0, 'C')
        pdf.cell(40, 10, 'Stock Mínimo', 1, 1, 'C')

        pdf.set_font('Helvetica', '', 9)
        # Usamos la función que creamos para el dashboard
        articulos = articulos_db.obtener_articulos_stock_bajo()
        for articulo in articulos:
            # articulo = (nombre, stock, stock_minimo)
            nombre = articulo[0]
            stock_actual = str(articulo[1])
            stock_minimo = str(articulo[2])

            pdf.cell(95, 10, nombre.encode('latin-1', 'replace').decode('latin-1'), 1, 0)
            pdf.cell(40, 10, stock_actual, 1, 0, 'C')
            pdf.cell(40, 10, stock_minimo, 1, 1, 'C')
            
        pdf.output(path)
        return True, "Reporte de Reposición generado exitosamente."
    except Exception as e:
        return False, f"Error al generar el reporte: {e}"