from decimal import Decimal
from datetime import date

class PoultryCalculator:
    @staticmethod
    def calculate_mortality(total_dead, total_chicks):
        if not total_chicks or total_chicks == 0:
            return 0.0
        return round((total_dead / total_chicks) * 100, 2)

    @staticmethod
    def calculate_fcr(feed_kg, total_weight_kg):
        if not total_weight_kg or total_weight_kg == 0:
            return 0.0
        return round(feed_kg / total_weight_kg, 3)

    @staticmethod
    def calculate_epef(viability_pct, avg_weight_kg, age_days, fcr):
        """
        European Production Efficiency Factor (EPEF)
        Formula: (Viability % × Live weight in kg × 100) / (Age in days × FCR)
        Wait, standard formula is often: (Viability % × Avg Weight kg) / (Age days × FCR) * 100
        """
        if not age_days or not fcr or age_days == 0 or fcr == 0:
            return 0.0
        return round((viability_pct * avg_weight_kg * 100) / (age_days * fcr), 2)

    @staticmethod
    def calculate_batch_stats(batch_model):
        """
        يقوم بحساب الإحصائيات لدفعة معينة بناءً على البيانات المتوفرة في الكائن
        """
        # 1. حساب الأيام
        if batch_model.date_in and batch_model.date_out:
            delta = batch_model.date_out - batch_model.date_in
            batch_model.days = delta.days
        elif batch_model.date_in:
            delta = date.today() - batch_model.date_in
            batch_model.days = delta.days

        # 2. حساب النافق
        total_dead = sum([r.dead_count for r in batch_model.daily_records]) if batch_model.daily_records else batch_model.total_dead
        batch_model.total_dead = total_dead
        batch_model.mort_rate = PoultryCalculator.calculate_mortality(total_dead, batch_model.chicks)

        # 3. حساب العلف
        total_feed = sum([r.feed_kg for r in batch_model.daily_records]) if batch_model.daily_records else (batch_model.feed_qty * 1000)
        
        # 4. حساب الوزن المبيوع (تحتاج لبيانات المبيعات)
        total_sold_qty = sum([s.qty for s in batch_model.farm_sales]) if batch_model.farm_sales else 0
        total_sold_qty += sum([s.qty_sold for s in batch_model.market_sales]) if batch_model.market_sales else 0
        
        # الوزن الكلي = الكمية المباعة * متوسط الوزن (إذا لم يكن متوفر بدقة من المبيعات)
        total_weight = total_sold_qty * (batch_model.avg_weight or 1.5)
        
        # 5. حساب FCR
        batch_model.fcr = PoultryCalculator.calculate_fcr(total_feed, total_weight)
        
        # 6. حساب EPEF
        viability = 100 - batch_model.mort_rate
        batch_model.epef = PoultryCalculator.calculate_epef(viability, batch_model.avg_weight or 0, batch_model.days, batch_model.fcr)

        return batch_model

def calculate_mortality_rate(total_chicks, total_dead):
    """Standalone function for UI compatibility"""
    if not total_chicks or total_chicks == 0:
        return 0.0
    return round((total_dead / total_chicks) * 100, 2)
