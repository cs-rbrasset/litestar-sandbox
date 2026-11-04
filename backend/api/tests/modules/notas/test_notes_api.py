from typing import TYPE_CHECKING

from litestar.testing import TestClient

from app import create_app
from core.auth import DevTokenVerifier
from core.identity import Identity

if TYPE_CHECKING:
    from core.settings import DatabaseSettings


def test_list_my_notes_starts_empty(app_client: TestClient) -> None:
    response = app_client.get("/api/v1/notas/mine")
    assert response.status_code == 200
    assert response.json() == []


def test_create_note_defaults_title_and_empty_content(app_client: TestClient) -> None:
    created = app_client.post("/api/v1/notas", json={})
    assert created.status_code == 201, created.text
    body = created.json()
    assert body["title"] == "Sem título"
    assert body["content"] == {}
    assert body["published"] is False


def test_create_note_then_list_shows_it(app_client: TestClient) -> None:
    created = app_client.post("/api/v1/notas", json={"title": "Primeiro artigo"})
    note_id = created.json()["id"]

    listed = app_client.get("/api/v1/notas/mine").json()
    assert len(listed) == 1
    assert listed[0]["id"] == note_id
    assert listed[0]["title"] == "Primeiro artigo"


def test_get_note_returns_full_content(app_client: TestClient) -> None:
    created = app_client.post("/api/v1/notas", json={"title": "Artigo"}).json()

    fetched = app_client.get(f"/api/v1/notas/{created['id']}")
    assert fetched.status_code == 200
    assert fetched.json()["title"] == "Artigo"


def test_get_unknown_note_is_404(app_client: TestClient) -> None:
    assert app_client.get("/api/v1/notas/999").status_code == 404


def test_update_note_changes_title_content_published(app_client: TestClient) -> None:
    created = app_client.post("/api/v1/notas", json={"title": "Rascunho"}).json()

    content = {"type": "doc", "content": [{"type": "paragraph"}]}
    updated = app_client.put(
        f"/api/v1/notas/{created['id']}",
        json={"title": "Publicado", "content": content, "published": True},
    )
    assert updated.status_code == 200
    body = updated.json()
    assert body["title"] == "Publicado"
    assert body["content"] == content
    assert body["published"] is True


def test_update_unknown_note_is_404(app_client: TestClient) -> None:
    response = app_client.put(
        "/api/v1/notas/999", json={"title": "x", "content": {}, "published": False}
    )
    assert response.status_code == 404


def test_delete_note_removes_it(app_client: TestClient) -> None:
    note = app_client.post("/api/v1/notas", json={"title": "Artigo"}).json()

    deleted = app_client.delete(f"/api/v1/notas/{note['id']}")
    assert deleted.status_code == 204

    assert app_client.get(f"/api/v1/notas/{note['id']}").status_code == 404
    assert app_client.get("/api/v1/notas/mine").json() == []


def test_delete_unknown_note_is_404(app_client: TestClient) -> None:
    assert app_client.delete("/api/v1/notas/999").status_code == 404


def _two_user_client(database_settings: DatabaseSettings) -> TestClient:
    alice = Identity(subject="u_alice", db_role="u_alice", name="Alice")
    bob = Identity(subject="u_bob", db_role="u_bob", name="Bob")
    app = create_app(
        database_settings,
        verifier=DevTokenVerifier({"tok-alice": alice, "tok-bob": bob}),
    )
    return TestClient(app=app)


def test_notes_are_isolated_per_owner(database_settings: DatabaseSettings) -> None:
    with _two_user_client(database_settings) as client:
        client.headers["Authorization"] = "Bearer tok-alice"
        alice_note = client.post("/api/v1/notas", json={"title": "Nota da Alice"}).json()

        client.headers["Authorization"] = "Bearer tok-bob"
        assert client.get("/api/v1/notas/mine").json() == []
        assert client.get(f"/api/v1/notas/{alice_note['id']}").status_code == 404
        assert (
            client.put(
                f"/api/v1/notas/{alice_note['id']}",
                json={"title": "hackeado", "content": {}, "published": False},
            ).status_code
            == 404
        )

        assert client.delete(f"/api/v1/notas/{alice_note['id']}").status_code == 404

        client.headers["Authorization"] = "Bearer tok-alice"
        assert client.get(f"/api/v1/notas/{alice_note['id']}").status_code == 200


def test_wiki_lists_only_published_notes_across_users(database_settings: DatabaseSettings) -> None:
    with _two_user_client(database_settings) as client:
        client.headers["Authorization"] = "Bearer tok-alice"
        alice_note = client.post("/api/v1/notas", json={"title": "Artigo da Alice"}).json()
        client.put(
            f"/api/v1/notas/{alice_note['id']}",
            json={"title": "Artigo da Alice", "content": {"from": "alice"}, "published": True},
        )

        client.headers["Authorization"] = "Bearer tok-bob"
        bob_note = client.post("/api/v1/notas", json={"title": "Artigo do Bob"}).json()
        client.put(
            f"/api/v1/notas/{bob_note['id']}",
            json={"title": "Artigo do Bob", "content": {"from": "bob"}, "published": False},
        )

        wiki = client.get("/api/v1/notas/wiki").json()
        assert len(wiki) == 1
        assert wiki[0]["author_name"] == "Alice"
        assert wiki[0]["title"] == "Artigo da Alice"
        assert wiki[0]["content"] == {"from": "alice"}


def test_unpublishing_removes_note_from_wiki(app_client: TestClient) -> None:
    note = app_client.post("/api/v1/notas", json={"title": "Artigo"}).json()
    app_client.put(
        f"/api/v1/notas/{note['id']}",
        json={"title": "Artigo", "content": {"v": 1}, "published": True},
    )
    assert len(app_client.get("/api/v1/notas/wiki").json()) == 1

    app_client.put(
        f"/api/v1/notas/{note['id']}",
        json={"title": "Artigo", "content": {"v": 1}, "published": False},
    )
    assert app_client.get("/api/v1/notas/wiki").json() == []
