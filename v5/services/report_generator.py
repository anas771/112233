from fpdf import FPDF
import os
from datetime import datetime

class ReportGenerator:
    def __init__(self, output_dir="reports"):
        self.output_dir = output_dir
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

    def generate_batch_report(self, batch_data, daily_records, sales, costs):
        """
        إنشاء تقرير PDF مفصل لدفعة معينة
        """
        pdf = FPDF()
        pdf.add_page()
        
        # إضافة خط يدعم العربية (يجب توفير ملف الخط)
        # pdf.add_font('Amiri', '', 'assets/fonts/Amiri-Regular.ttf', unicode=True)
        # pdf.set_font('Amiri', size=16)
        
        pdf.set_font("Arial", "B", 16)
        pdf.cell(200, 10, txt=f"Batch Report: {batch_data.batch_num}", ln=True, align='C')
        
        pdf.set_font("Arial", size=12)
        pdf.cell(200, 10, txt=f"Warehouse: {batch_data.warehouse.name}", ln=True)
        pdf.cell(200, 10, txt=f"Start Date: {batch_data.date_in.strftime('%Y-%m-%d')}", ln=True)
        pdf.cell(200, 10, txt=f"Initial Chicks: {batch_data.chicks}", ln=True)
        
        pdf.ln(10)
        pdf.set_font("Arial", "B", 14)
        pdf.cell(200, 10, txt="Summary Statistics", ln=True)
        
        # حسابات سريعة
        total_mortality = sum(r.dead_count for r in daily_records)
        mortality_pct = (total_mortality / batch_data.chicks * 100) if batch_data.chicks > 0 else 0
        
        pdf.set_font("Arial", size=12)
        pdf.cell(200, 10, txt=f"Total Mortality: {total_mortality} ({mortality_pct:.2f}%)", ln=True)
        
        # حفظ الملف
        filename = f"report_{batch_data.batch_num}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        filepath = os.path.join(self.output_dir, filename)
        pdf.output(filepath)
        return filepath
