"""
Generate branded S2W PDF templates for Quotation and Invoice.
These are blank templates with the S2W branding - data is overlaid separately.
"""
import io
from reportlab.lib.pagesizes import A4
from reportlab.lib.colors import HexColor, black, white
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas
from reportlab.lib.enums import TA_LEFT, TA_RIGHT, TA_CENTER


# S2W Brand Colors
PRIMARY = HexColor("#C1E12F")  # Lime green
CHARCOAL = HexColor("#2D2D2D")
LIGHT_GRAY = HexColor("#F5F5F0")
DOT_COLOR = HexColor("#E8E8D8")
HEADER_BG = HexColor("#EDEDED")
TABLE_HEADER_BG = CHARCOAL
TABLE_HEADER_TEXT = white
BORDER_COLOR = HexColor("#CCCCCC")

PAGE_W, PAGE_H = A4  # 595 x 842 points


def _draw_common_header(c, doc_type="QUOTE"):
    """Draw the S2W branded header common to both Quote and Invoice"""
    # Background watermark circle (S2W)
    c.setFillColor(HexColor("#F0F0E8"))
    c.circle(180, PAGE_H - 120, 130, fill=1, stroke=0)

    # S2W Logo circle
    c.setFillColor(CHARCOAL)
    c.circle(95, PAGE_H - 75, 40, fill=1, stroke=0)
    # S2W text in circle
    c.setFillColor(white)
    c.setFont("Helvetica-Bold", 16)
    c.drawCentredString(95, PAGE_H - 70, "S2W")

    # Brand name
    c.setFillColor(CHARCOAL)
    c.setFont("Helvetica-Bold", 26)
    c.drawString(145, PAGE_H - 65, "slim")
    c.setFillColor(PRIMARY)
    c.setFont("Helvetica-Bold", 32)
    c.drawString(195, PAGE_H - 65, "2")
    c.setFillColor(CHARCOAL)
    c.setFont("Helvetica-Bold", 26)
    c.drawString(215, PAGE_H - 65, "well")

    # Tagline
    c.setFont("Helvetica", 7)
    c.setFillColor(HexColor("#666666"))
    c.drawString(145, PAGE_H - 80, "W E L L N E S S   S I M P L I F I E D")

    # Document Type (QUOTE / INVOICE)
    c.setFillColor(CHARCOAL)
    c.setFont("Helvetica-Bold", 28)
    c.drawString(390, PAGE_H - 60, doc_type)

    # Reference fields
    c.setFont("Helvetica", 9)
    c.setFillColor(HexColor("#666666"))
    label = "Quote no:" if doc_type == "QUOTE" else "Invoice no:"
    c.drawString(390, PAGE_H - 80, label)
    c.drawString(390, PAGE_H - 95, "Date:")

    # Placeholder positions (for overlay)
    # doc_number: x=460, y=PAGE_H-80
    # date: x=420, y=PAGE_H-95

    # Gray info bar
    c.setFillColor(HEADER_BG)
    c.rect(40, PAGE_H - 165, PAGE_W - 80, 50, fill=1, stroke=0)

    # Patient Name / Address labels
    c.setFillColor(CHARCOAL)
    c.setFont("Helvetica-Bold", 10)
    c.drawString(50, PAGE_H - 140, "Patient Name:")
    c.setFont("Helvetica-Bold", 10)
    c.drawString(50, PAGE_H - 155, "Address:")


def _draw_table_header(c):
    """Draw the table header row"""
    y = PAGE_H - 190
    # Black header bar
    c.setFillColor(TABLE_HEADER_BG)
    c.rect(40, y, PAGE_W - 80, 25, fill=1, stroke=0)

    # Green accent dots on header
    c.setFillColor(PRIMARY)
    for x_pos in [305, 385, 475]:
        c.circle(x_pos, y + 12, 4, fill=1, stroke=0)

    # Column headers
    c.setFillColor(TABLE_HEADER_TEXT)
    c.setFont("Helvetica-Bold", 9)
    c.drawString(50, y + 8, "Description")
    c.drawString(290, y + 8, "Qty")
    c.drawString(370, y + 8, "Unit Price")
    c.drawString(470, y + 8, "Amount")


def _draw_dot_pattern(c):
    """Draw the subtle dot watermark pattern"""
    c.setFillColor(DOT_COLOR)
    for row in range(8):
        for col in range(6):
            x = 80 + col * 90
            y = PAGE_H - 250 - row * 55
            if y > 180:  # Don't draw over footer
                c.circle(x, y, 8, fill=1, stroke=0)


def _draw_footer(c):
    """Draw the banking details footer"""
    footer_y = 130

    # Top border line
    c.setStrokeColor(BORDER_COLOR)
    c.setLineWidth(0.5)
    c.line(40, footer_y + 40, PAGE_W - 40, footer_y + 40)

    # Banking Details header
    c.setFillColor(CHARCOAL)
    c.setFont("Helvetica-Bold", 11)
    c.drawString(50, footer_y + 20, "Banking Details:")

    # Separator line
    c.line(40, footer_y + 12, PAGE_W - 40, footer_y + 12)

    # Banking info
    c.setFont("Helvetica", 9)
    c.setFillColor(CHARCOAL)
    bank_lines = [
        "Slim2Well Pty Ltd",
        "Standard Bank",
        "Code 052650",
        "Account 032988265"
    ]
    for i, line in enumerate(bank_lines):
        c.drawString(50, footer_y - 5 - (i * 14), line)

    # Website and email on right
    c.setFont("Helvetica", 9)
    c.drawRightString(PAGE_W - 50, footer_y - 5, "www.slim2well.com")
    c.drawRightString(PAGE_W - 50, footer_y - 19, "social@slim2well.com")

    # Green accent bar at very bottom
    c.setFillColor(PRIMARY)
    c.rect(PAGE_W - 200, 30, 160, 5, fill=1, stroke=0)


def generate_quote_template():
    """Generate blank branded quotation PDF template"""
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)

    _draw_dot_pattern(c)
    _draw_common_header(c, "QUOTE")
    _draw_table_header(c)
    _draw_footer(c)

    c.save()
    buffer.seek(0)
    return buffer.read()


def generate_invoice_template():
    """Generate blank branded invoice PDF template"""
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)

    _draw_dot_pattern(c)
    _draw_common_header(c, "INVOICE")
    _draw_table_header(c)
    _draw_footer(c)

    c.save()
    buffer.seek(0)
    return buffer.read()


def generate_branded_quotation_pdf(quotation_name):
    """Generate a complete branded quotation PDF with data overlay"""
    import frappe

    qt = frappe.get_doc("Quotation", quotation_name)

    # Get patient info
    customer_name = qt.party_name or qt.customer_name or ""
    patient_address = ""
    if qt.customer_address:
        addr = frappe.get_doc("Address", qt.customer_address)
        patient_address = f"{addr.address_line1 or ''}, {addr.city or ''} {addr.pincode or ''}"
    elif qt.party_name:
        # Try to get from patient's linked address
        patient = frappe.db.get_value("Patient", {"customer": qt.party_name}, "name")
        if patient:
            addr_link = frappe.db.get_value("Dynamic Link",
                {"link_doctype": "Patient", "link_name": patient, "parenttype": "Address"}, "parent")
            if addr_link:
                addr = frappe.get_doc("Address", addr_link)
                patient_address = f"{addr.address_line1 or ''}, {addr.city or ''} {addr.pincode or ''}"

    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)

    # Draw template elements
    _draw_dot_pattern(c)
    _draw_common_header(c, "QUOTE")
    _draw_table_header(c)
    _draw_footer(c)

    # Overlay data
    c.setFillColor(CHARCOAL)

    # Quote number and date
    c.setFont("Helvetica-Bold", 9)
    c.drawString(460, PAGE_H - 80, qt.name)
    c.drawString(420, PAGE_H - 95, frappe.utils.formatdate(qt.transaction_date, "dd-MM-yyyy"))

    # Patient name and address
    c.setFont("Helvetica", 10)
    c.drawString(155, PAGE_H - 140, customer_name)
    c.setFont("Helvetica", 9)
    c.drawString(105, PAGE_H - 155, patient_address[:60])

    # Line items
    y = PAGE_H - 220
    c.setFont("Helvetica", 9)
    for item in qt.items:
        desc = item.description or item.item_name or item.item_code
        if len(desc) > 40:
            desc = desc[:40] + "..."
        c.drawString(50, y, desc)
        c.drawString(300, y, str(int(item.qty)))
        c.drawRightString(440, y, f"R {item.rate:,.2f}")
        c.drawRightString(540, y, f"R {item.amount:,.2f}")
        y -= 20

    # Total section
    y -= 20
    c.setStrokeColor(BORDER_COLOR)
    c.line(350, y + 10, 555, y + 10)

    c.setFont("Helvetica-Bold", 11)
    c.drawString(350, y - 5, "Total:")
    c.drawRightString(540, y - 5, f"R {qt.grand_total:,.2f}")

    c.save()
    buffer.seek(0)
    return buffer.read()


def generate_branded_invoice_pdf(invoice_name):
    """Generate a complete branded invoice PDF with data overlay"""
    import frappe

    inv = frappe.get_doc("Sales Invoice", invoice_name)

    customer_name = inv.customer_name or inv.customer or ""
    patient_address = ""
    if inv.customer_address:
        try:
            addr = frappe.get_doc("Address", inv.customer_address)
            patient_address = f"{addr.address_line1 or ''}, {addr.city or ''} {addr.pincode or ''}"
        except Exception:
            pass

    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)

    _draw_dot_pattern(c)
    _draw_common_header(c, "INVOICE")
    _draw_table_header(c)
    _draw_footer(c)

    # Overlay data
    c.setFillColor(CHARCOAL)

    # Invoice number and date
    c.setFont("Helvetica-Bold", 9)
    c.drawString(460, PAGE_H - 80, inv.name)
    c.drawString(420, PAGE_H - 95, frappe.utils.formatdate(inv.posting_date, "dd-MM-yyyy"))

    # Patient name and address
    c.setFont("Helvetica", 10)
    c.drawString(155, PAGE_H - 140, customer_name)
    c.setFont("Helvetica", 9)
    c.drawString(105, PAGE_H - 155, patient_address[:60])

    # Line items
    y = PAGE_H - 220
    c.setFont("Helvetica", 9)
    for item in inv.items:
        desc = item.description or item.item_name or item.item_code
        if len(desc) > 40:
            desc = desc[:40] + "..."
        c.drawString(50, y, desc)
        c.drawString(300, y, str(int(item.qty)))
        c.drawRightString(440, y, f"R {item.rate:,.2f}")
        c.drawRightString(540, y, f"R {item.amount:,.2f}")
        y -= 20

    # Total
    y -= 20
    c.setStrokeColor(BORDER_COLOR)
    c.line(350, y + 10, 555, y + 10)

    c.setFont("Helvetica-Bold", 11)
    c.drawString(350, y - 5, "Grand Total:")
    c.drawRightString(540, y - 5, f"R {inv.grand_total:,.2f}")

    if inv.outstanding_amount and inv.outstanding_amount > 0:
        c.setFont("Helvetica-Bold", 10)
        c.setFillColor(HexColor("#CC0000"))
        c.drawString(350, y - 25, "Amount Due:")
        c.drawRightString(540, y - 25, f"R {inv.outstanding_amount:,.2f}")

    c.save()
    buffer.seek(0)
    return buffer.read()
