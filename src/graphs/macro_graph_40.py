MACRO_NODES = [

"growth",
"inflation",
"central_bank_policy",
"liquidity",
"real_rates",
"yield_curve",
"credit_spreads",
"equity_risk_premium",
"dollar",
"em_fx",

"oil",
"commodities",
"gold",

"equities",
"tech_equities",
"value_equities",

"bonds",
"long_duration_bonds",
"short_rates",

"housing",
"consumer_spending",
"labor_market",

"banking_stress",
"financial_conditions",

"china_growth",
"global_trade",

"geopolitics",
"supply_chain",

"volatility",
"vix",
"move_index",

"risk_appetite",
"flight_to_safety",

"crypto",
"em_equities",
"em_debt",

"carry_trades",
"funding_costs",
]

MACRO_EDGES = {

"inflation":[
("central_bank_policy","hawkish"),
("real_rates","up"),
("gold","up"),
("bonds","down")
],

"central_bank_policy":[
("liquidity","down"),
("equities","down"),
("dollar","up")
],

"growth":[
("equities","up"),
("commodities","up"),
("yield_curve","steepen")
],

"geopolitics":[
("oil","up"),
("volatility","up"),
("equities","down")
],

"liquidity":[
("equities","up"),
("crypto","up"),
("tech_equities","up")
],

"banking_stress":[
("credit_spreads","up"),
("equities","down"),
("flight_to_safety","up")
],

}


def propagate_macro_event(node,direction):

    results=[]

    if node not in MACRO_EDGES:
        return results
    for target,effect in MACRO_EDGES[node]:

        results.append({
            "source":node,
            "target":target,
            "effect":effect
        })
    return results

