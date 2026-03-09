from collections import defaultdict



#Causal macro graph explaining macro relationships
MACRO_GRAPH = {
    "inflation": ["central_bank_policy", "bond_yields"],
    "central_bank_policy": ["bond_yields", "equities", "currencies"],
    "growth": ["equities", "commodities"],
    "oil_prices": ["inflation"],
    "bond_yields": ["equities", "currencies"],
    "risk_sentiment": ["equities", "currencies", "credit"],
    "geopolitics": ["oil_prices", "risk_sentiment"]
}


def propagate_macro_shock(node, direction = "up"):
    """
    Propagates macro shocks across the causal graph
    """

    impacts = []

    if node not in MACRO_GRAPH:
        return impacts
    
    for affected in MACRO_GRAPH[node]:

        if direction == "up":
            effect = "increase"
        else:
            effect = "decrease"

        impacts.append({
            "source": node,
            "target": affected,
            "effect": effect
        })

        return impacts
    

def generate_risk_implications(node, direction):

    propagation = propagate_macro_shock(node, direction)

    risks = []

    for p in propagation:

        if p["target"] == "bond_yields":
            risks.append("Duration risk rising")
        
        if p["target"] == "equities":
            risks.append("equity volatility likely")

        if p["target"] == "currencies":
            risks.append("FX volatility increasing")

        if p["target"] == "commodities":
            risks.append("Commodity inflation risk")

    return list(set(risks))

