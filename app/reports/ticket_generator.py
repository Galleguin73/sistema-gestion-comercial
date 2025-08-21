from fpdf import FPDF
from app.database import config_db, ventas_db
from datetime import datetime
import os

class TicketPDF(FPDF):
    # --- CORRECCIÓN: Todo el código de la clase debe estar indentado ---
    def __init__(self, orientation='P', unit='mm', format=(58, 297), empresa_info=None):
        super().__init__(orientation, unit, format)
        self.empresa_info = empresa_info or {}
        try:
            self.add_font('DejaVu', '', 'DejaVuSans.ttf', uni=True)
            self.add_font('DejaVu', 'B', 'DejaVuSans-Bold.ttf', uni=True)
            self.font_family = 'DejaVu'
        except RuntimeError:
            print("ADVERTENCIA: Fuente DejaVuSans no encontrada. Usando Arial.")
            self.font_family = 'Arial'
        self.set_auto_page_break(True, margin=5)

    def print_header(self, venta_encabezado):
        logo_path = self.empresa_info.get("logo_path")
        if logo_path and os.path.exists(logo_path):
            try:
                self.image(logo_path, x=14, y=8, w=30)
                self.ln(20)
            except Exception as e:
                print(f"Error al cargar logo en PDF: {e}")

        self.set_font(self.font_family, 'B', 9)
        if self.empresa_info.get('nombre_fantasia'): self.multi_cell(0, 4, self.empresa_info['nombre_fantasia'], 0, 'C')
        self.set_font(self.font_family, '', 7)
        if self.empresa_info.get('razon_social'): self.cell(0, 4, self.empresa_info['razon_social'], 0, 1, 'C')
        if self.empresa_info.get('domicilio'): self.cell(0, 4, self.empresa_info['domicilio'], 0, 1, 'C')
        if self.empresa_info.get('cuit'): self.cell(0, 4, f"CUIT: {self.empresa_info['cuit']}", 0, 1, 'C')
        self.ln(3)

        self.set_font(self.font_family, 'B', 8)
        self.cell(0, 5, f"{venta_encabezado.get('tipo_comprobante', '').upper()} N°: {venta_encabezado['id']:08d}", 0, 1, 'L')
        self.set_font(self.font_family, '', 7)
        fecha_str = venta_encabezado.get('fecha')
        if fecha_str:
            fecha = datetime.fromisoformat(fecha_str).strftime('%d/%m/%Y %H:%M')
            self.cell(0, 5, f"Fecha: {fecha}", 0, 1, 'L')
        self.cell(0, 5, f"Cliente: {venta_encabezado.get('cliente_nombre', 'Consumidor Final')}", 0, 1, 'L')
        if venta_encabezado.get('cliente_cuit'):
            self.cell(0, 5, f"CUIT/DNI: {venta_encabezado['cliente_cuit']}", 0, 1, 'L')
        self.ln(2)

    def print_items(self, detalles):
        self.set_font(self.font_family, 'B', 7)
        self.line(self.get_x(), self.get_y(), self.get_x() + 48, self.get_y()); self.ln(1)
        self.cell(8, 5, 'Cant.', 0, 0, 'C'); self.cell(26, 5, 'Descripción', 0, 0, 'L'); self.cell(14, 5, 'Subtotal', 0, 1, 'R')
        self.line(self.get_x(), self.get_y(), self.get_x() + 48, self.get_y()); self.ln(1)
        
        self.set_font(self.font_family, '', 7)
        for item in detalles:
            desc, cant, pu, sub, marca = item
            desc_completa = f"{marca} - {desc}" if marca else desc
            self.cell(8, 4, f"{cant:.2f}", 0, 0, 'C')
            x, y = self.get_x(), self.get_y()
            self.multi_cell(26, 4, desc_completa, 0, 'L')
            line_height = self.get_y() - y
            self.set_xy(x + 26, y)
            self.cell(14, line_height, f"${sub:.2f}", 0, 1, 'R')

    def print_totals(self, venta_encabezado):
        self.line(self.get_x(), self.get_y(), self.get_x() + 48, self.get_y()); self.ln(2)
        self.set_font(self.font_family, 'B', 10)
        self.cell(0, 8, f"TOTAL: $ {venta_encabezado.get('total', 0.0):.2f}", 0, 1, 'R')
    
    def footer(self):
        self.set_y(-15); self.set_font(self.font_family, 'I', 8); self.cell(0, 10, '¡Gracias por su compra!', 0, 0, 'C')

def crear_comprobante_venta(venta_id):
    try:
        info_empresa = config_db.obtener_configuracion()
        venta_encabezado = ventas_db.obtener_venta_completa_por_id(venta_id)
        venta_detalles = ventas_db.obtener_detalle_venta_completo(venta_id)
        
        if not venta_encabezado: return None, "No se encontró la venta."
        
        pdf = TicketPDF(format=(58, 297), empresa_info=info_empresa)
        pdf.set_margins(5, 5, 5); pdf.add_page()
        
        pdf.print_header(venta_encabezado)
        pdf.print_items(venta_detalles)
        pdf.print_totals(venta_encabezado)
        
        temp_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'temp')
        if not os.path.exists(temp_dir): os.makedirs(temp_dir)
        
        filepath = os.path.join(temp_dir, f"venta_{venta_id}.pdf")
        pdf.output(filepath)
        
        return filepath, "Comprobante generado."
    except Exception as e:
        return None, f"Error al crear el comprobante: {e}"