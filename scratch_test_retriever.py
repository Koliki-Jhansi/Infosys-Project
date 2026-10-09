import json
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from rag.knowledge_base import load_knowledge_base

eval_data = json.load(open('data/evaluation_dataset.json', encoding='utf-8'))
articles = load_knowledge_base()

corpus = []
for art in articles:
    t = art.get('title', '')
    cat = art.get('category', '')
    cl = art.get('cluster', '')
    kw = " ".join(art.get('keywords', []))
    c = art.get('content', '')
    doc = f"{t} {t} {t} {cat} {cl} {kw} {kw} {c}"
    corpus.append(doc)

vec = TfidfVectorizer(ngram_range=(1, 2), stop_words="english", sublinear_tf=True)
kb_mat = vec.fit_transform(corpus)

correct_top1 = 0
total_expected = 0
sim_scores = []

for case in eval_data:
    exp_kb = case.get('expected_kb_id')
    if not exp_kb:
        continue
    total_expected += 1
    
    q = f"{case['title']} {case['description']}"
    q_vec = vec.transform([q])
    sims = cosine_similarity(q_vec, kb_mat)[0]
    
    best_idx = np.argmax(sims)
    top_art = articles[best_idx]
    top_sim = sims[best_idx]
    sim_scores.append(top_sim)
    
    if top_art['id'] == exp_kb:
        correct_top1 += 1
    else:
        print(f"Mismatch {case['id']}: Exp {exp_kb}, Got {top_art['id']} ({top_art['title']}) - sim: {top_sim:.4f}")

print(f"Top-1 Retrieval Accuracy: {correct_top1}/{total_expected} ({correct_top1/total_expected*100:.2f}%)")
print(f"Average Top-1 Raw Similarity: {np.mean(sim_scores):.4f}")
