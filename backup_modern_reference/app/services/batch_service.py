from ..database import get_session
from ..models import Batch, Warehouse, DailyRecord, CostType, BatchCost, BatchStandards, MarketSale, FarmSale, BatchRevenue
from datetime import datetime
from sqlalchemy import select, func
from sqlalchemy.orm import joinedload

class BatchService:
    def get_all_batches(self):
        with get_session() as session:
            return session.query(Batch).options(joinedload(Batch.warehouse)).order_by(Batch.date_in.desc()).all()

    def create_batch(self, data):
        with get_session() as session:
            costs_data = data.pop("costs", {})
            batch = Batch(**data)
            session.add(batch)
            session.flush()
            
            total_extra_costs = 0
            for code, amount in costs_data.items():
                if amount > 0:
                    bc = BatchCost(batch_id=batch.id, cost_type_code=code, total_val=amount)
                    session.add(bc)
                    total_extra_costs += amount
                    if hasattr(batch, code):
                        setattr(batch, code, amount)
            
            if batch.total_cost == 0:
                batch.total_cost = total_extra_costs
            
            session.commit()
            return batch

    def update_batch(self, batch_id, data):
        with get_session() as session:
            costs_data = data.pop("costs", {})
            batch = session.get(Batch, batch_id)
            if not batch: return False
            for key, value in data.items():
                setattr(batch, key, value)
            
            session.query(BatchCost).filter_by(batch_id=batch_id).delete()
            for code, amount in costs_data.items():
                if amount > 0:
                    bc = BatchCost(batch_id=batch.id, cost_type_code=code, total_val=amount)
                    session.add(bc)
                    if hasattr(batch, code):
                        setattr(batch, code, amount)
            session.commit()
            return True

    def get_financial_summary(self, batch_id):
        """حساب الخلاصة المالية الدقيقة للدفعة بناءً على أحدث البيانات"""
        with get_session() as session:
            try:
                batch = session.get(Batch, batch_id)
                if not batch: return None

                total_dead_daily = session.query(func.sum(DailyRecord.dead_count)).filter(DailyRecord.batch_id == batch_id).scalar() or 0
                market_sales = session.query(MarketSale).filter(MarketSale.batch_id == batch_id).all()
                market_sold = sum(s.qty_sold for s in market_sales)
                market_dead = sum(s.deaths for s in market_sales)
                farm_sales = session.query(FarmSale).filter(FarmSale.batch_id == batch_id).all()
                farm_sold = sum(s.qty for s in farm_sales)
                
                total_sold = market_sold + farm_sold
                total_dead = total_dead_daily + market_dead
                consumed = batch.consumed_birds or 0
                chicks = batch.chicks or 0
                bird_diff = chicks - (total_sold + total_dead + consumed)

                total_feed_consumed = session.query(func.sum(DailyRecord.feed_kg)).filter(DailyRecord.batch_id == batch_id).scalar() or 0
                feed_in = batch.feed_qty or 0
                feed_sold = batch.feed_sale_qty or 0
                feed_rem = batch.feed_rem_qty or 0
                feed_diff = feed_in - (total_feed_consumed + feed_sold + feed_rem)

                costs_list = []
                cost_mapping = [
                    ("الكتاكيت", "chicks", "chick_val"),
                    ("العلف", "feed_qty", "feed_val"),
                    ("النشارة", "sawdust_qty", "sawdust_val"),
                    ("الغاز", "gas_qty", "gas_val"),
                    ("الماء", None, "water_val"),
                    ("العلاجات", None, "drugs_val"),
                    ("مصاريف عنبر", None, "wh_expenses"),
                    ("مصاريف بيت", None, "house_exp"),
                    ("أجور مربيين", None, "breeders_pay"),
                    ("قات مربيين", None, "qat_pay"),
                    ("إيجار عنبر", None, "rent_val"),
                    ("إضاءة", None, "light_val"),
                    ("إدارة وحسابات", None, "admin_val"),
                    ("لقاحات", None, "vaccine_pay"),
                ]
                
                total_cost = 0
                for label, qty_col, val_col in cost_mapping:
                    val = getattr(batch, val_col, 0) or 0
                    if val > 0:
                        qty = getattr(batch, qty_col, 0) if qty_col else None
                        costs_list.append({"type": label, "qty": float(qty) if qty is not None else None, "amount": float(val)})
                        total_cost += val

                sup_tot = (batch.sup_wh_pay or 0) + (batch.sup_co_pay or 0) + (batch.sup_sale_pay or 0)
                if sup_tot > 0:
                    costs_list.append({"type": "إشراف وتسويق", "amount": float(sup_tot)})
                    total_cost += sup_tot
                
                oth_tot = (batch.delivery_val or 0) + (batch.mixing_val or 0) + (batch.wash_val or 0) + (batch.other_costs or 0)
                if oth_tot > 0:
                    costs_list.append({"type": "مصاريف أخرى متنوعة", "amount": float(oth_tot)})
                    total_cost += oth_tot

                total_rev = 0
                rev_list = []
                market_rev = sum(s.net_val for s in market_sales if s.net_val)
                if market_rev > 0:
                    rev_list.append({"type": "مبيعات السوق", "qty": float(market_sold), "amount": float(market_rev)})
                    total_rev += market_rev
                
                farm_rev = sum(s.total_val for s in farm_sales if s.total_val)
                if farm_rev > 0:
                    rev_list.append({"type": "مبيعات المزرعة", "qty": float(farm_sold), "amount": float(farm_rev)})
                    total_rev += farm_rev
                
                if batch.offal_val:
                    rev_list.append({"type": "مبيعات ذبيل", "amount": float(batch.offal_val)})
                    total_rev += batch.offal_val
                if batch.feed_sale:
                    rev_list.append({"type": "مبيعات علف", "qty": float(batch.feed_sale_qty or 0), "amount": float(batch.feed_sale)})
                    total_rev += batch.feed_sale
                if batch.feed_trans_r:
                    rev_list.append({"type": "علف منقول / متبقي", "qty": float(batch.feed_trans_r_qty or 0), "amount": float(batch.feed_trans_r)})
                    total_rev += batch.feed_trans_r
                if batch.drug_return:
                    rev_list.append({"type": "مرتجع علاجات", "amount": float(batch.drug_return)})
                    total_rev += batch.drug_return
                if batch.gas_return:
                    rev_list.append({"type": "نقل غاز/نشارة", "amount": float(batch.gas_return)})
                    total_rev += batch.gas_return

                net_result = total_rev - total_cost
                share_pct = batch.share_pct or 65.0
                partner_share = (net_result * (share_pct / 100)) if net_result > 0 else 0
                company_share = net_result - partner_share if net_result > 0 else net_result

                mort_rate = (total_dead / chicks * 100) if chicks > 0 else 0
                total_weight = sum(s.qty_sold for s in market_sales if s.qty_sold)
                avg_price = (total_rev / total_weight) if total_weight > 0 else 0
                avg_weight = (total_weight / total_sold) if total_sold > 0 else 0
                fcr = (total_feed_consumed / total_weight) if total_weight > 0 else 0

                batch.total_cost = total_cost
                batch.total_rev = total_rev
                batch.total_dead = total_dead
                batch.total_sold = total_sold
                batch.mort_rate = mort_rate
                batch.net_result = net_result
                batch.fcr = fcr
                batch.avg_weight = avg_weight
                session.commit()

                return {
                    "batch_id": batch.id, "batch_num": batch.batch_num,
                    "warehouse_name": batch.warehouse.name if batch.warehouse else "N/A",
                    "partner_name": batch.partner_name or "بدون شريك",
                    "chicks": int(chicks), "total_cost": float(total_cost),
                    "total_rev": float(total_rev), "net_result": float(net_result),
                    "mort_rate": float(mort_rate), "fcr": float(fcr),
                    "avg_weight": float(avg_weight), "avg_price": float(avg_price),
                    "total_weight": float(total_weight), "total_sold": int(total_sold),
                    "total_dead": int(total_dead), "market_dead": int(market_dead),
                    "consumed_birds": int(consumed), "bird_diff": int(bird_diff),
                    "feed_in": float(feed_in), "feed_consumed": float(total_feed_consumed),
                    "feed_sold": float(feed_sold), "feed_rem": float(feed_rem),
                    "feed_diff": float(feed_diff), "share_pct": float(share_pct),
                    "partner_share": float(partner_share), "company_share": float(company_share),
                    "costs": costs_list, "revenues": rev_list
                }
            except Exception as e:
                return None
