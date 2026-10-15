import os
import re
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
from app.core.config import settings

class SimulatedJiraIssue:
    def __init__(
        self,
        key: str,
        summary: str,
        description: str,
        project_key: str,
        issue_type: str,
        priority: str,
        status: str = "To Do",
        assignee_name: Optional[str] = None,
        reporter_name: Optional[str] = "Flight Dispatcher",
        idempotency_key: Optional[str] = None,
        created_at: Optional[str] = None
    ):
        self.key = key
        self.summary = summary
        self.description = description
        self.project_key = project_key
        self.issue_type = issue_type
        self.priority = priority
        self.status = status
        self.assignee_name = assignee_name
        self.reporter_name = reporter_name
        self.idempotency_key = idempotency_key
        self.comments: List[Dict[str, Any]] = []
        self.url = f"{settings.JIRA_BASE_URL.rstrip('/')}/browse/{key}"
        now_str = datetime.now(timezone.utc).isoformat()
        self.created_at = created_at or now_str
        self.updated_at = now_str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.key,
            "key": self.key,
            "url": self.url,
            "project_key": self.project_key,
            "summary": self.summary,
            "description": self.description,
            "issue_type": self.issue_type,
            "priority": self.priority,
            "status": self.status,
            "assignee_name": self.assignee_name,
            "reporter_name": self.reporter_name,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "comments": self.comments,
            "transitions": self.get_available_transitions(),
            "idempotency_key": self.idempotency_key
        }

    def get_available_transitions(self) -> List[Dict[str, str]]:
        all_transitions = {
            "To Do": [
                {"id": "21", "name": "Start Progress", "to_status": "In Progress"},
                {"id": "31", "name": "Move to Review", "to_status": "In Review"},
                {"id": "41", "name": "Close / Resolve", "to_status": "Done"}
            ],
            "In Progress": [
                {"id": "11", "name": "Stop Progress", "to_status": "To Do"},
                {"id": "31", "name": "Submit for Review", "to_status": "In Review"},
                {"id": "41", "name": "Mark as Done", "to_status": "Done"}
            ],
            "In Review": [
                {"id": "21", "name": "Return to In Progress", "to_status": "In Progress"},
                {"id": "41", "name": "Approve & Resolve", "to_status": "Done"},
                {"id": "11", "name": "Reject to Backlog", "to_status": "To Do"}
            ],
            "Done": [
                {"id": "51", "name": "Reopen Issue", "to_status": "To Do"},
                {"id": "21", "name": "Reopen in Progress", "to_status": "In Progress"}
            ]
        }
        return all_transitions.get(self.status, [
            {"id": "21", "name": "Start Progress", "to_status": "In Progress"},
            {"id": "41", "name": "Mark as Done", "to_status": "Done"}
        ])

class SimulatedJiraService:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(SimulatedJiraService, cls).__new__(cls)
            cls._instance.issues: Dict[str, SimulatedJiraIssue] = {}
            cls._instance.idempotency_map: Dict[str, str] = {}
            cls._instance.counter = 200
            cls._instance._seed_default_projects_and_issues()
        return cls._instance

    def _seed_default_projects_and_issues(self):
        self.projects = [
            {
                "id": "10001",
                "key": "AERO",
                "name": "Aero Flight Operations",
                "project_type_key": "software",
                "lead_name": "Chief Pilot Aviation Lead"
            },
            {
                "id": "10002",
                "key": "IT",
                "name": "Airline IT & Avionics Support",
                "project_type_key": "service_desk",
                "lead_name": "Sarah Connor (Lead Support Agent)"
            },
            {
                "id": "10003",
                "key": "BAG",
                "name": "Passenger Baggage & Disruption Claims",
                "project_type_key": "business",
                "lead_name": "Station Ground Controller"
            }
        ]

        seed_data = [
            (
                "AERO-101",
                "ACARS telemetry latency on transcontinental route AA-902",
                "Real-time ACARS beacon telemetry experiences intermittent 45s latency during route handover between waypoint MERIT and WAYNE.",
                "AERO",
                "Task",
                "High",
                "In Progress",
                "Sarah Connor",
                "Capt. James Kirk"
            ),
            (
                "AERO-102",
                "Gate re-assignment notification lag at JFK Terminal 4",
                "Gate changes made under 25 minutes prior to boarding fail to broadcast push updates to passenger mobile apps consistently.",
                "AERO",
                "Bug",
                "Medium",
                "To Do",
                "Alex Rivera",
                "Station Operations"
            ),
            (
                "AERO-103",
                "Runway de-icing telemetry integration with dispatch queue",
                "Implement automated temperature sensor ingest from ground service trucks into central turnaround tracking system.",
                "AERO",
                "Story",
                "Low",
                "Done",
                "Marcus Vance",
                "Ground Crew"
            ),
            (
                "IT-101",
                "Flight disruption auto-rebooking gate timeout after 180s",
                "When European Regulation EC 261 automated re-accommodation pipeline triggers for cancelled flight AA-404, booking engine times out after 180 seconds under peak load.",
                "IT",
                "Bug",
                "Highest",
                "In Progress",
                "Sarah Connor",
                "System Monitoring"
            ),
            (
                "IT-102",
                "Crew roster dispatch synchronization failure during shift change",
                "Pilot and flight attendant duty hour tracking fails to update during 06:00 UTC shift turnover, causing false rest-period violation alerts.",
                "IT",
                "Task",
                "High",
                "To Do",
                "Alex Rivera",
                "Crew Scheduling"
            ),
            (
                "IT-103",
                "IFEC passenger Wi-Fi authentication gateway reconnect issue",
                "Passengers reconnecting after cruise climb altitude change encounter HTTP 502 bad gateway on captive portal.",
                "IT",
                "Task",
                "Medium",
                "Done",
                "Marcus Vance",
                "Avionics Tech"
            ),
            (
                "BAG-101",
                "Lost baggage RFID tag reader calibration at Carousel 3",
                "Baggage container tag scanners fail to record inbound status for transfer bags originating from London Heathrow flight AA-100.",
                "BAG",
                "Task",
                "High",
                "In Review",
                "Station Operations",
                "Emily Watson"
            ),
            (
                "BAG-102",
                "Delayed luggage delivery compensation calculation discrepancy",
                "Baggage claims portal computes domestic tariff allowance instead of Montreal Convention SDR rates on international itineraries.",
                "BAG",
                "Bug",
                "Medium",
                "To Do",
                "Sarah Connor",
                "Passenger Support"
            )
        ]

        for key, summary, desc, proj, itype, prio, st, assignee, reporter in seed_data:
            issue = SimulatedJiraIssue(
                key=key,
                summary=summary,
                description=desc,
                project_key=proj,
                issue_type=itype,
                priority=prio,
                status=st,
                assignee_name=assignee,
                reporter_name=reporter
            )
            issue.comments.append({
                "id": f"comm-{key}-1",
                "author": "Aero Assistant Sync Bot",
                "body": f"Automated synchronization linked issue {key} with flight operations triage system.",
                "created_at": datetime.now(timezone.utc).isoformat()
            })
            self.issues[key] = issue

    def map_priority(self, aero_priority: str) -> str:
        mapping = {
            "P1 Critical": "Highest",
            "P2 High": "High",
            "P3 Medium": "Medium",
            "P4 Low": "Low"
        }
        return mapping.get(aero_priority, aero_priority if aero_priority in ["Highest", "High", "Medium", "Low", "Lowest"] else "Medium")

    def test_connection(self) -> Dict[str, Any]:
        return {
            "success": True,
            "mode": "SIMULATED",
            "user": "Aero Assistant Simulator Agent",
            "email": settings.JIRA_EMAIL,
            "project_key": settings.JIRA_PROJECT_KEY,
            "message": f"Connected to Simulated Jira Cloud instance ({len(self.issues)} active issues across {len(self.projects)} projects).",
            "project_count": len(self.projects)
        }

    def get_projects(self) -> List[Dict[str, Any]]:
        return self.projects

    def get_issues(
        self,
        project_key: Optional[str] = None,
        search: Optional[str] = None,
        status: Optional[str] = None,
        priority: Optional[str] = None,
        jql: Optional[str] = None,
        page: int = 1,
        size: int = 10
    ) -> Dict[str, Any]:
        results = list(self.issues.values())

        # If JQL is provided, parse common JQL syntax (e.g. project = AERO AND status = "In Progress")
        if jql and jql.strip():
            jql_lower = jql.lower()
            proj_match = re.search(r'project\s*=\s*["\']?([a-zA-Z0-9_-]+)["\']?', jql, re.IGNORECASE)
            if proj_match:
                p_val = proj_match.group(1).upper()
                results = [i for i in results if i.project_key == p_val]

            status_match = re.search(r'status\s*=\s*["\']?([^"\'\n]+)["\']?', jql, re.IGNORECASE)
            if status_match:
                s_val = status_match.group(1).lower().strip()
                results = [i for i in results if s_val in i.status.lower()]

            text_match = re.search(r'text\s*~\s*["\']?([^"\'\n]+)["\']?', jql, re.IGNORECASE)
            if text_match:
                t_val = text_match.group(1).lower().strip()
                results = [i for i in results if t_val in i.summary.lower() or t_val in i.description.lower()]
        else:
            if project_key and project_key != "All":
                results = [i for i in results if i.project_key == project_key]

            if status and status != "All":
                results = [i for i in results if i.status.lower() == status.lower()]

            if priority and priority != "All":
                results = [i for i in results if i.priority.lower() == priority.lower()]

            if search and search.strip():
                kw = search.strip().lower()
                results = [
                    i for i in results
                    if kw in i.key.lower() or kw in i.summary.lower() or kw in i.description.lower() or (i.assignee_name and kw in i.assignee_name.lower())
                ]

        total = len(results)
        total_pages = max(1, (total + size - 1) // size)
        start_idx = (page - 1) * size
        end_idx = start_idx + size
        paged_issues = results[start_idx:end_idx]

        return {
            "items": [i.to_dict() for i in paged_issues],
            "total": total,
            "page": page,
            "size": size,
            "pages": total_pages,
            "project_key": project_key
        }

    def get_issue(self, key: str) -> Optional[Dict[str, Any]]:
        issue = self.issues.get(key)
        if not issue:
            return None
        return issue.to_dict()

    def create_issue(
        self,
        summary: str,
        description: str,
        priority: str,
        issue_type: Optional[str] = None,
        project_key: Optional[str] = None,
        assignee: Optional[str] = None,
        idempotency_key: Optional[str] = None
    ) -> Dict[str, Any]:
        # Idempotency check: if key already exists, return existing issue without re-creating
        if idempotency_key and idempotency_key in self.idempotency_map:
            existing_key = self.idempotency_map[idempotency_key]
            existing_issue = self.issues.get(existing_key)
            if existing_issue:
                return {
                    **existing_issue.to_dict(),
                    "idempotency_hit": True
                }

        self.counter += 1
        proj = project_key or settings.JIRA_PROJECT_KEY or "AERO"
        key = f"{proj}-{self.counter}"
        jira_priority = self.map_priority(priority)

        issue = SimulatedJiraIssue(
            key=key,
            summary=summary,
            description=description,
            project_key=proj,
            issue_type=issue_type or settings.JIRA_DEFAULT_ISSUE_TYPE or "Task",
            priority=jira_priority,
            status="To Do",
            assignee_name=assignee or "Unassigned",
            reporter_name="Sarah Connor (Lead Support Agent)",
            idempotency_key=idempotency_key
        )

        self.issues[key] = issue
        if idempotency_key:
            self.idempotency_map[idempotency_key] = key

        return {
            **issue.to_dict(),
            "idempotency_hit": False
        }

    def update_issue(self, key: str, summary: Optional[str] = None, description: Optional[str] = None) -> Optional[Dict[str, Any]]:
        issue = self.issues.get(key)
        if not issue:
            return None
        if summary is not None:
            issue.summary = summary
        if description is not None:
            issue.description = description
        issue.updated_at = datetime.now(timezone.utc).isoformat()
        return issue.to_dict()

    def get_transitions(self, key: str) -> List[Dict[str, str]]:
        issue = self.issues.get(key)
        if not issue:
            return []
        return issue.get_available_transitions()

    def transition_issue(self, key: str, transition_id: str, comment_text: Optional[str] = None) -> Optional[Dict[str, Any]]:
        issue = self.issues.get(key)
        if not issue:
            return None

        # Look up transition
        available = issue.get_available_transitions()
        target = next((t for t in available if t["id"] == transition_id or t["name"].lower() == transition_id.lower()), None)
        if target:
            issue.status = target["to_status"]
        else:
            # Direct status fallback if status name passed
            valid_statuses = ["To Do", "In Progress", "In Review", "Done"]
            for st in valid_statuses:
                if transition_id.lower() in st.lower():
                    issue.status = st
                    break

        if comment_text:
            self.add_comment(key, author="Station Supervisor", comment_text=comment_text)

        issue.updated_at = datetime.now(timezone.utc).isoformat()
        return issue.to_dict()

    def get_comments(self, key: str) -> List[Dict[str, Any]]:
        issue = self.issues.get(key)
        if not issue:
            return []
        return issue.comments

    def add_comment(self, key: str, author: str, comment_text: str) -> Optional[Dict[str, Any]]:
        issue = self.issues.get(key)
        if not issue:
            return None
        new_comm = {
            "id": f"comm-{key}-{len(issue.comments) + 1}",
            "author": author or "Support Agent",
            "body": comment_text,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        issue.comments.append(new_comm)
        issue.updated_at = datetime.now(timezone.utc).isoformat()
        return new_comm
