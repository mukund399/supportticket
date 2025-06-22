# solvers.py (Updated)
from pydantic import BaseModel, Field
from pydantic_ai import Agent
# --- NEW: Import Enum for creating a strict category list ---
from enum import Enum
from google.api_core import exceptions

# --- NEW: Define the strict list of teams the AI can assign ---
class AssignedTeam(str, Enum):
    """Enumeration for the possible team assignments."""
    FRONTEND = "Frontend"
    BACKEND = "Backend"
    SECURITY = "Security"
    UI_UX = "UI/UX"
    CUSTOMER_SUPPORT = "Customer Support"
    DOCUMENTATION = "Documentation"
    GENERAL_TRIAGE = "General Triage"

# --- Pydantic Models for Solver Outputs (Updated) ---
# We add the `assigned_team` field to every model.
class BugReport(BaseModel):
    title: str = Field(description="Generate a descriptive title suitable for a bug ticket. It should clearly state the core problem.")
    reproduction_steps: list[str] = Field(description="Create a list of numbered, easy-to-follow steps that an engineer can use to replicate the bug.")
    severity: str = Field(description="Categorize the severity. Must be one of: 'Critical', 'High', 'Medium', or 'Low'.")
    assigned_team: AssignedTeam = Field(
        description="Analyze the bug's title and reproduction steps. Determine if the root cause likely lies in **server-side logic, API functionality, database interactions, data processing, authentication mechanisms, or core system performance (e.g., 500 errors, login failures not related to UI, system crashes).** If the issue clearly points to these backend components, assign to the **'Backend'** team. For visual or user interface bugs specific to the client-side, assign 'Frontend' or 'UI/UX'. **Only assign to 'General Triage' if the problem domain is highly ambiguous and lacks clear technical indicators even after analyzing the title and steps.** Choose accurately from the available team options."
    )

class DraftResponse(BaseModel):
    customer_facing_response: str = Field(description="Write a response to the customer that is helpful, friendly, and empathetic, addressing their issue directly.")
    is_resolved: bool = Field(description="Determine if the drafted response fully resolves the user's question. Use 'true' if it does, 'false' if it does not.")
    assigned_team: AssignedTeam = Field(
        description="Based on the customer's original query and the nature of the drafted response, determine which internal team is responsible for the subject matter. If the issue discussed relates to **server functionality, data, APIs, or system integrations, consider 'Backend'.** If it's about account help, billing, or general guidance, consider 'Customer Support'. Select the most relevant team from the provided options. **Avoid 'General Triage' if a more specific team can be identified.**"
    )

class FeatureRequestReport(BaseModel):
    feature_summary: str = Field(description="Summarize the user's core feature request in one or two sentences.")
    user_goal: str = Field(description="Explain the underlying goal or problem the user is trying to solve with this new feature.")
    business_impact: str = Field(description="Categorize the potential business value. Must be one of: 'High', 'Medium', or 'Low'.")
    assigned_team: AssignedTeam = Field(
        description="Consider the feature_summary and user_goal. If the request involves **significant data manipulation, new API development, core architectural changes, system integrations, or complex backend logic,** assign to the **'Backend'** team. For features primarily focused on user interface changes or visual enhancements, assign 'Frontend' or 'UI/UX'. Assign the team that would primarily own the development and maintenance of this feature. **'General Triage' is inappropriate if the feature's technical domain (e.g., backend vs. frontend) is reasonably clear.** Choose from the available team options."
    )

class SecurityAlert(BaseModel):
    alert_summary: str = Field(description="Provide a concise summary of the potential security vulnerability reported in the ticket.")
    severity: str = Field(description="Categorize the security severity. Must be one of: 'Critical', 'High', 'Medium', or 'Low'.")
    recommended_action: str = Field(description="State the single most important next step to take immediately. Example: 'Escalate to security team' or 'Revoke API key'.")
    assigned_team: AssignedTeam = Field(
        description="Given the alert_summary and severity, assign to the **'Security'** team for incidents like unauthorized access, direct vulnerability exploitation, or policy violations. If the vulnerability is specifically identified within a **backend system (e.g., an API flaw, database vulnerability, server misconfiguration)** and the 'Security' team's role is primarily investigation/oversight before handoff, consider if 'Backend' might also be relevant for remediation, but prioritize **'Security'** for initial assignment of security-flagged issues. **Avoid 'General Triage' for clear security alerts.** Choose from the available team options."
    )

class CorrectnessReview(BaseModel):
    identified_error: str = Field(description="Isolate and describe the specific factual or textual error found (e.g., a typo in the UI, an incorrect number in a report).")
    suggested_correction: str = Field(description="Provide the exact text or value that would correct the identified error.")
    assigned_team: AssignedTeam = Field(
        description="Based on the identified_error, assign the team responsible for that content or system. If the error is in **backend-generated data, system calculations, API response content, or server-side configurations,** assign to the **'Backend'** team. For UI text errors, assign 'Frontend' or 'UI/UX'; for documentation errors, assign 'Documentation'. **Do not use 'General Triage' if the source of the error can be pinpointed to a specific domain.** Choose from the available team options."
    )

class GeneralTriage(BaseModel):
    triage_summary: str = Field(description="Summarize the ticket's content, noting its ambiguity or lack of a clear, actionable request.")
    recommended_next_step: str = Field(description="Determine the most logical next action for this unclear ticket. Example: 'Request clarification from the user' or 'Forward to Tier 2 support'.")
    assigned_team: AssignedTeam = Field(
        description="This ticket has been classified as requiring general triage due to initial ambiguity. The `assigned_team` should typically be **'General Triage'** itself, or **'Customer Support'** if the `recommended_next_step` is direct user interaction for clarification. **Only assign to a specialized technical team (like 'Backend') from within this GeneralTriage classification if the `triage_summary` and `recommended_next_step` *now very clearly and unequivocally* point to them *despite* the initial ambiguity that led to this overall ticket type.** The primary goal of this class is to handle initially unclear tickets."
    )

# --- Specialist Solver Agents () ---
_BUG_SOLVER_AGENT = Agent('google-gla:gemini-1.5-flash', output_type=BugReport, system_prompt="You are an expert software developer creating a bug report for Jira.")
_QUERY_SOLVER_AGENT = Agent('google-gla:gemini-1.5-flash', output_type=DraftResponse, system_prompt="You are a friendly customer support agent drafting a response.")
_REQUEST_SOLVER_AGENT = Agent('google-gla:gemini-1.5-flash', output_type=FeatureRequestReport, system_prompt="You are a product manager analyzing a new feature request.")
_SECURITY_SOLVER_AGENT = Agent('google-gla:gemini-1.5-flash', output_type=SecurityAlert, system_prompt="You are a security analyst creating a high-priority alert.")
_CORRECTNESS_SOLVER_AGENT = Agent('google-gla:gemini-1.5-flash', output_type=CorrectnessReview, system_prompt="You are a QA engineer noting a minor correctness issue.")
_MISC_SOLVER_AGENT = Agent('google-gla:gemini-1.5-flash', output_type=GeneralTriage, system_prompt="You are a support lead triaging an unclear ticket.")


# --- Public Functions for Solvers () ---
# No changes are needed here because the logic is generic.

def _run_solver(agent: Agent, ticket_data: dict, summary: str, model_name: str):
    """Generic function to run any solver agent and handle errors."""
    print(f"    -> [Solver] Generating {model_name}...")
    prompt = f"Based on the ticket and summary, generate the {model_name}.\nTICKET: {ticket_data}\nSUMMARY: {summary}"
    try:
        result = agent.run_sync(prompt)
        print(f"    -> [Solver] {model_name} generated successfully.")
        return result.output
    except exceptions.ResourceExhausted as e:
        print(f"    -> [Solver] FAILED: Rate limit exceeded (429). Skipping solver. Error: {e.message}")
        return None
    except Exception as e:
        if "Content field missing" in str(e) or "MALFORMED_FUNCTION_CALL" in str(e):
             print(f"    -> [Solver] FAILED: Model returned malformed data. Skipping solver. Error: {e}")
        else:
            print(f"    -> [Solver] FAILED: An unexpected error occurred. Skipping solver. Error: {e}")
        return None

def generate_bug_report(ticket_data: dict, summary: str):
    return _run_solver(_BUG_SOLVER_AGENT, ticket_data, summary, "BugReport")
def generate_draft_response(ticket_data: dict, summary: str):
    return _run_solver(_QUERY_SOLVER_AGENT, ticket_data, summary, "DraftResponse")
def generate_feature_request(ticket_data: dict, summary: str):
    return _run_solver(_REQUEST_SOLVER_AGENT, ticket_data, summary, "FeatureRequestReport")
def generate_security_alert(ticket_data: dict, summary: str):
    return _run_solver(_SECURITY_SOLVER_AGENT, ticket_data, summary, "SecurityAlert")
def generate_correctness_review(ticket_data: dict, summary: str):
    return _run_solver(_CORRECTNESS_SOLVER_AGENT, ticket_data, summary, "CorrectnessReview")
def generate_general_triage(ticket_data: dict, summary: str):
    return _run_solver(_MISC_SOLVER_AGENT, ticket_data, summary, "GeneralTriage")
