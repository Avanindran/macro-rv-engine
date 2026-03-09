import networkx as nx

def build_macro_graph():

    G = nx.DiGraph()

    edges = [
        ("inflation", "central_bank_policy"),
        ("central_bank_policy", "bond_yields"),
        ("bond_yields", "equities"),
        ("bond_yields", "fx"),
        ("oil", "inflation"),
        ("geopolitics", "oil"),
    ]

    G.add_edges_from(edges)

    return G