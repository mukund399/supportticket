# router.py
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from pydantic_ai import Agent
from enum import Enum
from google.api_core import exceptions

# --- Data Models () ---
class TicketCategory(Enum):
    BUGS = "BUGS"
    QUERY = "QUERY"
    REQUEST = "REQUEST"
    SECURITY = "SECURITY"
    CORRECTNESS = "CORRECTNESS"
    MISCELLANEOUS = "MISCELLANEOUS"

class UrgencyLevel(Enum):
    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"

class RoutingSlip(BaseModel):
    category: TicketCategory = Field(description="The single best category for the ticket based on detailed definitions.")
    urgency: UrgencyLevel = Field(description="The urgency of the ticket, rated as High, Medium, or Low.")
    summary: str = Field(description="A one-sentence summary of the ticket's content.")

# --- Router Agent Definition () ---
load_dotenv()
_ROUTER_AGENT = Agent(
    'google-gla:gemini-1.5-flash', # Or your preferred model
    output_type=RoutingSlip,
    system_prompt="""
    You are a specialized API for support ticket analysis. Your sole purpose is to analyze a user's support ticket and return a single, raw JSON object based on the provided 'RoutingSlip' schema.

    Adhere to the following rules without exception:
    1.  Your response MUST be a single, valid JSON object.
    2.  Do not add markdown backticks (```json), conversational text, or explanations. Your output must begin with '{' and end with '}'.

    --- TicketCategory Field Definitions ---
    Use the following criteria to determine the 'category' field value. Choose the single most appropriate category:

    - "BUGS": The user reports that a feature, component, or the product itself is broken, not working as expected, producing errors, or is unavailable. This includes login failures, crashes, non-functional buttons, incorrect data processing, system outages, API errors (e.g., "I can't log in," "The export feature gives an error 500," "The site is down," "API returns unexpected data or fails"). This category is for when something is functionally wrong.

    - "QUERY": The user is asking a "how-to" question, seeking information or clarification about existing features, pricing, account management, product capabilities, or understanding documentation. They are not reporting something broken but rather seeking guidance, explanation, or information (e.g., "How do I change my password?," "What are the limits for API usage?," "Where can I find my invoices?," "Can you explain this part of the documentation?").

    - "REQUEST": The user is suggesting a new feature, an improvement to an existing feature, a change in product behavior, or an integration. They are asking for something that doesn't currently exist or works differently from how they'd like (e.g., "It would be great if you added dark mode," "Can you integrate with Salesforce?," "Please increase the file upload limit," "I wish this button did X instead of Y").

    - "SECURITY": The user reports a security vulnerability, suspicious activity, potential data breach, unauthorized access, or has concerns directly related to account or platform security (e.g., "I think my account was hacked," "Your API exposes sensitive data in responses," "Suspicious login attempt from an unknown IP," "Cross-site scripting vulnerability found").

    - "CORRECTNESS": The user points out a factual error, typo, broken link, or outdated information in documentation, UI text, reports, or other static content provided by the product/service. This is for errors in content, not functional software bugs (e.g., "There's a typo on your pricing page," "The help article for feature X is outdated," "The link to terms of service is broken").

    - "MISCELLANEOUS": Use this category **sparingly and only as a last resort**. Assign this if the ticket's primary purpose does not clearly fit into any of the other defined categories, is highly ambiguous even after careful reading, or is general feedback/commentary not actionable as a bug, query, or request (e.g., non-specific complaints without actionable details, vague compliments, or rants that don't describe a specific problem).
        **Important: Do NOT use "MISCELLANEOUS" if the ticket describes a broken feature (that's "BUGS"), asks a clear question (that's "QUERY"), or requests a new feature (that's "REQUEST").** Prioritize specific categories over "MISCELLANEOUS".

    --- Urgency Field Definitions ---
    Use the following criteria to determine the 'urgency' field value:
    - "High": The user is completely blocked from using a critical function, reports a significant security vulnerability, indicates actual data loss, or a core service is down. (e.g., cannot log in, critical feature is non-functional, production system outage, PII exposure).
    - "Medium": A core feature is significantly degraded or unreliable, but a workaround might exist, or the impact is not system-wide. The user's workflow is notably impacted but not completely stopped. (e.g., slow performance on a key feature, intermittent errors, a non-critical feature is broken).
    - "Low": The user has a general question, is making a feature request, reporting a cosmetic issue/typo that doesn't affect functionality, or a minor bug with an easy workaround. (e.g., "How do I...?", "Request for new report format", "Small UI misalignment", "Typo in docs").
    """
)

def run_router(ticket: dict) -> RoutingSlip | None:
    """Processes a ticket to determine its category, urgency, and a summary."""
    print(f"-> [Router] Analyzing ticket: {ticket.get('ticket_id', 'N/A')}")
    prompt_content = (
        f"Ticket ID: {ticket.get('ticket_id', 'N/A')}\n"
        f"Customer Tier: {ticket.get('customer_tier', 'N/A')}\n"
        f"Subject: {ticket.get('subject', '')}\n"
        f"Message: {ticket.get('message', '')}\n"
        f"Previous Tickets: {ticket.get('previous_tickets', 0)}\n"
        f"Monthly Revenue: {ticket.get('monthly_revenue', 0)}\n"
        f"Account Age (Days): {ticket.get('account_age_days', 0)}\n\n"
        "Please analyze and route this ticket based on the schema and definitions provided in your system instructions."
    )

    try:
        # Assuming _ROUTER_AGENT.run_sync can take a more structured prompt
        # If it only takes a simple string, you might need to concatenate,
        # but modern agents often handle structured inputs or rely heavily on system prompt.
        result = _ROUTER_AGENT.run_sync(prompt_content)
        slip = result.output
        print(f"-> [Router] Analysis complete for {ticket.get('ticket_id', 'N/A')}. Category: {slip.category.value}, Urgency: {slip.urgency.value}")
        return slip
    except exceptions.ResourceExhausted as e:
        print(f"-> [Router] FAILED for {ticket.get('ticket_id', 'N/A')}: Rate limit exceeded (429). Skipping ticket. Error: {e.message if hasattr(e, 'message') else e}")
        return None
    except Exception as e:
        if "Content field missing" in str(e) or "MALFORMED_FUNCTION_CALL" in str(e) or "Invalid JSON" in str(e):
             print(f"-> [Router] FAILED for {ticket.get('ticket_id', 'N/A')}: Model returned malformed data. Skipping ticket. Error: {e}")
        else:
            print(f"-> [Router] FAILED for {ticket.get('ticket_id', 'N/A')}: An unexpected error occurred. Skipping ticket. Error: {e}")
        return None
