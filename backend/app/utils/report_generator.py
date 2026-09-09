import os
from fpdf import FPDF

class ReportGenerator:
    def __init__(self):
        pass
        
    def generate_clinical_report(self, *args, **kwargs):
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Helvetica", size=12)
        pdf.cell(200, 10, txt="OcuPulse Clinical Report", ln=1, align='C')
        
        os.makedirs("reports", exist_ok=True)
        report_path = f"reports/report_generated.pdf"
        pdf.output(report_path)
        return report_path
