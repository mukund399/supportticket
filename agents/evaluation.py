# evaluation.py (Updated)
import json
import time
from pydantic import BaseModel, Field
from pydantic_ai import Agent
import statistics

SLEEP_INTERVAL_SECONDS = 10 # Sleep interval for LLM-as-judge calls

# --- LLM-as-Judge Model and Agent () ---
class SolverEvaluationScore(BaseModel):
    relevance: int = Field(description="Score 1-5. How relevant is the output to the original ticket?", ge=1, le=5)
    clarity: int = Field(description="Score 1-5. Is the output clear and easy to understand?", ge=1, le=5)
    actionability: int = Field(description="Score 1-5. Can a human act on this output?", ge=1, le=5)

EVALUATOR_AGENT = Agent(
    'google-gla:gemini-2.0-flash',
    output_type=SolverEvaluationScore,
    system_prompt="You are an expert quality assurance lead. Your sole task is to evaluate the generated output from another AI agent based on the original user ticket. Score the agent's output strictly on a scale of 1 to 5 for each of the provided criteria. Your response MUST be ONLY the JSON object."
)

def run_solver_evaluator(ticket: dict, solver_output: dict) -> SolverEvaluationScore | None:
    # ... (This function is unchanged)
    print("    -> [Evaluator] Grading solver output...")
    prompt = f"Based on the Original Ticket below, please evaluate the provided Agent Output.\n\n--- ORIGINAL TICKET ---\n{ticket}\n\n--- AGENT OUTPUT (to be evaluated) ---\n{solver_output}"
    try:
        result = EVALUATOR_AGENT.run_sync(prompt)
        print("    -> [Evaluator] Grading complete.")
        return result.output
    except Exception as e:
        print(f"    -> [Evaluator] Error during grading: {e}")
        return None

def calculate_metrics(results: list[dict], evaluate_with_llm: bool) -> dict:
    """Calculates evaluation metrics for both the router and solver agents."""
    total_tickets = len(results)
    if total_tickets == 0: return {}

    # --- Router Metrics () ---
    total_processing_time = sum(r.get("processing_time_seconds", 0) for r in results)
    average_processing_time = total_processing_time / total_tickets if total_tickets > 0 else 0
    correctly_routed, routing_attempts = 0, 0
    correctly_urgent, urgency_attempts = 0, 0

    # --- NEW: Counters for Team Assignment ---
    correctly_assigned_team, team_assignment_attempts = 0, 0

    for r in results:
        # Router accuracy calculation
        if r.get("router_output") != "ROUTING FAILED":
            gt_cat = r.get("original_ticket", {}).get("ground_truth_category")
            if gt_cat:
                routing_attempts += 1
                if gt_cat.lower() == r["router_output"].get("category", "").lower():
                    correctly_routed += 1
            gt_urg = r.get("original_ticket", {}).get("ground_truth_urgency")
            if gt_urg:
                urgency_attempts += 1
                if gt_urg.lower() == r["router_output"].get("urgency", "").lower():
                    correctly_urgent += 1

        # --- THIS IS THE FIX ---
        # Solver team assignment accuracy calculation
        solver_output = r.get("solver_output", {})
        if solver_output.get("status") == "SUCCESS":
            gt_team = r.get("original_ticket", {}).get("ground_truth_team")
            if gt_team:
                team_assignment_attempts += 1
                ai_team = solver_output.get("data", {}).get("assigned_team", "")
                if gt_team.lower() == ai_team.lower():
                    correctly_assigned_team += 1

    # --- Metric Calculations (Updated) ---
    routing_accuracy = (correctly_routed / routing_attempts) * 100 if routing_attempts > 0 else 0
    urgency_accuracy = (correctly_urgent / urgency_attempts) * 100 if urgency_attempts > 0 else 0
    team_assignment_accuracy = (correctly_assigned_team / team_assignment_attempts) * 100 if team_assignment_attempts > 0 else 0

    successful_solves = sum(1 for r in results if r.get("solver_output", {}).get("status") == "SUCCESS")
    solver_success_rate = (successful_solves / total_tickets) * 100 if total_tickets > 0 else 0

    metrics = {
        "overall_performance": {
            "total_tickets_processed": total_tickets,
            "average_processing_time_seconds": f"{average_processing_time:.2f}",
        },
        "router_evaluation": {
            "routing_accuracy_percent": f"{routing_accuracy:.2f}% ({correctly_routed}/{routing_attempts})",
            "urgency_accuracy_percent": f"{urgency_accuracy:.2f}% ({correctly_urgent}/{urgency_attempts})",
        },
        "solver_evaluation": {
            "solver_success_rate_percent": f"{solver_success_rate:.2f}%",
            # NEW: Add the team assignment accuracy metric
            "team_assignment_accuracy_percent": f"{team_assignment_accuracy:.2f}% ({correctly_assigned_team}/{team_assignment_attempts})",
        }
    }

    # --- LLM-as-Judge Evaluation (if enabled) ---
    if evaluate_with_llm:
        print("\n================== RUNNING LLM-AS-JUDGE EVALUATION ==================")
        llm_eval_scores = {"relevance": [], "clarity": [], "actionability": []}
        successful_solves = [r for r in results if r.get("solver_output", {}).get("status") == "SUCCESS"]

        for result in successful_solves:
            eval_score = run_solver_evaluator(result["original_ticket"], result["solver_output"])
            if eval_score:
                llm_eval_scores["relevance"].append(eval_score.relevance)
                llm_eval_scores["clarity"].append(eval_score.clarity)
                llm_eval_scores["actionability"].append(eval_score.actionability)
                print(f"Sleeping for {SLEEP_INTERVAL_SECONDS} seconds...")
                time.sleep(SLEEP_INTERVAL_SECONDS)

        if successful_solves:
            metrics["solver_evaluation"]["llm_as_judge_metrics"] = {
                "evaluations_performed": len(llm_eval_scores["relevance"]),
                "avg_relevance_score": f"{statistics.mean(llm_eval_scores['relevance']):.2f} / 5",
                "avg_clarity_score": f"{statistics.mean(llm_eval_scores['clarity']):.2f} / 5",
                "avg_actionability_score": f"{statistics.mean(llm_eval_scores['actionability']):.2f} / 5",
            }

    return metrics
