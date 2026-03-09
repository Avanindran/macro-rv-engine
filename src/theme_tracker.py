import datetime
from collections import defaultdict


theme_history = defaultdict(list)


def update_theme(theme):

    timestamp = datetime.datetime.now()
    theme_history[theme].append(timestamp)



def calculate_theme_heat():
    heat_scores = {}
    
    now = datetime.datetime.now()

    for theme, timestamps in theme_history.items():
        score = 0

        for t in timestamps:
            delta_hours =(now - t).total_seconds() / 3600
            weight = max(0, 1 - (delta_hours/24))
            score += weight
        
        heat_scores[theme] = round(score, 2)
    
    return heat_scores

def get_hottest_theme():

    heat = calculate_theme_heat()
    if not heat:
        return None
    return max(heat, key=heat.get)