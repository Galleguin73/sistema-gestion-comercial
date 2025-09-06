# Archivo: app/gui/mixins/pricing_mixin.py
import tkinter as tk
from tkinter import TclError
from .locale_validation_mixin import LocaleValidationMixin

class PricingLogicMixin:
    """
    Mixin con la lógica de cálculo de precios, compatible con el formato localizado.
    """
    def bind_pricing_events(self):
        self.costo_entry.bind("<FocusOut>", self._calcular_desde_costo_utilidad, add='+')
        self.iva_combo.bind("<<ComboboxSelected>>", self._calcular_desde_costo_utilidad)
        self.utilidad_entry.bind("<FocusOut>", self._calcular_desde_costo_utilidad, add='+')
        self.venta_entry.bind("<FocusOut>", self._calcular_desde_venta, add='+')

    def _calcular_desde_costo_utilidad(self, event=None):
        try:
            costo = LocaleValidationMixin._parse_local_number(self.costo_entry.get()) or 0.0
            iva_porc = float(self.iva_combo.get() or "0")
            util_porc = LocaleValidationMixin._parse_local_number(self.utilidad_entry.get()) or 0.0
            
            costo_con_iva = costo * (1 + iva_porc / 100)
            precio_venta = costo_con_iva * (1 + util_porc / 100)
            
            self.venta_entry.delete(0, tk.END)
            self.venta_entry.insert(0, LocaleValidationMixin._format_local_number(precio_venta))
        except (ValueError, TclError):
            # Evita errores mientras el usuario escribe
            pass

    def _calcular_desde_venta(self, event=None):
        if hasattr(self, '_format_on_focus_out'):
            self._format_on_focus_out(event)
        try:
            costo = LocaleValidationMixin._parse_local_number(self.costo_entry.get()) or 0.0
            iva_porc = float(self.iva_combo.get() or "0")
            precio_venta = LocaleValidationMixin._parse_local_number(self.venta_entry.get()) or 0.0
            costo_con_iva = costo * (1 + iva_porc / 100)
            
            if costo_con_iva > 0:
                utilidad = ((precio_venta / costo_con_iva) - 1) * 100
                self.utilidad_entry.delete(0, tk.END)
                self.utilidad_entry.insert(0, LocaleValidationMixin._format_local_number(utilidad))
        except (ValueError, TclError):
            # Evita errores mientras el usuario escribe
            pass