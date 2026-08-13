import io
import csv
from flask import send_file
import xlsxwriter
from reportlab.lib.pagesizes import letter, landscape
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from datetime import datetime

def generate_csv_response(filename, headers, rows):
    """Generates a CSV file response streaming from memory."""
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(headers)
    for row in rows:
        formatted_row = ["" if val is None else str(val) for val in row]
        writer.writerow(formatted_row)
    
    output.seek(0)
    bytes_io = io.BytesIO(output.getvalue().encode('utf-8'))
    return send_file(
        bytes_io,
        mimetype="text/csv",
        as_attachment=True,
        download_name=filename
    )

def generate_excel_response(filename, title, headers, rows):
    """Generates an Excel workbook response using xlsxwriter."""
    output = io.BytesIO()
    workbook = xlsxwriter.Workbook(output)
    worksheet = workbook.add_worksheet("Report")
    
    title_format = workbook.add_format({
        'bold': True,
        'size': 14,
        'font_color': '#0284c7',
        'align': 'center',
        'valign': 'vcenter'
    })
    header_format = workbook.add_format({
        'bold': True,
        'bg_color': '#0f172a',
        'font_color': '#ffffff',
        'border': 1,
        'align': 'left',
        'font_size': 10
    })
    cell_format = workbook.add_format({
        'border': 1,
        'align': 'left',
        'font_size': 9
    })
    
    worksheet.merge_range(0, 0, 0, len(headers) - 1, title, title_format)
    worksheet.set_row(0, 30)
    
    for col_num, header in enumerate(headers):
        worksheet.write(2, col_num, header, header_format)
    worksheet.set_row(2, 20)
    
    for row_num, row in enumerate(rows, start=3):
        for col_num, val in enumerate(row):
            val_str = "" if val is None else str(val)
            worksheet.write(row_num, col_num, val_str, cell_format)
            
    for col_num, header in enumerate(headers):
        max_len = len(header)
        for row in rows:
            val_str = "" if row[col_num] is None else str(row[col_num])
            max_len = max(max_len, len(val_str))
        worksheet.set_column(col_num, col_num, max(max_len + 3, 12))
        
    workbook.close()
    output.seek(0)
    return send_file(
        output,
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        as_attachment=True,
        download_name=filename
    )

def generate_pdf_response(filename, title, headers, rows, filters_applied=None):
    """Generates a landscape styled PDF report using reportlab."""
    buffer = io.BytesIO()
    
    doc = SimpleDocTemplate(
        buffer,
        pagesize=landscape(letter),
        leftMargin=36,
        rightMargin=36,
        topMargin=36,
        bottomMargin=36
    )
    
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=16,
        textColor=colors.HexColor('#0284c7'),
        spaceAfter=6
    )
    
    meta_style = ParagraphStyle(
        'DocMeta',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        textColor=colors.HexColor('#64748b'),
        spaceAfter=15
    )
    
    cell_header_style = ParagraphStyle(
        'CellHeader',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=9,
        textColor=colors.white
    )
    
    cell_body_style = ParagraphStyle(
        'CellBody',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8,
        textColor=colors.HexColor('#1e293b')
    )
    
    elements = []
    elements.append(Paragraph(title, title_style))
    
    now_str = datetime.now().strftime("%Y-%m-%d %I:%M %p")
    meta_text = f"Report generated on: {now_str}"
    if filters_applied:
        filter_parts = []
        for k, v in filters_applied.items():
            if v:
                filter_parts.append(f"{k}: {v}")
        if filter_parts:
            meta_text += " | Filters: " + ", ".join(filter_parts)
            
    elements.append(Paragraph(meta_text, meta_style))
    
    table_data = []
    
    header_row = [Paragraph(h, cell_header_style) for h in headers]
    table_data.append(header_row)
    
    for row in rows:
        body_row = []
        for val in row:
            val_str = "" if val is None else str(val)
            body_row.append(Paragraph(val_str, cell_body_style))
        table_data.append(body_row)
        
    num_cols = len(headers)
    col_width = 720.0 / num_cols if num_cols > 0 else 720.0
    
    t = Table(table_data, colWidths=[col_width] * num_cols)
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#0f172a')),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 5),
        ('TOPPADDING', (0,0), (-1,-1), 5),
        ('LEFTPADDING', (0,0), (-1,-1), 5),
        ('RIGHTPADDING', (0,0), (-1,-1), 5),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#cbd5e1')),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor('#f8fafc')])
    ]))
    
    elements.append(t)
    doc.build(elements)
    buffer.seek(0)
    
    return send_file(
        buffer,
        mimetype="application/pdf",
        as_attachment=True,
        download_name=filename
    )
