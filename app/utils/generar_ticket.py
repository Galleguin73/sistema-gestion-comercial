import os
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.units import mm
from datetime import datetime
from app.database import config_db
from PIL import Image

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
TICKETS_DIR = os.path.join(BASE_DIR, 'tickets')

def crear_ticket_venta(venta_id, datos_venta, items_carrito, info_empresa):
    """
    Crea un archivo PDF con el ticket de la venta, con fuentes y layout ajustados.
    """
    os.makedirs(TICKETS_DIR, exist_ok=True)
    filepath = os.path.join(TICKETS_DIR, f"ticket_venta_{venta_id}.pdf")
    
    config = config_db.obtener_configuracion()
    tipo_impresion = config.get("tipo_impresion", "Ticket 80mm")
    logo_path = info_empresa.get("logo_path", None)

    width_mm = 80 if "80mm" in tipo_impresion else 58
    page_width = width_mm * mm
    
    line_height = 10 # Reducimos la altura de línea base
    dynamic_height = (len(items_carrito) * line_height * 1.5) + (100 * mm)
    
    c = canvas.Canvas(filepath, pagesize=(page_width, dynamic_height))
    
    y_position = dynamic_height - (8 * mm)

    if logo_path and os.path.exists(logo_path):
        try:
            with Image.open(logo_path) as img:
                img_width, img_height = img.size
                aspect_ratio = img_height / img_width
                max_width = page_width - (20 * mm)
                draw_width = max_width
                draw_height = max_width * aspect_ratio
                c.drawImage(logo_path, (page_width - draw_width) / 2, y_position - draw_height, 
                            width=draw_width, height=draw_height, mask='auto')
                y_position -= (draw_height + 4 * mm)
        except Exception as e:
            print(f"No se pudo cargar o dibujar el logo: {e}")

    # --- TAMAÑOS DE FUENTE REDUCIDOS ---
    c.setFont("Helvetica-Bold", 10)
    c.drawCentredString(page_width / 2, y_position, info_empresa.get('nombre_fantasia', ''))
    y_position -= line_height

    c.setFont("Helvetica", 7)
    c.drawCentredString(page_width / 2, y_position, info_empresa.get('razon_social', ''))
    y_position -= line_height
    c.drawCentredString(page_width / 2, y_position, f"CUIT: {info_empresa.get('cuit', '')}")
    y_position -= line_height
    c.drawCentredString(page_width / 2, y_position, info_empresa.get('domicilio', ''))
    y_position -= line_height
    c.drawCentredString(page_width / 2, y_position, info_empresa.get('condicion_iva', ''))
    y_position -= line_height * 1.5

    # --- LAYOUT CORREGIDO: Ticket y Fecha en líneas separadas ---
    c.drawString(10, y_position, f"{datos_venta.get('tipo_comprobante', 'TICKET')} N°: {str(venta_id).zfill(8)}")
    y_position -= line_height
    fecha_str = datetime.now().strftime('%d/%m/%Y %H:%M')
    c.drawString(10, y_position, f"Fecha: {fecha_str}")
    y_position -= line_height
    
    cliente_nombre = datos_venta.get('cliente_nombre', 'Consumidor Final')
    c.drawString(10, y_position, f"Cliente: {cliente_nombre}")
    y_position -= line_height
    c.line(10, y_position, page_width - 10, y_position)
    y_position -= line_height

    c.setFont("Helvetica-Bold", 6)
    x_subtotal = page_width - 10
    x_precio_unit = page_width - 45
    x_desc = 30
    x_cant = 10
    
    c.drawString(x_cant, y_position, "Cant.")
    c.drawString(x_desc, y_position, "Descripción")
    c.drawRightString(x_precio_unit, y_position, "P. Unit")
    c.drawRightString(x_subtotal, y_position, "Subtotal")
    y_position -= line_height
    
    c.setFont("Helvetica", 6)
    espacio_desc = x_precio_unit - x_desc - 5
    max_chars_desc = int(espacio_desc / 3.5) # Ajuste para fuente más pequeña

    for item in items_carrito.values():
        desc = item['descripcion']
        cant = item['cantidad']
        precio = item['precio_unit']
        subtotal = cant * precio - item.get('descuento', 0.0)

        c.drawString(x_cant, y_position, str(cant))
        c.drawString(x_desc, y_position, desc[:max_chars_desc])
        c.drawRightString(x_precio_unit, y_position, f"${precio:,.2f}")
        c.drawRightString(x_subtotal, y_position, f"${subtotal:,.2f}")
        y_position -= line_height

    y_position -= line_height / 2
    c.line(10, y_position, page_width - 10, y_position)
    y_position -= line_height
    
    c.setFont("Helvetica-Bold", 9)
    c.drawRightString(page_width - 10, y_position, f"TOTAL: ${datos_venta.get('total', 0.0):,.2f}")
    y_position -= line_height * 2
    
    c.setFont("Helvetica", 7)
    c.drawCentredString(page_width / 2, y_position, "¡Gracias por su compra!")
    
    c.save()
    return filepath