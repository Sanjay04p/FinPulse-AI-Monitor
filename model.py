import os
import torch
from transformers import pipeline

def load_finbert():
    """
    Loads FinBERT with authentication and error handling.
    """
    device = 0 if torch.cuda.is_available() else -1
    
    token = os.getenv("HF_TOKEN")

    try:
        # 3. Initialize the pipeline
        pipe = pipeline(
            "sentiment-analysis", 
            model="ProsusAI/finbert", 
            device=device,
            token=token  
        )
        return pipe
    except Exception as e:
        
        print(f"Error loading FinBERT: {e}")
        return None

def analyze_news_list(news_items, pipe):
    """
    Runs analysis only if the pipeline exists.
    """
    if pipe is None:
        return []
        
    results = []
    for item in news_items[:20]:
        text = item['headline']
        prediction = pipe(text[:512])[0]
        
        results.append({
            "datetime": item['datetime'],
            "headline": text,
            "url": item['url'],
            "label": prediction['label'],
            "score": prediction['score']
        })
    return results