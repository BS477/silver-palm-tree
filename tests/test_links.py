from models import Link


def test_create_link(client, db_session):
    data = {"movieId": 1, "imdbId": "12345", "tmdbId": "54321"}
    response = client.post("/links", json=data)

    assert response.status_code == 200

    link = db_session.query(Link).filter_by(movieId=1).first()
    assert link is not None
    assert link.imdbId == "12345"


def test_get_link(client, db_session):
    db_session.add(Link(movieId=10, imdbId="i10", tmdbId="t10"))
    db_session.commit()

    response = client.get("/links/10")
    assert response.status_code == 200
    assert response.json()["imdbId"] == "i10"


def test_get_link_not_found(client):
    response = client.get("/links/9999")
    assert response.status_code == 404


def test_update_link(client, db_session):
    db_session.add(Link(movieId=20, imdbId="old", tmdbId="old"))
    db_session.commit()

    response = client.put("/links/20", json={"imdbId": "new"})
    assert response.status_code == 200

    link = db_session.query(Link).filter_by(movieId=20).first()
    assert link.imdbId == "new"


def test_delete_link(client, db_session):
    db_session.add(Link(movieId=33, imdbId="xx", tmdbId="yy"))
    db_session.commit()

    response = client.delete("/links/33")
    assert response.status_code == 200

    assert db_session.query(Link).filter_by(movieId=33).first() is None
