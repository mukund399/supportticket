# orchestrator.py
from pydantic import BaseModel
from .router import RoutingSlip, TicketCategory
from .solvers import (
    generate_bug_report, generate_draft_response, generate_feature_request,
    generate_security_alert, generate_correctness_review, generate_general_triage
)

def _process_solver_output(solver_name: str, result_obj: BaseModel | None) -> dict:
    """Helper to format the solver output for JSON logging."""
    if result_obj:
        # --- FIX: Use mode='json' here as well for consistency ---
        return {"status": "SUCCESS", "solver": solver_name, "data": result_obj.model_dump(mode='json')}
    return {"status": "FAILURE", "solver": solver_name, "data": "Could not generate valid structured output."}

def solve_bug_ticket(ticket: dict, slip: RoutingSlip) -> dict:
    print(f"--> [Orchestrator] Routed to: Bug Solver")
    result = generate_bug_report(ticket, slip.summary)
    return _process_solver_output("BugSolver", result)

def solve_query_ticket(ticket: dict, slip: RoutingSlip) -> dict:
    print(f"--> [Orchestrator] Routed to: Query Solver")
    result = generate_draft_response(ticket, slip.summary)
    return _process_solver_output("QuerySolver", result)

def solve_request_ticket(ticket: dict, slip: RoutingSlip) -> dict:
    print(f"--> [Orchestrator] Routed to: Feature Request Solver")
    result = generate_feature_request(ticket, slip.summary)
    return _process_solver_output("FeatureRequestSolver", result)

def solve_security_ticket(ticket: dict, slip: RoutingSlip) -> dict:
    print(f"--> [Orchestrator] Routed to: Security Solver")
    result = generate_security_alert(ticket, slip.summary)
    return _process_solver_output("SecuritySolver", result)

def solve_correctness_ticket(ticket: dict, slip: RoutingSlip) -> dict:
    print(f"--> [Orchestrator] Routed to: Correctness Solver")
    result = generate_correctness_review(ticket, slip.summary)
    return _process_solver_output("CorrectnessSolver", result)

def solve_misc_ticket(ticket: dict, slip: RoutingSlip) -> dict:
    print(f"--> [Orchestrator] Routed to: Miscellaneous Solver")
    result = generate_general_triage(ticket, slip.summary)
    return _process_solver_output("MiscSolver", result)

_HANDLER_MAP = {
    TicketCategory.BUGS: solve_bug_ticket,
    TicketCategory.QUERY: solve_query_ticket,
    TicketCategory.REQUEST: solve_request_ticket,
    TicketCategory.SECURITY: solve_security_ticket,
    TicketCategory.CORRECTNESS: solve_correctness_ticket,
    TicketCategory.MISCELLANEOUS: solve_misc_ticket,
}

def route_to_solver(ticket: dict, routing_slip: RoutingSlip) -> dict:
    """Takes a routing_slip and calls the appropriate solver function."""
    print(f"--> [Orchestrator] Routing ticket with category '{routing_slip.category.value}'...")
    handler_function = _HANDLER_MAP.get(routing_slip.category, solve_misc_ticket)
    result = handler_function(ticket, routing_slip)
    return result
