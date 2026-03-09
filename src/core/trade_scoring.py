def score_trades(trades, propagation):

    scored = []

    for trade in trades:

        score = 50

        score += len(propagation) * 5

        if "Gold" in trade:
            score += 5

        if "Oil" in trade:
            score += 5

        scored.append({

            "trade":trade,
            "confidence":min(score,95)

        })

    return sorted(scored, key=lambda x: x["confidence"], reverse=True)