from fastapi import FastAPI
from fastapi.testclient import TestClient
from app.middleware.security_headers import SecurityHeadersMiddleware


def create_test_app():
    app = FastAPI()
    app.add_middleware(SecurityHeadersMiddleware)

    @app.get("/test")
    async def test_endpoint():
        return {"message": "ok"}

    return app


def test_security_headers_are_set():
    client = TestClient(create_test_app())
    response = client.get("/test")
    assert response.status_code == 200
    assert (
        response.headers["Strict-Transport-Security"]
        == "max-age=3600; includeSubDomains"
    )
    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert response.headers["X-Frame-Options"] == "DENY"
