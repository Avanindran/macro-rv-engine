


def classify_regime(growth_signal, inflation_signal):

    if growth_signal >= 0 and inflation_signal <= 0:
        return "Goldilocks"
    elif growth_signal >= 0 and inflation_signal >= 0:
        return "Overheating"
    elif growth_signal <= 0 and inflation_signal >= 0:
        return "Stagflation"
    elif growth_signal <= 0 and inflation_signal <= 0:
        return "Recession"
    
    return "Neutral"