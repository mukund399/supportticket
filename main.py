# main.py
import json
from dotenv import load_dotenv
import os
import time
from agents.router import run_router
from agents.orchestrator import route_to_solver
from agents.evaluation import calculate_metrics

INPUT_FILE = "./evaluation/tickets_mini.json"
OUTPUT_FILE = "results.json"
EVALUATION_FILE = "evaluation_results.json"
BATCH_SIZE = 3
SLEEP_INTERVAL_SECONDS = 30
EVALUATE_SOLVER_QUALITY_WITH_LLM = False # Keep this false for now

def create_batches(data: list, size: int) -> list:
    return [data[i:i + size] for i in range(0, len(data), size)]

def main():
    """Main application entry point to process tickets from a JSON file."""
    load_dotenv()
    if not os.getenv("GOOGLE_API_KEY"):
        print("Error: GOOGLE_API_KEY environment variable not set.")
        return

    try:
        with open(INPUT_FILE, "r") as f:
            tickets_to_process = json.load(f)
        print(f"Found {len(tickets_to_process)} tickets in '{INPUT_FILE}'.")
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Error loading '{INPUT_FILE}': {e}")
        return

    all_results = []
    ticket_batches = create_batches(tickets_to_process, BATCH_SIZE)
    num_batches = len(ticket_batches)
    print(f"Processing tickets in {num_batches} batches of up to {BATCH_SIZE}.")

    for i, batch in enumerate(ticket_batches):
        print(f"\n==================== PROCESSING BATCH {i + 1} of {num_batches} ====================")
        for ticket in batch:
            print(f"\n----- Processing Ticket: {ticket.get('ticket_id', 'N/A')} -----")
            start_time = time.time()
            
            # --- THIS IS THE FIX ---
            # Create a clean copy of the ticket for processing, removing ALL ground truth fields.
            ticket_for_processing = ticket.copy()
            ticket_for_processing.pop("ground_truth_category", None)
            ticket_for_processing.pop("ground_truth_urgency", None)
            ticket_for_processing.pop("ground_truth_team", None) # Remove the new team field

            routing_slip = run_router(ticket_for_processing)
            if routing_slip:
                final_result = route_to_solver(ticket_for_processing, routing_slip)
                record = {
                    "original_ticket": ticket, # Save the original ticket with ground truth
                    "router_output": routing_slip.model_dump(mode='json'),
                    "solver_output": final_result
                }
            else:
                record = {"original_ticket": ticket, "router_output": "ROUTING FAILED", "solver_output": None}

            record["processing_time_seconds"] = time.time() - start_time
            all_results.append(record)

        print(f"\n==================== BATCH {i + 1} COMPLETE ====================")
        if i < num_batches - 1:
            print(f"Sleeping for {SLEEP_INTERVAL_SECONDS} seconds...")
            time.sleep(SLEEP_INTERVAL_SECONDS)

    with open(OUTPUT_FILE, "w") as f:
        json.dump(all_results, f, indent=2)
    print(f"\n===================================================================")
    print(f"Processing complete. All results saved to '{OUTPUT_FILE}'.")

    print("\n========================= EVALUATION METRICS ========================")
    metrics = calculate_metrics(all_results, evaluate_with_llm=EVALUATE_SOLVER_QUALITY_WITH_LLM)
    if metrics:
        print(json.dumps(metrics, indent=2))
        with open(EVALUATION_FILE, "w") as f:
            json.dump(metrics, f, indent=2)
        print(f"\nEvaluation metrics saved to '{EVALUATION_FILE}'.")
    else:
        print("No tickets processed, no metrics calculated.")

if __name__ == "__main__":
    main()
