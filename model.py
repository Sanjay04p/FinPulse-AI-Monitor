from transformers import pipeline

def load_finbert():
    """
    Loads the FinBERT model.
    """
    pipe = pipeline("sentiment-analysis", model="ProsusAI/finbert")
    return pipe

def analyze_news_list(news_items, pipe):
    """
    Takes raw news items and the model pipeline, 
    returns the list with sentiment scores AND dates.
    """
    results = []
    
    for item in news_items[:20]:
        text = item['headline']
        
        # Run prediction
        prediction = pipe(text[:512])[0]
        
        results.append({
            "datetime": item['datetime'],  
            "headline": text,
            "url": item['url'],
            "label": prediction['label'],
            "score": prediction['score']
        })
    return results