from collections import defaultdict


"""
Systematic Causal Knowledge Graph
Deterministic relationships for multi-level macro shock propagation.
"""

MACRO_NODES = [
    "growth", "inflation", "central_bank_policy", "liquidity", "real_rates", 
    "yield_curve", "credit_spreads", "equity_risk_premium", "dollar", "em_fx",
    "oil", "commodities", "gold", "equities", "tech_equities", "value_equities",
    "bonds", "long_duration_bonds", "short_rates", "housing", "consumer_spending", 
    "labor_market", "banking_stress", "financial_conditions", "china_growth", 
    "global_trade", "geopolitics", "supply_chain", "volatility", "vix", 
    "move_index", "risk_appetite", "flight_to_safety", "crypto", "em_equities", 
    "em_debt", "carry_trades", "funding_costs"
]

MACRO_EDGES = {
    "inflation": [
        ("central_bank_policy", "hawkish"),
        ("real_rates", "up"),
        ("gold", "up"),
        ("bonds", "down")
    ],
    "central_bank_policy": [
        ("liquidity", "down"),
        ("equities", "down"),
        ("dollar", "up")
    ],
    "growth": [
        ("equities", "up"),
        ("commodities", "up"),
        ("yield_curve", "steepen")
    ],
    "geopolitics": [
        ("oil", "up"),
        ("volatility", "up"),
        ("equities", "down")
    ],
    "liquidity": [
        ("equities", "up"),
        ("crypto", "up"),
        ("tech_equities", "up")
    ],
    "banking_stress": [
        ("credit_spreads", "up"),
        ("equities", "down"),
        ("flight_to_safety", "up")
    ],
    # Adding a few bridge nodes to make the chain reactions deeper
    "oil": [
        ("inflation", "up")
    ],
    "volatility": [
        ("liquidity", "down")
    ]
}

def invert_effect(effect: str) -> str:
    """Flips the contagion effect if the upstream node is negative."""
    inversions = {
        "up": "down",
        "down": "up",
        "hawkish": "dovish",
        "dovish": "hawkish",
        "steepen": "flatten",
        "flatten": "steepen"
    }
    return inversions.get(effect.lower(), effect)

def propagate_macro_shock(node: str, direction: str, max_depth: int = 2) -> list:
    """
    Propagates a shock through the deterministic causal graph using BFS traversal.
    Finds 1st and 2nd order chain reactions.
    """
    results = []
    
    node = node.lower().strip() if node else ""
    direction = direction.lower().strip() if direction else "up"

    if not node or node not in MACRO_EDGES:
        return results

    # Queue stores: (current_node, current_direction, current_depth)
    queue = [(node, direction, 0)]
    visited_edges = set() # To prevent infinite loops if the graph has cycles
    
    while queue:
        curr_node, curr_dir, depth = queue.pop(0)
        
        # Stop traversing if we hit our depth limit
        if depth >= max_depth:
            continue
            
        if curr_node not in MACRO_EDGES:
            continue
            
        for target, base_effect in MACRO_EDGES[curr_node]:
            # Prevent infinite loops (e.g., A -> B -> A)
            edge_sig = (curr_node, target)
            if edge_sig in visited_edges:
                continue
            visited_edges.add(edge_sig)
            
            # If the current node's direction is negative, invert its impact on the target
            if curr_dir in ["down", "decreases", "bearish", "cooling", "drops", "dovish", "flatten"]:
                final_effect = invert_effect(base_effect)
            else:
                final_effect = base_effect
                
            results.append({
                "source": curr_node,
                "target": target,
                "effect": final_effect
            })
            
            # Add the target back into the queue to find its downstream effects
            queue.append((target, final_effect, depth + 1))
            
    return results

def generate_risk_implications(node: str, direction: str) -> list:
    """Generates plain-text risk warnings based on the BFS graph."""
    propagation = propagate_macro_shock(node, direction)
    risks = []
    
    for p in propagation:
        risks.append(f"Systematic Risk Alert: Monitor {p['target'].upper()} exposure due to secondary {p['effect'].upper()} pressures stemming from {p['source'].upper()}.")
    
    if not risks:
        risks.append("No direct systemic risks mapped in the causal graph for this specific node.")
        
    return list(set(risks)) # Deduplicate risks
