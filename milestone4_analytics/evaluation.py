"""
SupportPilot / AeroAssist AI - Milestone 4 Evaluation Engine
Module: evaluation.py
Performs offline and online benchmark evaluations for:
1. Intent / Issue Classifier (Accuracy, Precision, Recall, Macro-F1, Confusion Matrix)
2. Knowledge Base Retrieval & RAG Resolution (KB Coverage, Retrieval Relevance, Success Rate)
"""

import os
import sys
import json
import time
import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional, Tuple
from sklearn.metrics import (
    accuracy_score,
    precision_recall_fscore_support,
    confusion_matrix,
    classification_report
)

# Ensure parent directory is in sys.path to access classifier, retriever, and agents
PARENT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PARENT_DIR not in sys.path:
    sys.path.insert(0, PARENT_DIR)

EVAL_DATASET_PATH = os.path.join(PARENT_DIR, "data", "evaluation_dataset.json")


def load_evaluation_dataset(dataset_path: Optional[str] = None) -> List[Dict[str, Any]]:
    """Loads ground-truth labelled evaluation dataset."""
    target_path = dataset_path or EVAL_DATASET_PATH
    if not os.path.exists(target_path):
        return []
    with open(target_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data if isinstance(data, list) else []


def evaluate_classifier_performance(
    dataset_path: Optional[str] = None
) -> Dict[str, Any]:
    """
    Evaluates the intent classifier against the ground truth dataset.
    Returns:
    - Overall Accuracy
    - Precision, Recall, Macro F1, Weighted F1
    - Per-category breakdown
    - Confusion Matrix (labels, matrix array)
    """
    try:
        from classifier import classify_ticket
    except ImportError:
        return {
            "error": "Classifier module not available in project path.",
            "accuracy": 0.0,
            "macro_f1": 0.0
        }

    dataset = load_evaluation_dataset(dataset_path)
    if not dataset:
        return {
            "error": "Evaluation dataset empty or not found.",
            "total_samples": 0,
            "accuracy": 0.0,
            "macro_f1": 0.0
        }

    y_true = []
    y_pred = []
    confidences = []
    latencies = []
    category_samples = []

    for item in dataset:
        text = item.get("text", "")
        true_cat = item.get("expected_category")
        if not text or not true_cat:
            continue

        t0 = time.perf_counter()
        pred_cat, conf = classify_ticket(text)
        t1 = time.perf_counter()

        y_true.append(true_cat)
        y_pred.append(pred_cat)
        confidences.append(conf)
        latencies.append((t1 - t0) * 1000.0)
        category_samples.append({
            "text_sample": text[:60] + "...",
            "expected_category": true_cat,
            "predicted_category": pred_cat,
            "confidence": round(conf, 4),
            "match": (true_cat == pred_cat)
        })

    if not y_true:
        return {"error": "No valid labelled samples to evaluate.", "total_samples": 0}

    labels = sorted(list(set(y_true + y_pred)))
    acc = accuracy_score(y_true, y_pred)
    prec_macro, rec_macro, f1_macro, _ = precision_recall_fscore_support(
        y_true, y_pred, labels=labels, average="macro", zero_division=0
    )
    prec_weighted, rec_weighted, f1_weighted, _ = precision_recall_fscore_support(
        y_true, y_pred, labels=labels, average="weighted", zero_division=0
    )

    # Per-class report
    class_report = classification_report(
        y_true, y_pred, labels=labels, output_dict=True, zero_division=0
    )
    
    # Per-class table DataFrame
    per_class_list = []
    for lbl in labels:
        if lbl in class_report:
            per_class_list.append({
                "Category": lbl,
                "Precision (%)": round(class_report[lbl]["precision"] * 100, 1),
                "Recall (%)": round(class_report[lbl]["recall"] * 100, 1),
                "F1-Score (%)": round(class_report[lbl]["f1-score"] * 100, 1),
                "Support": int(class_report[lbl]["support"])
            })
    df_per_class = pd.DataFrame(per_class_list)

    # Confusion matrix
    cm = confusion_matrix(y_true, y_pred, labels=labels)

    return {
        "total_samples": len(y_true),
        "accuracy": round(acc * 100.0, 2),
        "macro_precision": round(prec_macro * 100.0, 2),
        "macro_recall": round(rec_macro * 100.0, 2),
        "macro_f1": round(f1_macro * 100.0, 2),
        "weighted_f1": round(f1_weighted * 100.0, 2),
        "avg_confidence": round(float(np.mean(confidences)), 4),
        "avg_latency_ms": round(float(np.mean(latencies)), 2),
        "labels": labels,
        "confusion_matrix": cm.tolist(),
        "per_class_df": df_per_class,
        "sample_evaluations": pd.DataFrame(category_samples)
    }


def evaluate_resolution_and_rag(
    dataset_path: Optional[str] = None
) -> Dict[str, Any]:
    """
    Evaluates RAG retrieval relevance, decision correctness, and Knowledge-Base coverage.
    
    Definitions:
    - Resolution success rate = successfully auto-resolved tickets ÷ eligible tickets × 100.
    - Knowledge-base coverage = tickets with similarity >= 0.60 ÷ eligible tickets × 100.
    """
    try:
        from rag.retriever import retrieve_relevant_knowledge
        from agents import execute_full_resolution_workflow
    except ImportError:
        return {"error": "RAG retriever or agents module not available."}

    dataset = load_evaluation_dataset(dataset_path)
    if not dataset:
        return {"error": "Evaluation dataset empty or not found."}

    total_cases = len(dataset)
    retrieval_matches = 0
    correct_decisions = 0
    solvable_cases = 0
    solvable_resolved = 0
    escalation_expected_cases = 0
    correctly_escalated = 0

    results = []
    latencies = []

    for item in dataset:
        ticket_data = {
            "ticket_id": item.get("id", "EVAL-00"),
            "customer_id": "CUST-EVAL",
            "subject": item.get("text", "")[:40],
            "description": item.get("text", ""),
            "category": item.get("expected_category", "General"),
            "priority": item.get("expected_priority", "Medium"),
            "severity": "Low"
        }

        expected_action = item.get("expected_action", "AUTO_RESOLVE")
        expected_kb_id = item.get("expected_kb_id")

        t0 = time.perf_counter()
        agent_res = execute_full_resolution_workflow(ticket_data)
        t1 = time.perf_counter()
        latencies.append((t1 - t0) * 1000.0)

        actual_action = agent_res.get("final_action", "ESCALATE")
        sim_score = agent_res.get("retrieval_similarity", 0.0)
        final_conf = agent_res.get("final_confidence", 0.0)
        retrieved_id = agent_res.get("retrieved_kb_id", "")

        # Retrieval check
        kb_hit = False
        if expected_kb_id:
            kb_hit = (retrieved_id == expected_kb_id) or (sim_score >= 0.60)
            if kb_hit:
                retrieval_matches += 1

        # Decision match
        decision_match = (actual_action == expected_action)
        if decision_match:
            correct_decisions += 1

        if expected_action == "AUTO_RESOLVE":
            solvable_cases += 1
            if actual_action == "AUTO_RESOLVE":
                solvable_resolved += 1
        elif expected_action == "ESCALATE":
            escalation_expected_cases += 1
            if actual_action == "ESCALATE":
                correctly_escalated += 1

        results.append({
            "id": item.get("id"),
            "category": item.get("expected_category"),
            "expected_action": expected_action,
            "actual_action": actual_action,
            "decision_match": decision_match,
            "similarity": round(sim_score, 4),
            "confidence": round(final_conf, 4),
            "retrieved_kb_id": retrieved_id
        })

    decision_accuracy = (correct_decisions / total_cases * 100.0) if total_cases > 0 else 0.0
    auto_resolve_coverage = (solvable_resolved / solvable_cases * 100.0) if solvable_cases > 0 else 0.0
    escalation_accuracy = (correctly_escalated / escalation_expected_cases * 100.0) if escalation_expected_cases > 0 else 0.0
    kb_coverage = (retrieval_matches / total_cases * 100.0) if total_cases > 0 else 0.0

    return {
        "total_evaluated": total_cases,
        "decision_accuracy": round(decision_accuracy, 2),
        "solvable_auto_resolve_rate": round(auto_resolve_coverage, 2),
        "escalation_safety_rate": round(escalation_accuracy, 2),
        "kb_coverage_rate": round(kb_coverage, 2),
        "avg_pipeline_latency_ms": round(float(np.mean(latencies)), 2),
        "detailed_results_df": pd.DataFrame(results)
    }
