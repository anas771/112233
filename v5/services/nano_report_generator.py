import os
from datetime import datetime
import io
import matplotlib.pyplot as plt
from fpdf import FPDF
import arabic_reshaper
from bidi.algorithm import get_display

class NanoReportGenerator:
    def __init__(self, output_dir="reports", assets_dir=None):
        self.output_dir = output_dir
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
            
        # تحديد مسار الأصول (الخطوط والهيدر)
        if not assets_dir:
            # افتراض المسار النسبي من v5/services
            self.assets_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "assets")
        else:
            self.assets_dir = assets_dir
            
        self.font_path = os.path.join(self.assets_dir, "Amiri-Regular.ttf")
        self.header_path = os.path.join(self.assets_dir, "nano_header.png")

    def _ar(self, text):
        """تجهيز النص العربي للـ PDF"""
        if not text: return ""
        reshaped_text = arabic_reshaper.reshape(str(text))
        return get_display(reshaped_text)

    def generate_nano_report(self, batch, daily_records, sales, costs):
        """
        إنشاء تقرير نانو الفاخر (Premium AI Style)
        """
        pdf = FPDF()
        pdf.add_page()
        
        # 1. إضافة الخط العربي
        if os.path.exists(self.font_path):
            pdf.add_font('Amiri', '', self.font_path, uni=True)
            pdf.set_font('Amiri', '', 14)
        else:
            pdf.set_font('Arial', '', 14)

        # 2. الهيدر الفاخر
        if os.path.exists(self.header_path):
            pdf.image(self.header_path, x=0, y=0, w=210)
            pdf.ln(45)
        else:
            pdf.ln(10)

        # 3. العنوان الرئيسي
        pdf.set_font('Amiri', '', 26)
        pdf.set_text_color(0, 90, 158) # أزرق نانو
        pdf.cell(0, 15, self._ar("تقرير الكفاءة الإنتاجية والتحليل المالي"), ln=True, align='C')
        pdf.set_font('Amiri', '', 14)
        pdf.set_text_color(100, 100, 100)
        pdf.cell(0, 10, self._ar(f"عنبر: {batch.warehouse.name} | رقم الدفعة: {batch.batch_num}"), ln=True, align='C')
        pdf.ln(5)

        # 4. بطاقات الأداء (KPI Cards)
        # سنقوم برسم مستطيلات ملونة كبطاقات
        self._draw_kpi_cards(pdf, batch)
        pdf.ln(35)

        # 5. جدول البيانات الأساسية
        pdf.set_text_color(0, 0, 0)
        pdf.set_font('Amiri', '', 12)
        pdf.set_fill_color(245, 247, 250)
        pdf.cell(0, 10, self._ar("ملخص البيانات التشغيلية"), 0, 1, 'R')
        
        details = [
            ("تاريخ الدخول", batch.date_in.strftime('%Y-%m-%d') if batch.date_in else "-"),
            ("تاريخ الخروج", batch.date_out.strftime('%Y-%m-%d') if batch.date_out else "مستمر"),
            ("عمر الدورة", f"{batch.days or 0} يوم"),
            ("إجمالي التكاليف", f"{batch.total_cost:,.2f} ريال"),
            ("إجمالي الإيرادات", f"{batch.total_rev:,.2f} ريال"),
            ("معدل التحويل FCR", f"{batch.fcr or 0:.3f}"),
            ("مؤشر الكفاءة EPEF", f"{batch.epef or 0:.0f}"),
        ]
        
        for label, val in details:
            pdf.set_fill_color(252, 252, 252)
            pdf.cell(95, 8, str(val), 1, 0, 'C', True)
            pdf.cell(95, 8, self._ar(label), 1, 1, 'R', True)

        # 6. الرسم البياني للنافق
        pdf.ln(10)
        chart_path = self._generate_mortality_chart(daily_records)
        if chart_path:
            pdf.image(chart_path, x=15, y=pdf.get_y(), w=180)
            # تنظيف الملف المؤقت
            try: os.remove(chart_path)
            except: pass

        # 7. تذييل الصفحة
        pdf.set_y(-25)
        pdf.set_font('Amiri', '', 9)
        pdf.set_text_color(150, 150, 150)
        pdf.cell(0, 10, self._ar("تم إنشاء هذا التقرير آلياً بواسطة نظام دوجي برو v5.0 - جميع الحقوق محفوظة"), 0, 0, 'C')

        # حفظ الملف
        filename = f"Nano_Report_{batch.batch_num}_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf"
        filepath = os.path.join(self.output_dir, filename)
        pdf.output(filepath)
        return filepath

    def _draw_kpi_cards(self, pdf, batch):
        """رسم بطاقات KPI ملونة"""
        start_y = pdf.get_y()
        cards = [
            ("صافي الربح", f"{batch.net_result:,.0f}", "#107C10"),
            ("النافق الكلي", f"{batch.total_dead:,}", "#A80000"),
            ("نسبة النافق", f"{batch.mort_rate:.1f}%", "#D83B01"),
            ("متوسط الوزن", f"{batch.avg_weight:.2f} كجم", "#0078D4"),
        ]
        
        card_w = 45
        card_h = 25
        spacing = 4
        
        curr_x = 10
        for title, val, color_hex in cards:
            # تحويل الهاكس إلى RGB
            r = int(color_hex[1:3], 16)
            g = int(color_hex[3:5], 16)
            b = int(color_hex[5:7], 16)
            
            pdf.set_fill_color(r, g, b)
            pdf.rect(curr_x, start_y, card_w, card_h, 'F')
            
            # نص العنوان (أبيض صغير)
            pdf.set_xy(curr_x, start_y + 3)
            pdf.set_font('Amiri', '', 10)
            pdf.set_text_color(255, 255, 255)
            pdf.cell(card_w, 8, self._ar(title), 0, 0, 'C')
            
            # القيمة (أبيض كبير)
            pdf.set_xy(curr_x, start_y + 11)
            pdf.set_font('Amiri', '', 16)
            pdf.cell(card_w, 12, val, 0, 0, 'C')
            
            curr_x += card_w + spacing

    def _generate_mortality_chart(self, records):
        """توليد صورة للرسم البياني"""
        if not records: return None
        
        days = [r.day_num for r in records]
        dead = [r.dead_count for r in records]
        
        plt.figure(figsize=(10, 4), dpi=100)
        plt.plot(days, dead, color='#A80000', linewidth=3, marker='o', markersize=5, label='النافق اليومي')
        plt.fill_between(days, dead, color='#FDE7E9', alpha=0.4)
        
        plt.title(self._ar("تحليل منحنى النافق اليومي"), fontsize=14)
        plt.grid(True, linestyle='--', alpha=0.6)
        
        # حفظ كصورة مؤقتة
        temp_path = f"temp_chart_{datetime.now().timestamp()}.png"
        plt.savefig(temp_path, bbox_inches='tight', transparent=True)
        plt.close()
        return temp_path

    def generate_daily_report(self, batch, records):
        """تقرير السجلات اليومية"""
        pdf = FPDF()
        pdf.add_page()
        if os.path.exists(self.font_path):
            pdf.add_font('Amiri', '', self.font_path, uni=True)
            pdf.set_font('Amiri', '', 16)
            
        pdf.cell(0, 15, self._ar(f"سجل البيانات اليومي - دفعة {batch.batch_num}"), ln=True, align='C')
        pdf.set_font('Amiri', '', 11)
        
        # الهيدر
        pdf.set_fill_color(230, 230, 230)
        headers = [("ملاحظات", 80), ("علف", 25), ("نافق", 20), ("يوم", 15), ("التاريخ", 40)]
        for h, w in headers:
            pdf.cell(w, 10, self._ar(h), 1, 0, 'C', True)
        pdf.ln()
        
        for r in records:
            notes = getattr(r, 'notes', "")
            pdf.cell(80, 8, self._ar(notes or ""), 1, 0, 'R')
            pdf.cell(25, 8, f"{r.feed_kg or 0}", 1, 0, 'C')
            pdf.cell(20, 8, str(r.dead_count or 0), 1, 0, 'C')
            pdf.cell(15, 8, str(r.day_num or ""), 1, 0, 'C')
            pdf.cell(40, 8, r.rec_date.strftime('%Y-%m-%d'), 1, 1, 'C')
            
        filename = f"Daily_Report_{batch.batch_num}_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf"
        filepath = os.path.join(self.output_dir, filename)
        pdf.output(filepath)
        return filepath

    def generate_financial_report(self, batch, sales, market_sales, costs):
        """التقرير المالي التفصيلي"""
        pdf = FPDF()
        pdf.add_page()
        if os.path.exists(self.font_path):
            pdf.add_font('Amiri', '', self.font_path, uni=True)
            pdf.set_font('Amiri', '', 18)
            
        pdf.cell(0, 15, self._ar(f"التقرير المالي - دفعة {batch.batch_num}"), ln=True, align='C')
        pdf.ln(5)
        
        pdf.set_font('Amiri', '', 12)
        pdf.set_fill_color(240, 240, 240)
        pdf.cell(0, 10, self._ar("ملخص الإيرادات"), 1, 1, 'R', True)
        
        # مبيعات العنبر
        pdf.set_fill_color(255, 255, 255)
        total_farm = sum(s.total_val for s in sales)
        pdf.cell(95, 10, f"{total_farm:,.2f}", 1, 0, 'C')
        pdf.cell(95, 10, self._ar("إجمالي مبيعات العنبر"), 1, 1, 'R')
        
        # مبيعات السوق
        total_market = sum(s.net_val for s in market_sales)
        pdf.cell(95, 10, f"{total_market:,.2f}", 1, 0, 'C')
        pdf.cell(95, 10, self._ar("إجمالي مبيعات السوق"), 1, 1, 'R')
        
        pdf.ln(5)
        pdf.set_fill_color(240, 240, 240)
        pdf.cell(0, 10, self._ar("ملخص التكاليف"), 1, 1, 'R', True)
        
        total_costs = sum(c.company_val for c in costs)
        pdf.cell(95, 10, f"{total_costs:,.2f}", 1, 0, 'C')
        pdf.cell(95, 10, self._ar("إجمالي تكاليف العنبر"), 1, 1, 'R')
        
        pdf.ln(10)
        # النتيجة النهائية
        net = (total_farm + total_market) - total_costs
        color = (16, 124, 16) if net >= 0 else (168, 0, 0)
        pdf.set_text_color(*color)
        pdf.set_font('Amiri', '', 20)
        pdf.cell(95, 15, f"{net:,.2f} ريال", 1, 0, 'C')
        pdf.set_text_color(0, 0, 0)
        pdf.cell(95, 15, self._ar("صافي الربح / الخسارة"), 1, 1, 'R')
        
        filename = f"Financial_Report_{batch.batch_num}_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf"
        filepath = os.path.join(self.output_dir, filename)
        pdf.output(filepath)
        return filepath
