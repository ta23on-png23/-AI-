# logic.py

def judge_prediction(t1, t4, is_women_race):
    """
    展示タイムとレース種別から予測を出すロジック
    """
    diff = t1 - t4
    
    # 0.10秒差判定
    is_power_diff = diff >= 0.10
    
    # 女子戦なら判定を少し厳しく、あるいは注目度を上げる（今後の拡張用）
    if is_women_race:
        pass 

    # 判定
    if is_power_diff:
        return "4-5-1", f"⚠️ 中穴アラート！(タイム差:{diff:.2f})"
    else:
        return "1-2-3", "✅ 本命展開"