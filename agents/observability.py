"""
observability.py

LangSmith Observability & Clinical Explainability Bridge for HealthOS.
Provides transparent tracing of:
1. ToxicBERT safety guardrail decisions & scores
2. SLM semantic entity extraction & intent classification
3. Clinical triage department mapping & ambiguity resolution
4. Dynamic state machine & dependency walks
5. Clinical Audit Cards & consultation outcomes
"""

import os
import atexit
from typing import Any, Callable, Dict, Optional

# Load .env if present
try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass

# If no API key is provided, disable LangSmith tracing to prevent warnings during offline/local testing
_api_key = os.getenv("LANGCHAIN_API_KEY", "").strip()
if not _api_key:
    os.environ["LANGCHAIN_TRACING_V2"] = "false"

try:
    from langsmith import traceable, get_current_run_tree, Client
    _client_cls = Client
except ImportError:
    _client_cls = None
    # Graceful fallback no-op decorator if langsmith is not installed or import fails
    def traceable(*args, **kwargs):
        def decorator(fn):
            return fn
        if len(args) == 1 and callable(args[0]):
            return args[0]
        return decorator

    def get_current_run_tree():
        return None

_client_instance = None


def get_client():
    """Returns or initializes the singleton LangSmith client."""
    global _client_instance
    if _client_instance is None and is_tracing_active() and _client_cls is not None:
        try:
            _client_instance = _client_cls()
        except Exception:
            _client_instance = None
    return _client_instance


def flush_traces() -> None:
    """Flushes any pending runs in the queue to LangSmith cloud."""
    client = get_client()
    if client is not None:
        try:
            client.flush()
        except Exception:
            pass


atexit.register(flush_traces)


def is_tracing_active() -> bool:
    """Returns True if LangSmith tracing is currently enabled and configured with an API key."""
    return (
        os.getenv("LANGCHAIN_TRACING_V2", "false").lower() in ("true", "1")
        and bool(os.getenv("LANGCHAIN_API_KEY", "").strip())
    )


def get_project_name() -> str:
    """Returns the configured LangSmith project name or default."""
    return os.getenv("LANGCHAIN_PROJECT", "HealthOS-Clinical-Observability")


def attach_clinical_audit_metadata(schema: Dict[str, Any], extra: Optional[Dict[str, Any]] = None) -> None:
    """
    Attaches clinical explainability metadata, triage confidence, and
    the formatted audit card to the active LangSmith trace tree.
    """
    try:
        run = get_current_run_tree()
        if not run:
            return

        dept_sec = schema.get("department_section", {})
        metadata = {
            "task": schema.get("task"),
            "stage": schema.get("stage"),
            "assigned_department": dept_sec.get("department"),
            "confidence_score": dept_sec.get("confidence"),
            "is_ambiguous": dept_sec.get("is_ambiguous", False),
            "clinical_reasoning": dept_sec.get("reasoning"),
            "chief_complaints": schema.get("symptom_section", {}).get("symptoms", []),
            "booking_confirmed": schema.get("booking_section", {}).get("booking_confirmed", False),
        }

        # Include formatted clinical audit card
        try:
            from state_schema import format_clinical_audit
            metadata["clinical_audit_card"] = format_clinical_audit(schema)
        except Exception:
            try:
                from agents.state_schema import format_clinical_audit
                metadata["clinical_audit_card"] = format_clinical_audit(schema)
            except Exception:
                pass

        if extra:
            metadata.update(extra)

        run.add_metadata(metadata)
    except Exception:
        # Observability logging should never crash the clinical workflow
        pass
