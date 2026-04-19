def calc_mortality_rate(dead, total):
    if not total: return 0.0
    return round((dead / total) * 100, 2)

def calc_fcr(feed_kg, weight_kg):
    if not weight_kg: return 0.0
    return round(feed_kg / weight_kg, 2)

def calc_epef(mortality_rate, avg_weight, days, fcr):
    """
    EPEF = [(100 - Mortality %) * Avg. Weight (kg) * 10] / [Days * FCR]
    """
    try:
        if not days or not fcr: return 0.0
        num = (100 - mortality_rate) * avg_weight * 10
        den = days * fcr
        return round(num / den, 0)
    except:
        return 0.0

def calc_profit_sharing(net_result, share_pct=65):
    share_val = (net_result * share_pct) / 100
    partner_val = net_result - share_val
    return share_val, partner_val
