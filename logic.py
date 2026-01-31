def judge_prediction(t1, t4, is_women_race):
    """
    展示タイムの差から予測を出すロジック
    """
    diff = t1 - t4
    if diff >= 0.10:
        return "4-5-1", f"⚠️ 中穴アラート！(タイム差:{diff:.2f})"
    else:
        return "1-2-3", "✅ 本命展開"
