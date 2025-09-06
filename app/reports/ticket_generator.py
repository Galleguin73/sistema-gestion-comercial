# Archivo: app/reports/ticket_generator.py (Reescrito con FPDF2)

import os
from datetime import datetime
from fpdf import FPDF
from app.database import ventas_db, config_db

# --- CONFIGURACIÓN DEL TICKET ---
TICKET_WIDTH = 80  # Ancho del ticket en mm (80mm es un estándar para impresoras térmicas)
FONT_DEJAVU_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'DejaVuSans.ttf')

class TicketPDF(FPDF):
    """Clase personalizada para generar el ticket con encabezado y pie de página si fuera necesario."""
    def header(self):
        # Esta función se puede usar para añadir un logo o encabezado en cada página
        pass

    def footer(self):
        # Esta función se puede usar para añadir un pie de página
        self.set_y(-15)
        self.set_font('DejaVu', '', 8)
        self.cell(0, 10, '¡Gracias por su compra!', align='C')

def crear_comprobante_venta(venta_id):
    try:
        # --- 1. OBTENER DATOS DE LA BASE DE DATOS ---
        venta = ventas_db.obtener_venta_completa_por_id(venta_id)
        detalles = ventas_db.obtener_detalle_venta_completo(venta_id)
        config = config_db.obtener_configuracion()

        if not venta or not config:
            return None, "No se encontraron datos de la venta o configuración."

        # --- 2. CONFIGURAR EL DOCUMENTO PDF ---
        pdf = TicketPDF(orientation='P', unit='mm', format=(TICKET_WIDTH, 297)) # Ancho fijo, alto variable
        pdf.add_page()
        
        # Agregamos la fuente DejaVu que soporta caracteres especiales como € y acentos
        try:
            pdf.add_font('DejaVu', '', FONT_DEJAVU_PATH, uni=True)
            pdf.add_font('DejaVu', 'B', FONT_DEJAVU_PATH, uni=True) # Versión en negrita
        except RuntimeError:
            print("Advertencia: No se encontró la fuente DejaVuSans.ttf. Usando Arial.")
            pdf.add_font('DejaVu', '', 'Arial', uni=True)
            pdf.add_font('DejaVu', 'B', 'Arial', uni=True)


        pdf.set_auto_page_break(True, margin=10)
        pdf.set_margins(5, 5, 5)

        # --- 3. DIBUJAR EL CONTENIDO DEL TICKET ---
        
        # Encabezado de la empresa
        pdf.set_font('DejaVu', 'B', 10)
        pdf.cell(0, 5, config.get("nombre_fantasia", "Mi Comercio"), ln=True, align='C')
        pdf.set_font('DejaVu', '', 8)
        pdf.cell(0, 4, f"Razón Social: {config.get('razon_social', '')}", ln=True, align='C')
        pdf.cell(0, 4, f"CUIT: {config.get('cuit', '')} - IIBB: {config.get('iibb', '')}", ln=True, align='C')
        pdf.cell(0, 4, f"{config.get('domicilio', '')}", ln=True, align='C')
        pdf.cell(0, 4, f"{config.get('ciudad', '')}, {config.get('provincia', '')}", ln=True, align='C')
        pdf.ln(5)

        # Línea divisoria
        pdf.line(pdf.get_x(), pdf.get_y(), pdf.get_x() + TICKET_WIDTH - 10, pdf.get_y())
        pdf.ln(2)

        # Datos del comprobante
        pdf.set_font('DejaVu', 'B', 9)
        pdf.cell(0, 5, f"COMPROBANTE NO VÁLIDO COMO FACTURA", ln=True, align='C')
        pdf.set_font('DejaVu', '', 8)
        fecha_dt = datetime.fromisoformat(venta['fecha_venta'].split('.')[0])
        pdf.cell(0, 5, f"Fecha: {fecha_dt.strftime('%d/%m/%Y %H:%M')}", ln=True)
        pdf.cell(0, 5, f"Comprobante N°: {venta['id']:08d}", ln=True)
        pdf.cell(0, 5, f"Cliente: {venta.get('cliente_nombre', 'Consumidor Final')}", ln=True)
        pdf.ln(3)

        # Encabezados de la tabla de artículos
        pdf.set_font('DejaVu', 'B', 7)
        pdf.cell(10, 5, 'Cant.', border=0, align='C')
        pdf.cell(35, 5, 'Descripción', border=0)
        pdf.cell(10, 5, 'P.Unit', border=0, align='R')
        pdf.cell(15, 5, 'Subtotal', border=0, align='R', ln=True)
        pdf.line(pdf.get_x(), pdf.get_y(), pdf.get_x() + TICKET_WIDTH - 10, pdf.get_y())
        pdf.ln(1)

        # Items de la venta
        pdf.set_font('DejaVu', '', 7)
        subtotal_general = 0
        for item in detalles:
            descripcion, cantidad, precio_unit, subtotal, marca = item
            subtotal_general += subtotal

            # Guardamos la posición actual para manejar el texto multi-línea
            start_x = pdf.get_x()
            start_y = pdf.get_y()
            
            # Cantidad (columna 1)
            pdf.multi_cell(10, 4, str(cantidad), align='C')

            # Descripción (columna 2)
            pdf.set_xy(start_x + 10, start_y)
            pdf.multi_cell(35, 4, descripcion)
            
            # P. Unit (columna 3)
            pdf.set_xy(start_x + 45, start_y)
            pdf.multi_cell(10, 4, f"{precio_unit:,.2f}", align='R')
            
            # Subtotal (columna 4)
            pdf.set_xy(start_x + 55, start_y)
            pdf.multi_cell(15, 4, f"{subtotal:,.2f}", align='R', ln=1)

        # Totales
        pdf.ln(3)
        pdf.line(pdf.get_x(), pdf.get_y(), pdf.get_x() + TICKET_WIDTH - 10, pdf.get_y())
        pdf.ln(2)
        
        pdf.set_font('DejaVu', 'B', 10)
        pdf.cell(40, 6, 'TOTAL:', border=0)
        pdf.cell(30, 6, f"$ {venta['monto_total']:,.2f}", border=0, ln=True, align='R')

        # Datos fiscales (si existen)
        if venta.get('cae'):
            pdf.ln(5)
            pdf.set_font('DejaVu', '', 8)
            pdf.cell(0, 4, f"CAE: {venta['cae']}", ln=True, align='C')
            pdf.cell(0, 4, f"Vto. CAE: {format_db_date(venta.get('cae_vencimiento'))}", ln=True, align='C')

        # --- 4. GUARDAR EL ARCHIVO PDF ---
        # Creamos el directorio si no existe
        tickets_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'tickets')
        os.makedirs(tickets_dir, exist_ok=True)
        
        filepath = os.path.join(tickets_dir, f"venta_{venta_id}.pdf")
        pdf.output(filepath)

        return filepath, "Comprobante generado exitosamente."

    except Exception as e:
        error_msg = f"Error al generar el ticket: {e}"
        print(error_msg)
        return None, error_msg