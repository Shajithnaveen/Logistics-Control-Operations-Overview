from datetime import datetime
from typing import Dict, List, Any, Optional
from app.optimizer.constraints import ConstraintChecker

class OverrideAuditLogService:
    def __init__(self):
        self.logs: List[Dict[str, Any]] = []
        self._counter = 1

    def get_logs(self) -> List[Dict[str, Any]]:
        return self.logs

    def process_override(self, 
                         user: str,
                         role: str,
                         action_type: str,
                         vehicle_id: str,
                         vehicle: Dict[str, Any],
                         route_stops: List[Dict[str, Any]],
                         original_assignment: str,
                         new_assignment: str,
                         reason: str,
                         constraint_affected: str,
                         confirm_hard_override: bool = False) -> Dict[str, Any]:
        """
        Validates and logs a dispatcher manual override.
        Rejects anonymous overrides or hard constraint violations without explicit confirmation + reason.
        """
        # Rule: Anonymous or unauthorized override prohibited
        if not user or user.strip().lower() in ["anonymous", "unknown", "none"]:
            return {
                "success": False,
                "error": "Unauthorized override prohibited. Valid dispatcher identity required.",
                "safe_assignment": False
            }

        # Evaluate constraints on the new proposed route stops
        hard_v, soft_v, details = ConstraintChecker.evaluate_route(vehicle, route_stops)
        
        has_hard_violations = len(hard_v) > 0
        
        # Rule: Hard constraint override requires explicit confirmation and mandatory non-empty reason
        if has_hard_violations and not confirm_hard_override:
            return {
                "success": False,
                "error": f"HARD CONSTRAINT VIOLATION: {'; '.join(hard_v)}. Explicit confirmation required to force override.",
                "requires_confirmation": True,
                "hard_violations": hard_v,
                "safe_assignment": False
            }

        if has_hard_violations and (not reason or len(reason.strip()) < 5):
            return {
                "success": False,
                "error": "Mandatory typed reason (at least 5 characters) required to override hard constraints.",
                "requires_confirmation": True,
                "hard_violations": hard_v,
                "safe_assignment": False
            }

        override_record = {
            "override_id": f"OVR-{self._counter:04d}",
            "user": user,
            "role": role,
            "timestamp": datetime.now().isoformat(),
            "action_type": action_type,
            "vehicle_id": vehicle_id,
            "original_assignment": original_assignment,
            "new_assignment": new_assignment,
            "reason": reason if reason else "Dispatcher operational override",
            "constraint_affected": constraint_affected or ("Hard Constraint: " + "; ".join(hard_v) if has_hard_violations else "Soft Constraint"),
            "hard_constraint_overridden": has_hard_violations,
            "status": "APPROVED_OVERRIDE" if has_hard_violations else "SUCCESS",
            "route_details": details
        }
        
        self.logs.insert(0, override_record)
        self._counter += 1
        
        return {
            "success": True,
            "override": override_record,
            "hard_violations": hard_v,
            "soft_violations": soft_v,
            "safe_assignment": len(hard_v) == 0,
            "details": details
        }

override_service = OverrideAuditLogService()
