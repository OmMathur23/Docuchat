import requests


class APIError(Exception):
    def __init__(self, status_code: int, detail: str):
        self.status_code = status_code
        self.detail = detail
        super().__init__(f"[{status_code}] {detail}")


class DocuChatClient:
    def __init__(self, base_url: str, token: str | None = None):
        self.base_url = base_url.rstrip("/")
        self.token = token

    def _headers(self) -> dict:
        return {"Authorization": f"Bearer {self.token}"} if self.token else {}

    @staticmethod
    def _handle(resp: requests.Response):
        if resp.status_code >= 400:
            detail = resp.text
            try:
                body = resp.json()
                detail = body.get("detail", detail)
            except ValueError:
                pass
            raise APIError(resp.status_code, str(detail))
        if resp.status_code == 204 or not resp.content:
            return None
        return resp.json()

    def signup(self, email: str, password: str) -> dict:
        resp = requests.post(
            f"{self.base_url}/auth/signup",
            json={"email": email, "password": password},
            timeout=15,
        )
        return self._handle(resp)

    def login(self, email: str, password: str) -> dict:
        resp = requests.post(
            f"{self.base_url}/auth/login",
            json={"email": email, "password": password},
            timeout=15,
        )
        return self._handle(resp)

    def list_documents(self, limit: int = 100, skip: int = 0) -> list[dict]:
        resp = requests.get(
            f"{self.base_url}/documents/",
            headers=self._headers(),
            params={"limit": limit, "skip": skip},
            timeout=15,
        )
        return self._handle(resp)

    def upload_document(self, filename: str, file_bytes: bytes, content_type: str) -> dict:
        files = {"file": (filename, file_bytes, content_type)}
        resp = requests.post(
            f"{self.base_url}/documents/upload",
            headers=self._headers(),
            files=files,
            timeout=180,
        )
        return self._handle(resp)

    def delete_document(self, document_id: int) -> None:
        resp = requests.delete(
            f"{self.base_url}/documents/{document_id}",
            headers=self._headers(),
            timeout=15,
        )
        return self._handle(resp)

    def ask(self, document_id: int, question: str) -> dict:
        resp = requests.post(
            f"{self.base_url}/documents/{document_id}/ask",
            headers=self._headers(),
            json={"question": question},
            timeout=90,
        )
        return self._handle(resp)
