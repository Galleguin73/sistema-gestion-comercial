# import pyafipws
import os
from app.database import config_db

TA = None

def autenticar():
    """Se conecta a la WSAA para obtener el Token de Acceso."""
    global TA
    
    config = config_db.obtener_configuracion()
    if not config:
        raise ConnectionError("No se pudo obtener la configuración de la empresa.")

    cert_path = config.get("afip_cert_path")
    pkey_path = config.get("afip_pkey_path")
    cuit = config.get("cuit")

    if not all([cert_path, pkey_path, cuit]):
        raise ConnectionError("Faltan configurar el CUIT, Certificado o Clave Privada de AFIP.")

    if not os.path.exists(cert_path) or not os.path.exists(pkey_path):
        raise FileNotFoundError("No se encontraron los archivos de certificado o clave privada en las rutas especificadas.")

    if TA is None or TA.is_expired():
        print("Autenticando con AFIP...")
        # --- CAMBIO: Se accede a la clase a través del paquete principal ---
        wsaa = pyafipws.WSAA()
        TA = wsaa.Autenticar("wsfe", cert_path, pkey_path, "homo")
    
    return TA, cuit

def solicitar_cae_factura(datos_factura):
    """Envía los datos de una factura a la AFIP para obtener el CAE."""
    try:
        token_acceso, cuit_empresa = autenticar()
        wsfev1 = pyafipws.WSFEV1()
        wsfev1.Conectar(TA=token_acceso)
        wsfev1.Cuit = cuit_empresa
        
        punto_venta = 1
        tipo_cbte = 6    # Factura B
        concepto = 1     # Productos
        importe_total = datos_factura['total']

        # --- CAMBIO: Lógica para manejar Consumidor Final ---
        cliente_cuit = datos_factura.get('cliente_cuit')
        
        if not cliente_cuit:
            # Si no hay CUIT, es un Consumidor Final.
            tipo_doc = 99  # Sin identificar / Varios
            nro_doc = 0    # AFIP espera 0 para consumidor final
        else:
            # Si hay CUIT, usamos el tipo de documento correspondiente.
            tipo_doc = 80  # CUIT
            nro_doc = cliente_cuit
        # --- FIN DEL CAMBIO ---

        ultimo_autorizado = wsfev1.CompUltimoAutorizado(pto_vta=punto_venta, tipo_cbte=tipo_cbte)
        proximo_a_autorizar = ultimo_autorizado + 1
        
        wsfev1.CrearFactura(
            concepto=concepto, tipo_doc=tipo_doc, nro_doc=nro_doc,
            tipo_cbte=tipo_cbte, pto_vta=punto_venta,
            cbte_nro=proximo_a_autorizar,
            imp_total=importe_total
        )
        
        wsfev1.CAESolicitar()

        if wsfev1.Resultado == "A":
            return {
                "cae": wsfev1.CAE,
                "vencimiento": wsfev1.Vencimiento,
                "numero_factura": proximo_a_autorizar,
                "error": None
            }
        else:
            errores = wsfev1.Observaciones + " " + wsfev1.Errores
            return {"cae": None, "error": errores.strip()}

    except Exception as e:
        return {"cae": None, "error": str(e)}