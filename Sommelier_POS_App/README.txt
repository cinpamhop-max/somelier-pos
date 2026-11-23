SOMMELIER POS — PRIMERA VERSION
================================
Incluye mesas (12 iniciales), pedidos desde celulares, comandas para cocina,
caja/cierre de cuentas, registro del medio de pago, menú y resumen de ventas.

INSTALACION EN WINDOWS
1. Instalar Python 3.10 o superior desde python.org. Marcar "Add Python to PATH".
2. Descomprimir esta carpeta en la computadora que estará en caja.
3. Hacer doble clic en INSTALAR_Y_ABRIR.bat.
4. En la computadora abrir http://127.0.0.1:5000
5. Para conectar celulares, todos deben estar en el mismo Wi-Fi.
   En la PC abrir CMD, escribir ipconfig y buscar Dirección IPv4.
   En los celulares abrir http://IP-DE-LA-PC:5000 (ej. http://192.168.1.20:5000).

USUARIOS Y PIN INICIALES
Mozo: mozo / 1111
Caja: caja / 2468
Administrador: admin / 1234
Cocina: cocina / 2222

IMPORTANTE
Es una primera versión funcional para probar la operatoria interna. Cambiá los PIN
antes de usarla con personal y clientes. Si Windows pregunta por Firewall, permitir
Python en redes privadas. Mantener la PC encendida mientras se usa desde celulares.

No emite facturas fiscales ni reemplaza la integración con ARCA/controlador fiscal.
No procesa pagos: registra el medio elegido. "Mixto" queda como etiqueta, todavía
no permite cargar importes separados. Aún no incluye impresora de comandas, división
de cuenta, stock ni registro detallado de anulaciones. Hacer copia de sommelier.db.
No exponer este servidor directamente a Internet.


USAR COMO APP EN LOS CELULARES
- Abrí Chrome en el celular conectado al mismo Wi-Fi que la computadora.
- Escribí http://IP-DE-LA-PC:5000
- En el menú de Chrome elegí "Agregar a pantalla principal" o "Instalar aplicación"
  (la opción puede variar según el teléfono/navegador).
- Se crea un acceso directo con aspecto de aplicación. La computadora debe quedar
  encendida y el celular conectado al Wi-Fi del restaurante para operar.
