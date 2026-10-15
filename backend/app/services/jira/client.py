import base64
import time
from typing import Dict, Any, List, Optional
import httpx
from app.core.config import settings
from app.core.logging import logger
from app.services.jira.simulator import SimulatedJiraService

class JiraClientService:
    def __init__(self):
        self.mock_mode = settings.JIRA_MOCK_MODE or not settings.JIRA_ENABLED
        self.simulator = SimulatedJiraService()

    def is_real_cloud_configured(self) -> bool:
        if self.mock_mode or not settings.JIRA_ENABLED:
            return False
        if not settings.JIRA_BASE_URL or "example.atlassian.net" in settings.JIRA_BASE_URL or "your-domain" in settings.JIRA_BASE_URL:
            return False
        if not settings.JIRA_EMAIL or "example.com" in settings.JIRA_EMAIL or "@" not in settings.JIRA_EMAIL:
            return False
        if not settings.JIRA_API_TOKEN or "mock-token" in settings.JIRA_API_TOKEN or "your-jira-api-token" in settings.JIRA_API_TOKEN:
            return False
        return True

    def _get_headers(self) -> Dict[str, str]:
        auth_str = f"{settings.JIRA_EMAIL}:{settings.JIRA_API_TOKEN}"
        encoded_auth = base64.b64encode(auth_str.encode()).decode()
        return {
            "Authorization": f"Basic {encoded_auth}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }

    async def test_connection(self) -> Dict[str, Any]:
        if not self.is_real_cloud_configured():
            sim_res = self.simulator.test_connection()
            if not settings.JIRA_ENABLED:
                sim_res["message"] = "Jira integration currently running in Simulator mode (JIRA_ENABLED=false). Real Jira Cloud credentials can be configured in .env."
            elif self.mock_mode:
                sim_res["message"] = "Jira integration running in Deterministic Simulator mode (JIRA_MOCK_MODE=true)."
            return sim_res

        url = f"{settings.JIRA_BASE_URL.rstrip('/')}/rest/api/3/myself"
        start_time = time.time()
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(url, headers=self._get_headers())
                latency_ms = int((time.time() - start_time) * 1000)
                
                if resp.status_code == 401:
                    return {
                        "success": False,
                        "mode": "REAL_CLOUD",
                        "error": "Authentication failed (401 Unauthorized)",
                        "message": f"Invalid Jira API token or email for {settings.JIRA_EMAIL}. Please verify your Atlassian API token."
                    }
                elif resp.status_code == 403:
                    return {
                        "success": False,
                        "mode": "REAL_CLOUD",
                        "error": "Access forbidden (403 Forbidden)",
                        "message": "Authenticated user does not have permission to access Jira Cloud REST API."
                    }
                
                resp.raise_for_status()
                data = resp.json()

                # Also retrieve project count
                proj_url = f"{settings.JIRA_BASE_URL.rstrip('/')}/rest/api/3/project"
                proj_resp = await client.get(proj_url, headers=self._get_headers())
                proj_count = len(proj_resp.json()) if proj_resp.status_code == 200 and isinstance(proj_resp.json(), list) else 1

                return {
                    "success": True,
                    "mode": "REAL_CLOUD",
                    "user": data.get("displayName"),
                    "email": data.get("emailAddress") or settings.JIRA_EMAIL,
                    "project_key": settings.JIRA_PROJECT_KEY,
                    "project_count": proj_count,
                    "latency_ms": latency_ms,
                    "message": f"Successfully connected to Jira Cloud ({settings.JIRA_BASE_URL}) as {data.get('displayName')} ({latency_ms}ms)."
                }
        except httpx.ConnectError as e:
            logger.error(f"Jira network connection error: {str(e)}")
            return {
                "success": False,
                "mode": "REAL_CLOUD",
                "error": "Network Connection Failure",
                "message": f"Could not reach Jira host at {settings.JIRA_BASE_URL}. Verify internet connectivity and base URL."
            }
        except Exception as e:
            logger.error(f"Jira connectivity test failed: {str(e)}")
            return {
                "success": False,
                "mode": "REAL_CLOUD",
                "error": str(e),
                "message": f"Failed connecting to Jira Cloud at {settings.JIRA_BASE_URL}: {str(e)}"
            }

    async def get_projects(self) -> List[Dict[str, Any]]:
        if not self.is_real_cloud_configured():
            return self.simulator.get_projects()

        url = f"{settings.JIRA_BASE_URL.rstrip('/')}/rest/api/3/project"
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(url, headers=self._get_headers())
                resp.raise_for_status()
                data = resp.json()
                return [
                    {
                        "id": str(p.get("id")),
                        "key": p.get("key"),
                        "name": p.get("name"),
                        "project_type_key": p.get("projectTypeKey", "software"),
                        "lead_name": p.get("lead", {}).get("displayName", "Project Lead"),
                        "avatar_url": p.get("avatarUrls", {}).get("48x48")
                    }
                    for p in data
                ]
        except Exception as e:
            logger.warning(f"Failed to fetch projects from real Jira: {e}. Falling back to simulator projects.")
            return self.simulator.get_projects()

    async def get_issues(
        self,
        project_key: Optional[str] = None,
        search: Optional[str] = None,
        status: Optional[str] = None,
        priority: Optional[str] = None,
        jql: Optional[str] = None,
        page: int = 1,
        size: int = 10
    ) -> Dict[str, Any]:
        if not self.is_real_cloud_configured():
            return self.simulator.get_issues(
                project_key=project_key,
                search=search,
                status=status,
                priority=priority,
                jql=jql,
                page=page,
                size=size
            )

        # Build JQL query for real Jira REST v3
        start_at = (page - 1) * size
        jql_clauses = []
        if jql and jql.strip():
            jql_query = jql.strip()
        else:
            if project_key and project_key != "All":
                jql_clauses.append(f'project = "{project_key}"')
            if status and status != "All":
                jql_clauses.append(f'status = "{status}"')
            if priority and priority != "All":
                jql_clauses.append(f'priority = "{priority}"')
            if search and search.strip():
                jql_clauses.append(f'(text ~ "{search.strip()}" OR key = "{search.strip()}")')
            
            jql_query = " AND ".join(jql_clauses) if jql_clauses else "ORDER BY created DESC"

        url = f"{settings.JIRA_BASE_URL.rstrip('/')}/rest/api/3/search"
        params = {
            "jql": jql_query,
            "startAt": start_at,
            "maxResults": size,
            "fields": "summary,description,status,priority,issuetype,project,assignee,reporter,created,updated"
        }

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                resp = await client.get(url, headers=self._get_headers(), params=params)
                resp.raise_for_status()
                data = resp.json()
                total = data.get("total", 0)
                issues_raw = data.get("issues", [])

                items = []
                for raw in issues_raw:
                    fields = raw.get("fields", {})
                    # Parse ADF or plain description
                    desc_raw = fields.get("description")
                    desc_str = ""
                    if isinstance(desc_raw, str):
                        desc_str = desc_raw
                    elif isinstance(desc_raw, dict):
                        # Simple ADF text extractor
                        try:
                            content = desc_raw.get("content", [])
                            paragraphs = []
                            for c in content:
                                for sub in c.get("content", []):
                                    if "text" in sub:
                                        paragraphs.append(sub["text"])
                            desc_str = "\n".join(paragraphs)
                        except Exception:
                            desc_str = str(desc_raw)

                    key = raw.get("key")
                    items.append({
                        "id": str(raw.get("id")),
                        "key": key,
                        "url": f"{settings.JIRA_BASE_URL.rstrip('/')}/browse/{key}",
                        "project_key": fields.get("project", {}).get("key", ""),
                        "summary": fields.get("summary", ""),
                        "description": desc_str,
                        "issue_type": fields.get("issuetype", {}).get("name", "Task"),
                        "priority": fields.get("priority", {}).get("name", "Medium"),
                        "status": fields.get("status", {}).get("name", "To Do"),
                        "assignee_name": fields.get("assignee", {}).get("displayName") if fields.get("assignee") else None,
                        "reporter_name": fields.get("reporter", {}).get("displayName") if fields.get("reporter") else None,
                        "created_at": fields.get("created", ""),
                        "updated_at": fields.get("updated", ""),
                        "comments": [],
                        "transitions": []
                    })

                total_pages = max(1, (total + size - 1) // size)
                return {
                    "items": items,
                    "total": total,
                    "page": page,
                    "size": size,
                    "pages": total_pages,
                    "project_key": project_key
                }
        except Exception as e:
            logger.warning(f"Real Jira issue search failed: {e}. Falling back to simulator issues.")
            return self.simulator.get_issues(
                project_key=project_key,
                search=search,
                status=status,
                priority=priority,
                jql=jql,
                page=page,
                size=size
            )

    async def get_issue(self, key: str) -> Optional[Dict[str, Any]]:
        if not self.is_real_cloud_configured():
            return self.simulator.get_issue(key)

        url = f"{settings.JIRA_BASE_URL.rstrip('/')}/rest/api/3/issue/{key}?expand=transitions"
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(url, headers=self._get_headers())
                if resp.status_code == 404:
                    return None
                resp.raise_for_status()
                raw = resp.json()
                fields = raw.get("fields", {})

                # Extract description
                desc_raw = fields.get("description")
                desc_str = ""
                if isinstance(desc_raw, str):
                    desc_str = desc_raw
                elif isinstance(desc_raw, dict):
                    try:
                        paragraphs = []
                        for c in desc_raw.get("content", []):
                            for sub in c.get("content", []):
                                if "text" in sub:
                                    paragraphs.append(sub["text"])
                        desc_str = "\n".join(paragraphs)
                    except Exception:
                        desc_str = str(desc_raw)

                # Extract comments
                comments = []
                for c in fields.get("comment", {}).get("comments", []):
                    c_body = c.get("body", "")
                    if isinstance(c_body, dict):
                        try:
                            parts = []
                            for p in c_body.get("content", []):
                                for s in p.get("content", []):
                                    if "text" in s:
                                        parts.append(s["text"])
                            c_body = "\n".join(parts)
                        except Exception:
                            c_body = str(c_body)
                    comments.append({
                        "id": str(c.get("id")),
                        "author": c.get("author", {}).get("displayName", "User"),
                        "body": str(c_body),
                        "created_at": c.get("created", "")
                    })

                # Extract transitions
                transitions = [
                    {
                        "id": str(t.get("id")),
                        "name": t.get("name"),
                        "to_status": t.get("to", {}).get("name", "")
                    }
                    for t in raw.get("transitions", [])
                ]

                return {
                    "id": str(raw.get("id")),
                    "key": key,
                    "url": f"{settings.JIRA_BASE_URL.rstrip('/')}/browse/{key}",
                    "project_key": fields.get("project", {}).get("key", ""),
                    "summary": fields.get("summary", ""),
                    "description": desc_str,
                    "issue_type": fields.get("issuetype", {}).get("name", "Task"),
                    "priority": fields.get("priority", {}).get("name", "Medium"),
                    "status": fields.get("status", {}).get("name", "To Do"),
                    "assignee_name": fields.get("assignee", {}).get("displayName") if fields.get("assignee") else None,
                    "reporter_name": fields.get("reporter", {}).get("displayName") if fields.get("reporter") else None,
                    "created_at": fields.get("created", ""),
                    "updated_at": fields.get("updated", ""),
                    "comments": comments,
                    "transitions": transitions
                }
        except Exception as e:
            logger.warning(f"Failed to fetch issue {key} from real Jira: {e}")
            return self.simulator.get_issue(key)

    async def create_issue(
        self,
        summary: str,
        description: str,
        priority: str,
        issue_type: Optional[str] = None,
        project_key: Optional[str] = None,
        assignee: Optional[str] = None,
        idempotency_key: Optional[str] = None
    ) -> Dict[str, Any]:
        if not self.is_real_cloud_configured():
            return self.simulator.create_issue(
                summary=summary,
                description=description,
                priority=priority,
                issue_type=issue_type,
                project_key=project_key,
                assignee=assignee,
                idempotency_key=idempotency_key
            )

        # Real Jira REST API v3 Issue Creation
        url = f"{settings.JIRA_BASE_URL.rstrip('/')}/rest/api/3/issue"
        proj = project_key or settings.JIRA_PROJECT_KEY
        itype = issue_type or settings.JIRA_DEFAULT_ISSUE_TYPE

        adf_description = {
            "version": 1,
            "type": "doc",
            "content": [
                {
                    "type": "paragraph",
                    "content": [{"type": "text", "text": description[:3000]}]
                }
            ]
        }

        payload: Dict[str, Any] = {
            "fields": {
                "project": {"key": proj},
                "summary": summary[:255],
                "description": adf_description,
                "issuetype": {"name": itype}
            }
        }

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                resp = await client.post(url, headers=self._get_headers(), json=payload)
                resp.raise_for_status()
                data = resp.json()
                key = data.get("key")
                issue_url = f"{settings.JIRA_BASE_URL.rstrip('/')}/browse/{key}"
                return {
                    "id": str(data.get("id")),
                    "key": key,
                    "url": issue_url,
                    "project_key": proj,
                    "issue_type": itype,
                    "priority": priority,
                    "status": "To Do",
                    "summary": summary,
                    "description": description,
                    "idempotency_hit": False
                }
        except Exception as e:
            logger.error(f"Real Jira creation failed: {str(e)}. Falling back to simulation.")
            return self.simulator.create_issue(
                summary=summary,
                description=description,
                priority=priority,
                issue_type=issue_type,
                project_key=project_key,
                assignee=assignee,
                idempotency_key=idempotency_key
            )

    async def update_issue(self, key: str, summary: Optional[str] = None, description: Optional[str] = None) -> Optional[Dict[str, Any]]:
        if not self.is_real_cloud_configured():
            return self.simulator.update_issue(key, summary=summary, description=description)

        url = f"{settings.JIRA_BASE_URL.rstrip('/')}/rest/api/3/issue/{key}"
        fields: Dict[str, Any] = {}
        if summary:
            fields["summary"] = summary[:255]
        if description:
            fields["description"] = {
                "version": 1,
                "type": "doc",
                "content": [
                    {
                        "type": "paragraph",
                        "content": [{"type": "text", "text": description[:3000]}]
                    }
                ]
            }

        if not fields:
            return await self.get_issue(key)

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.put(url, headers=self._get_headers(), json={"fields": fields})
                resp.raise_for_status()
                return await self.get_issue(key)
        except Exception as e:
            logger.warning(f"Real Jira update failed: {e}. Falling back to simulator update.")
            return self.simulator.update_issue(key, summary=summary, description=description)

    async def get_transitions(self, key: str) -> List[Dict[str, str]]:
        if not self.is_real_cloud_configured():
            return self.simulator.get_transitions(key)

        url = f"{settings.JIRA_BASE_URL.rstrip('/')}/rest/api/3/issue/{key}/transitions"
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(url, headers=self._get_headers())
                resp.raise_for_status()
                data = resp.json()
                return [
                    {
                        "id": str(t.get("id")),
                        "name": t.get("name"),
                        "to_status": t.get("to", {}).get("name", "")
                    }
                    for t in data.get("transitions", [])
                ]
        except Exception as e:
            logger.warning(f"Real Jira get transitions failed: {e}")
            return self.simulator.get_transitions(key)

    async def transition_issue(self, key: str, transition_id: str, comment_text: Optional[str] = None) -> Optional[Dict[str, Any]]:
        if not self.is_real_cloud_configured():
            return self.simulator.transition_issue(key, transition_id=transition_id, comment_text=comment_text)

        url = f"{settings.JIRA_BASE_URL.rstrip('/')}/rest/api/3/issue/{key}/transitions"
        payload: Dict[str, Any] = {
            "transition": {"id": transition_id}
        }
        if comment_text:
            payload["update"] = {
                "comment": [
                    {
                        "add": {
                            "body": {
                                "version": 1,
                                "type": "doc",
                                "content": [
                                    {
                                        "type": "paragraph",
                                        "content": [{"type": "text", "text": comment_text}]
                                    }
                                ]
                            }
                        }
                    }
                ]
            }

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.post(url, headers=self._get_headers(), json=payload)
                resp.raise_for_status()
                return await self.get_issue(key)
        except Exception as e:
            logger.warning(f"Real Jira transition failed: {e}. Falling back to simulator transition.")
            return self.simulator.transition_issue(key, transition_id=transition_id, comment_text=comment_text)

    async def get_comments(self, key: str) -> List[Dict[str, Any]]:
        if not self.is_real_cloud_configured():
            return self.simulator.get_comments(key)

        url = f"{settings.JIRA_BASE_URL.rstrip('/')}/rest/api/3/issue/{key}/comment"
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(url, headers=self._get_headers())
                resp.raise_for_status()
                data = resp.json()
                comments = []
                for c in data.get("comments", []):
                    c_body = c.get("body", "")
                    if isinstance(c_body, dict):
                        try:
                            parts = []
                            for p in c_body.get("content", []):
                                for s in p.get("content", []):
                                    if "text" in s:
                                        parts.append(s["text"])
                            c_body = "\n".join(parts)
                        except Exception:
                            c_body = str(c_body)
                    comments.append({
                        "id": str(c.get("id")),
                        "author": c.get("author", {}).get("displayName", "User"),
                        "body": str(c_body),
                        "created_at": c.get("created", "")
                    })
                return comments
        except Exception as e:
            logger.warning(f"Real Jira get comments failed: {e}")
            return self.simulator.get_comments(key)

    async def add_comment(self, key: str, author: str, comment_text: str) -> Optional[Dict[str, Any]]:
        if not self.is_real_cloud_configured():
            return self.simulator.add_comment(key, author=author, comment_text=comment_text)

        url = f"{settings.JIRA_BASE_URL.rstrip('/')}/rest/api/3/issue/{key}/comment"
        payload = {
            "body": {
                "version": 1,
                "type": "doc",
                "content": [
                    {
                        "type": "paragraph",
                        "content": [{"type": "text", "text": comment_text}]
                    }
                ]
            }
        }
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.post(url, headers=self._get_headers(), json=payload)
                resp.raise_for_status()
                data = resp.json()
                return {
                    "id": str(data.get("id")),
                    "author": data.get("author", {}).get("displayName", author),
                    "body": comment_text,
                    "created_at": data.get("created", "")
                }
        except Exception as e:
            logger.warning(f"Real Jira add comment failed: {e}. Falling back to simulator comment.")
            return self.simulator.add_comment(key, author=author, comment_text=comment_text)
