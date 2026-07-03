import pyotp

from app.core.rate_limit import limiter

REGISTER_PAYLOAD = {"name": "Test User", "email": "test@example.com", "password": "supersecret1"}


def test_full_auth_and_mfa_flow(client, monkeypatch):
    captured = {}
    monkeypatch.setattr(
        "app.api.routes.auth._send_verification_email",
        lambda user, raw_token: captured.__setitem__("token", raw_token),
    )

    # 1. register -> 201, no token
    r = client.post("/api/auth/register", json=REGISTER_PAYLOAD)
    assert r.status_code == 201
    assert "access_token" not in r.json()
    assert "token" in captured

    # 3. login before verification -> 403
    r = client.post(
        "/api/auth/login", json={"email": REGISTER_PAYLOAD["email"], "password": REGISTER_PAYLOAD["password"]}
    )
    assert r.status_code == 403

    # 2. verify email
    r = client.post("/api/auth/verify-email", json={"token": captured["token"]})
    assert r.status_code == 200

    # invalid/reused token now fails
    r = client.post("/api/auth/verify-email", json={"token": captured["token"]})
    assert r.status_code == 400

    # 4. login after verification (MFA off) -> access_token
    r = client.post(
        "/api/auth/login", json={"email": REGISTER_PAYLOAD["email"], "password": REGISTER_PAYLOAD["password"]}
    )
    assert r.status_code == 200
    access_token = r.json()["access_token"]
    assert access_token

    r = client.get("/api/auth/me", headers={"Authorization": f"Bearer {access_token}"})
    assert r.status_code == 200
    assert r.json()["email"] == REGISTER_PAYLOAD["email"]

    # 5. set up MFA
    r = client.post("/api/auth/mfa/setup", headers={"Authorization": f"Bearer {access_token}"})
    assert r.status_code == 200
    secret = r.json()["secret"]

    r = client.post(
        "/api/auth/mfa/confirm",
        json={"code": pyotp.TOTP(secret).now()},
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["mfa_enabled"] is True
    backup_codes = body["backup_codes"]
    assert len(backup_codes) == 10

    # 6. login again -> mfa_required
    r = client.post(
        "/api/auth/login", json={"email": REGISTER_PAYLOAD["email"], "password": REGISTER_PAYLOAD["password"]}
    )
    assert r.status_code == 200
    data = r.json()
    assert data["mfa_required"] is True
    pending_token = data["mfa_pending_token"]

    # wrong TOTP code -> 401
    r = client.post("/api/auth/mfa/verify", json={"mfa_pending_token": pending_token, "code": "000000"})
    assert r.status_code == 401

    # correct TOTP code -> access_token
    r = client.post(
        "/api/auth/mfa/verify", json={"mfa_pending_token": pending_token, "code": pyotp.TOTP(secret).now()}
    )
    assert r.status_code == 200
    assert r.json()["access_token"]

    # backup code path: succeeds once, fails on reuse
    r = client.post(
        "/api/auth/login", json={"email": REGISTER_PAYLOAD["email"], "password": REGISTER_PAYLOAD["password"]}
    )
    pending_token_2 = r.json()["mfa_pending_token"]
    backup_code = backup_codes[0]

    r = client.post("/api/auth/mfa/verify", json={"mfa_pending_token": pending_token_2, "code": backup_code})
    assert r.status_code == 200

    r = client.post(
        "/api/auth/login", json={"email": REGISTER_PAYLOAD["email"], "password": REGISTER_PAYLOAD["password"]}
    )
    pending_token_3 = r.json()["mfa_pending_token"]
    r = client.post("/api/auth/mfa/verify", json={"mfa_pending_token": pending_token_3, "code": backup_code})
    assert r.status_code == 401


def test_login_rate_limit(client):
    limiter.enabled = True
    try:
        statuses = []
        for _ in range(11):
            r = client.post("/api/auth/login", json={"email": "nobody@example.com", "password": "wrong"})
            statuses.append(r.status_code)
        assert statuses[-1] == 429
    finally:
        limiter.enabled = False
