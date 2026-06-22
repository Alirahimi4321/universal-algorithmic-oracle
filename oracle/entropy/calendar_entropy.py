"""Calendar-based entropy generation."""
import math
import time
from datetime import datetime

def _gregorian_to_jalali(gy, gm, gd):
    """Convert Gregorian date to Jalali (Persian) calendar."""
    g_d_m = [0, 31, 59, 90, 120, 151, 181, 212, 243, 273, 304, 334]
    if gm > 2:
        gy2 = gy + 1
    else:
        gy2 = gy
    days = 355666 + (365 * gy) + ((gy2 + 3) // 4) - ((gy2 + 99) // 100) + ((gy2 + 399) // 400) + gd + g_d_m[gm - 1]
    jy = -1595 + (33 * (days // 12053))
    days %= 12053
    jy += 4 * (days // 1461)
    days %= 1461
    if days > 365:
        jy += (days - 1) // 365
        days = (days - 1) % 365
    if days < 186:
        jm = 1 + (days // 31)
        jd = 1 + (days % 31)
    else:
        jm = 7 + ((days - 186) // 30)
        jd = 1 + ((days - 186) % 30)
    return jy, jm, jd

def _gregorian_to_hijri(gy, gm, gd):
    """Convert Gregorian date to Hijri (Islamic) calendar."""
    jd = int((1461 * (gy + 4800 + (gm - 14) // 12)) / 4) + int((367 * (gm - 2 - 12 * ((gm - 14) // 12))) / 12) - int((3 * ((gy + 4900 + (gm - 14) // 12) // 100)) / 4) + gd - 32075
    l = jd - 1948440 + 10632
    n = int((l - 1) / 10631)
    l = l - 10631 * n + 354
    j = int((10985 - l) / 5316) * int((50 * l) / 17719) + int(l / 5670) * int((43 * l) / 15238)
    l = l - int((30 - j) / 15) * int((17719 * j) / 50) - int(j / 16) * int((15238 * j) / 43) + 29
    hm = int((24 * l) / 709)
    hd = l - int((709 * hm) / 24)
    hy = 30 * n + j - 30
    return hy, hm, hd

def generate_calendar_entropy() -> dict:
    now = datetime.now()
    timestamp = time.time()
    
    gregorian = {"year": now.year, "month": now.month, "day": now.day, 
                 "hour": now.hour, "minute": now.minute}
    
    jy, jm, jd = _gregorian_to_jalali(now.year, now.month, now.day)
    jalali = {"year": jy, "month": jm, "day": jd}
    
    hy, hm, hd = _gregorian_to_hijri(now.year, now.month, now.day)
    hijri = {"year": hy, "month": hm, "day": hd}
    
    numeric_signature = [
        math.sin(now.month * 0.5) * 0.5 + 0.5,
        math.cos(now.day * 0.3) * 0.5 + 0.5,
        math.sin(now.hour * 0.1) * 0.5 + 0.5,
        math.sin(timestamp % 1.0 * 2 * math.pi),
    ]
    
    return {
        "gregorian": gregorian,
        "jalali": jalali,
        "hijri": hijri,
        "numeric_signature": numeric_signature,
        "timestamp": timestamp,
    }
