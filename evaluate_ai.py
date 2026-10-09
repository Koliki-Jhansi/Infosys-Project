"""
AeroAssist AI - Evaluation & Performance Benchmark Engine
Runs standardized evaluation on curated test cases and produces reproducible
metrics including accuracy, precision, recall, F1, retrieval relevance, and confidence breakdowns.
"""
import os
import json
from collections import defaultdict
from typing import Dict, List, Any
import numpy as np

from unittest.mock import patch
from agents import get_multi_agent_system
from classifier import get_classifier, CATEGORIES

def run_evaluation(dataset_path: str = None) -> Dict[str, Any]:
    if dataset_path is None:
        dataset_path = os.path.join(os.path.dirname(__file__), "data", "evaluation_dataset.json")

    with open(dataset_path, "r", encoding="utf-8") as f:
        cases = json.load(f)

    with patch("agents.create_jira_issue", return_value={"status": "Not Configured", "jira_created": False}), \
         patch("agents.send_escalation_email", return_value={"status": "Not Configured"}):
        return _execute_evaluation(cases)

def _execute_evaluation(cases: List[Dict[str, Any]]) -> Dict[str, Any]:

    mas = get_multi_agent_system()
    classifier = get_classifier()

    total_cases = len(cases)
    cat_correct = 0
    decision_correct = 0
    human_escalations_correct = 0
    human_cases_total = 0
    auto_resolve_cases_total = 0
    auto_resolve_passed = 0
    retrieval_correct = 0
    retrieval_total_expected = 0

    cat_true = []
    cat_pred = []
    
    diag_scores = []
    ret_scores = []
    comp_scores = []
    final_scores = []

    case_results = []

    for case in cases:
        c_id = case["id"]
        title = case["title"]
        desc = case["description"]
        exp_cat = case["expected_category"]
        exp_kb = case.get("expected_kb_id")
        req_human = case.get("requires_human_support", False)
        exp_dec = case["expected_decision"]

        ticket_payload = {
            "ticket_id": c_id,
            "title": title,
            "description": desc,
            "category": exp_cat
        }

        # Run multi-agent system
        res = mas.process_ticket(ticket_payload)
        pred_cat = res["diagnosis_category"]
        act_dec = res["decision"]
        act_kb = res.get("retrieved_kb_id")
        sim_score = res.get("retrieval_similarity", 0.0)
        diag_conf = res.get("diagnosis_confidence", 0.0)
        res_comp = res.get("resolution_completeness", 0.0)
        final_conf = res.get("final_confidence", 0.0)

        cat_true.append(exp_cat)
        cat_pred.append(pred_cat)
        if pred_cat == exp_cat:
            cat_correct += 1

        if act_dec == exp_dec:
            decision_correct += 1

        if req_human:
            human_cases_total += 1
            if act_dec == "ESCALATE":
                human_escalations_correct += 1
        else:
            auto_resolve_cases_total += 1
            if act_dec == "AUTO_RESOLVE":
                auto_resolve_passed += 1

        if exp_kb:
            retrieval_total_expected += 1
            if act_kb == exp_kb:
                retrieval_correct += 1

        diag_scores.append(diag_conf)
        ret_scores.append(sim_score)
        comp_scores.append(res_comp)
        final_scores.append(final_conf)

        case_results.append({
            "id": c_id,
            "scenario": case.get("scenario"),
            "title": title,
            "expected_category": exp_cat,
            "predicted_category": pred_cat,
            "category_match": bool(pred_cat == exp_cat),
            "expected_kb_id": exp_kb,
            "retrieved_kb_id": act_kb,
            "retrieval_match": bool(act_kb == exp_kb) if exp_kb else None,
            "diagnosis_confidence": round(diag_conf, 4),
            "retrieval_similarity": round(sim_score, 4),
            "resolution_completeness": round(res_comp, 4),
            "final_confidence": round(final_conf, 4),
            "expected_decision": exp_dec,
            "actual_decision": act_dec,
            "decision_match": bool(act_dec == exp_dec)
        })

    # Calculate Classification Precision, Recall, F1 per class and macro
    category_metrics = {}
    macro_p, macro_r, macro_f1 = 0.0, 0.0, 0.0
    unique_cats = sorted(list(set(cat_true + cat_pred)))

    for cat in unique_cats:
        tp = sum(1 for t, p in zip(cat_true, cat_pred) if t == cat and p == cat)
        fp = sum(1 for t, p in zip(cat_true, cat_pred) if t != cat and p == cat)
        fn = sum(1 for t, p in zip(cat_true, cat_pred) if t == cat and p != cat)
        
        prec = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        rec = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f1 = (2 * prec * rec) / (prec + rec) if (prec + rec) > 0 else 0.0
        
        category_metrics[cat] = {
            "precision": round(prec, 4),
            "recall": round(rec, 4),
            "f1_score": round(f1, 4),
            "support": sum(1 for t in cat_true if t == cat)
        }
        macro_p += prec
        macro_r += rec
        macro_f1 += f1

    n_cats = len(unique_cats) if unique_cats else 1
    macro_p /= n_cats
    macro_r /= n_cats
    macro_f1 /= n_cats

    eval_summary = {
        "sample_size": total_cases,
        "classification_accuracy": round(cat_correct / total_cases * 100, 2),
        "macro_precision": round(macro_p * 100, 2),
        "macro_recall": round(macro_r * 100, 2),
        "macro_f1_score": round(macro_f1 * 100, 2),
        "category_metrics": category_metrics,
        "retrieval_relevance_rate": round(retrieval_correct / max(1, retrieval_total_expected) * 100, 2),
        "retrieval_expected_count": retrieval_total_expected,
        "retrieval_matched_count": retrieval_correct,
        "overall_decision_accuracy": round(decision_correct / total_cases * 100, 2),
        "solvable_auto_resolution_rate": round(auto_resolve_passed / max(1, auto_resolve_cases_total) * 100, 2),
        "human_escalation_capture_rate": round(human_escalations_correct / max(1, human_cases_total) * 100, 2),
        "agent_stage_averages": {
            "diagnosis_confidence": round(float(np.mean(diag_scores)) * 100, 2),
            "retrieval_similarity": round(float(np.mean(ret_scores)) * 100, 2),
            "resolution_completeness": round(float(np.mean(comp_scores)) * 100, 2),
            "final_confidence": round(float(np.mean(final_scores)) * 100, 2)
        },
        "case_results": case_results
    }

    return eval_summary

if __name__ == "__main__":
    report = run_evaluation()
    print("=== AEROASSIST AI EVALUATION REPORT ===")
    print(f"Sample Size: {report['sample_size']}")
    print(f"Category Classification Accuracy: {report['classification_accuracy']}%")
    print(f"Macro F1-Score: {report['macro_f1_score']}%")
    print(f"Retrieval Top-1 Match Rate: {report['retrieval_relevance_rate']}% ({report['retrieval_matched_count']}/{report['retrieval_expected_count']})")
    print(f"Overall Decision Accuracy: {report['overall_decision_accuracy']}%")
    print(f"Solvable Auto-Resolution Coverage: {report['solvable_auto_resolution_rate']}%")
    print(f"Human Support Escalation Capture Rate: {report['human_escalation_capture_rate']}%")
    print("Stage Averages:", report['agent_stage_averages'])
