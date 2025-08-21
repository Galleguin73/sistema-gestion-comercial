# Archivo nuevo: app/gui/mixins/pricing_mixin.py
import tkinter as tk
from tkinter import TclError

class PricingLogicMixin:
    """
    Un Mixin que contiene la lógica de cálculo de precios para ser
    reutilizada en diferentes ventanas de ABM de artículos.
    """
    def bind_pricing_events(self):
        """Conecta los eventos de los widgets de precio a las funciones de cálculo."""
        self.costo_entry.bind("<KeyRelease>", self._calcular_desde_costo_utilidad)
        self.iva_combo.bind("<<ComboboxSelected>>", self._calcular_desde_costo_utilidad)
        self.utilidad_entry.bind("<KeyRelease>", self._calcular_desde_costo_utilidad)
        self.venta_entry.bind("<KeyRelease>", self._calcular_desde_venta)

    def _calcular_desde_costo_utilidad(self, event=None):
        try:
            costo_str = self.costo_entry.get().replace(',', '.') or "0"
            iva_str = self.iva_combo.get() or "0"
            util_str = self.utilidad_entry.get().replace(',', '.') or "0"
            costo = float(costo_str)
            iva_porc = float(iva_str)
            util_porc = float(util_str)
            costo_con_iva = costo * (1 + iva_porc / 100)
            precio_venta = costo_con_iva * (1 + util_porc / 100)
            
            # Desvinculamos temporalmente para evitar bucles infinitos
            self.venta_entry.unbind("<KeyRelease>")
            self.venta_entry.delete(0, tk.END)
            self.venta_entry.insert(0, f"{precio_venta:.2f}")
            self.venta_entry.bind("<KeyRelease>", self._calcular_desde_venta)
        except (ValueError, TclError):
            pass

    def _calcular_desde_venta(self, event=None):
        try:
            costo_str = self.costo_entry.get().replace(',', '.') or "0"
            iva_str = self.iva_combo.get() or "0"
            venta_str = self.venta_entry.get().replace(',', '.') or "0"
            costo = float(costo_str)
            iva_porc = float(iva_str)
            precio_venta = float(venta_str)
            costo_con_iva = costo * (1 + iva_porc / 100)
            
            if costo_con_iva > 0:
                utilidad = ((precio_venta / costo_con_iva) - 1) * 100
                # Desvinculamos temporalmente para evitar bucles infinitos
                self.utilidad_entry.unbind("<KeyRelease>")
                self.utilidad_entry.delete(0, tk.END)
                self.utilidad_entry.insert(0, f"{utilidad:.2f}")
                self.utilidad_entry.bind("<KeyRelease>", self._calcular_desde_costo_utilidad)
        except (ValueError, TclError):
            pass