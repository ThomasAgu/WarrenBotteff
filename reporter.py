# Este archivo va a estar destinado a imprimir los datos y guardarlos en un forato legible para destues je

# Recibe una operacion.

# Crea una hoja de calculo en la carpeta /reports, o edita una existnte con el formato, "Operaciones_{Fecha}", e imprime
# Fecha | Hora | (COMPRA/VENTA) | Moneda | Cantidad | Valor en USD | Ganancia o Perdida (verde o rojo)

# Ademas vamos a tener una fila final con 
# Fecha | Cantidad Operaciones | Capital Inicial | Capital Final | Diferencial

import os
from datetime import datetime
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

class TradeReporter:
    def __init__(self, reports_dir="reports", capital_inicial=1000.0):
        """
        Inicializa el reportero de operaciones.
        
        :param reports_dir: Carpeta donde se guardarán los archivos .xlsx
        :param capital_inicial: Capital inicial de la cuenta para calcular el resumen
        """
        self.reports_dir = reports_dir
        self.capital_inicial = float(capital_inicial)
        
        # Crear la carpeta /reports si no existe
        if not os.path.exists(self.reports_dir):
            os.makedirs(self.reports_dir)

    def _get_filepath(self, date_str=None):
        """Genera el nombre de archivo con formato Operaciones_{Fecha}.xlsx"""
        if date_str is None:
            date_str = datetime.now().strftime("%Y-%m-%d")
        filename = f"Operaciones_{date_str}.xlsx"
        return os.path.join(self.reports_dir, filename)

    def _apply_styles(self, ws):
        """Aplica estilos visuales profesionales a la hoja de cálculo."""
        COLOR_HEADER_BG = "1F4E78"       # Azul oscuro
        COLOR_HEADER_TEXT = "FFFFFF"     # Blanco
        COLOR_SUMMARY_BG = "D9E1F2"      # Azul claro
        COLOR_ZEBRA = "F9FBFD"           # Gris suave
        
        font_family = "Segoe UI"
        
        header_font = Font(name=font_family, size=11, bold=True, color=COLOR_HEADER_TEXT)
        header_fill = PatternFill(start_color=COLOR_HEADER_BG, end_color=COLOR_HEADER_BG, fill_type="solid")
        
        data_font = Font(name=font_family, size=10)
        
        summary_font = Font(name=font_family, size=11, bold=True)
        summary_fill = PatternFill(start_color=COLOR_SUMMARY_BG, end_color=COLOR_SUMMARY_BG, fill_type="solid")
        
        # Estilos para PnL positivo y negativo
        font_green = Font(name=font_family, size=10, bold=True, color="006100")
        font_red = Font(name=font_family, size=10, bold=True, color="9C0006")
        fill_green = PatternFill(start_color="C6EFCE", end_color="C6EFCE", fill_type="solid")
        fill_red = PatternFill(start_color="FFC7CE", end_color="FFC7CE", fill_type="solid")
        
        thin_border = Border(
            left=Side(style='thin', color='E0E0E0'),
            right=Side(style='thin', color='E0E0E0'),
            top=Side(style='thin', color='E0E0E0'),
            bottom=Side(style='thin', color='E0E0E0')
        )
        
        double_bottom_border = Border(
            top=Side(style='thin', color='1F4E78'),
            bottom=Side(style='double', color='1F4E78')
        )

        # Ubicar dónde termina la tabla de operaciones y dónde empieza el resumen
        max_row = ws.max_row
        summary_header_row = None
        for r in range(1, max_row + 1):
            if ws.cell(row=r, column=2).value == "Cant. Operaciones":
                summary_header_row = r
                break

        ops_end_row = (summary_header_row - 2) if summary_header_row else max_row

        # 1. Aplicar estilos a la Tabla de Operaciones
        for row in ws.iter_rows(min_row=1, max_row=ops_end_row, min_col=1, max_col=7):
            for cell in row:
                if cell.row == 1:
                    cell.font = header_font
                    cell.fill = header_fill
                    cell.alignment = Alignment(horizontal="center", vertical="center")
                else:
                    cell.font = data_font
                    cell.border = thin_border
                    
                    if cell.row % 2 == 0 and cell.column != 7:
                        cell.fill = PatternFill(start_color=COLOR_ZEBRA, end_color=COLOR_ZEBRA, fill_type="solid")
                    
                    if cell.column in [1, 2, 3, 4]:
                        cell.alignment = Alignment(horizontal="center", vertical="center")
                    elif cell.column in [5, 6, 7]:
                        cell.alignment = Alignment(horizontal="right", vertical="center")
                    
                    # Formatos numéricos
                    if cell.column == 5:
                        cell.number_format = '#,##0.000000'
                    elif cell.column == 6:
                        cell.number_format = '"$"#,##0.00'
                    elif cell.column == 7:
                        cell.number_format = '"$"#,##0.00;[Red]("$"#,##0.00);"-"'
                        val = cell.value
                        if isinstance(val, (int, float)):
                            if val > 0:
                                cell.font = font_green
                                cell.fill = fill_green
                            elif val < 0:
                                cell.font = font_red
                                cell.fill = fill_red

        # 2. Aplicar estilos a la Fila / Tabla de Resumen Final
        if summary_header_row:
            # Encabezados de resumen
            for col in range(1, 6):
                c = ws.cell(row=summary_header_row, column=col)
                c.font = Font(name=font_family, size=10, bold=True, color="1F4E78")
                c.fill = PatternFill(start_color="E9EEF4", end_color="E9EEF4", fill_type="solid")
                c.alignment = Alignment(horizontal="center", vertical="center")
                c.border = Border(top=Side(style='medium', color='1F4E78'), bottom=Side(style='thin', color='1F4E78'))

            # Valores del resumen
            val_row = summary_header_row + 1
            for col in range(1, 6):
                c = ws.cell(row=val_row, column=col)
                c.font = summary_font
                c.fill = summary_fill
                c.border = double_bottom_border
                c.alignment = Alignment(horizontal="center" if col in [1, 2] else "right", vertical="center")
                
                if col == 2:
                    c.number_format = '#,##0'
                elif col in [3, 4]:
                    c.number_format = '"$"#,##0.00'
                elif col == 5:
                    c.number_format = '"$"#,##0.00;[Red]("$"#,##0.00);"-"'
                    val = c.value
                    if isinstance(val, (int, float)):
                        if val > 0:
                            c.font = Font(name=font_family, size=11, bold=True, color="006100")
                        elif val < 0:
                            c.font = Font(name=font_family, size=11, bold=True, color="9C0006")

        # Ajustar ancho de columnas automáticamente según contenido
        for col in ws.columns:
            max_len = 0
            col_letter = get_column_letter(col[0].column)
            for cell in col:
                val_str = str(cell.value or '')
                if len(val_str) > max_len:
                    max_len = len(val_str)
            ws.column_dimensions[col_letter].width = max(max_len + 4, 15)

    def log_trade(self, tipo, moneda, cantidad, valor_usd, pnl=0.0, timestamp=None):
        """
        Registra o actualiza una operación en el archivo diario de Excel.
        """
        if timestamp is None:
            dt = datetime.now()
        elif isinstance(timestamp, str):
            dt = datetime.fromisoformat(timestamp)
        else:
            dt = timestamp

        fecha_str = dt.strftime("%Y-%m-%d")
        hora_str = dt.strftime("%H:%M:%S")
        filepath = self._get_filepath(fecha_str)

        trades = []
        
        # Si el archivo ya existe, leer operaciones previas
        if os.path.exists(filepath):
            wb_old = openpyxl.load_workbook(filepath, data_only=True)
            ws_old = wb_old.active
            
            for r in range(2, ws_old.max_row + 1):
                f_val = ws_old.cell(row=r, column=1).value
                if ws_old.cell(row=r, column=2).value == "Cant. Operaciones":
                    break
                if f_val is not None:
                    trades.append([
                        str(ws_old.cell(row=r, column=1).value),
                        str(ws_old.cell(row=r, column=2).value),
                        str(ws_old.cell(row=r, column=3).value),
                        str(ws_old.cell(row=r, column=4).value),
                        float(ws_old.cell(row=r, column=5).value or 0),
                        float(ws_old.cell(row=r, column=6).value or 0),
                        float(ws_old.cell(row=r, column=7).value or 0)
                    ])
            wb_old.close()

        # Agregar la nueva operación
        nueva_operacion = [
            fecha_str,
            hora_str,
            tipo.upper(),
            moneda.upper(),
            float(cantidad),
            float(valor_usd),
            float(pnl)
        ]
        trades.append(nueva_operacion)

        # Crear nuevo libro con estructura limpia
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Reporte Diario"
        ws.views.sheetView[0].showGridLines = True

        # 1. Agregar Operaciones
        headers_ops = ["Fecha", "Hora", "Tipo", "Moneda", "Cantidad", "Valor en USD", "Ganancia / Pérdida"]
        ws.append(headers_ops)
        for t in trades:
            ws.append(t)

        # Espacio en blanco
        ws.append([])

        # 2. Agregar Resumen Final
        headers_summary = ["Fecha", "Cant. Operaciones", "Capital Inicial", "Capital Final", "Diferencial"]
        ws.append(headers_summary)

        cant_operaciones = len(trades)
        pnl_acumulado = sum(t[6] for t in trades)
        capital_final = self.capital_inicial + pnl_acumulado

        summary_row = [
            fecha_str,
            cant_operaciones,
            self.capital_inicial,
            capital_final,
            pnl_acumulado
        ]
        ws.append(summary_row)

        # Aplicar formato visual
        self._apply_styles(ws)

        # Guardar en la carpeta /reports
        wb.save(filepath)
        print(f"📊 [Reporter] Operación guardada en '{filepath}'")