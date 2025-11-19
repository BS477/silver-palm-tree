from models import Tag


def test_create_tag(client, db_session):
    data = {"userId": 1, "movieId": 10, "tag": "cool", "timestamp": 123}
    response = client.post("/tags", json=data)
    assert response.status_code == 200

    tag = db_session.query(Tag).first()
    assert tag.tag == "cool"


def test_get_tag(client, db_session):
    t = Tag(userId=1, movieId=2, tag="funny", timestamp=555)
    db_session.add(t)
    db_session.commit()

    response = client.get(f"/tags/{t.id}")
    assert response.status_code == 200
    assert response.json()["tag"] == "funny"


def test_get_tag_not_found(client):
    assert client.get("/tags/9999").status_code == 404


def test_update_tag(client, db_session):
    t = Tag(userId=1, movieId=2, tag="old", timestamp=111)
    db_session.add(t)
    db_session.commit()

    response = client.put(f"/tags/{t.id}", json={"tag": "updated"})
    assert response.status_code == 200

    assert db_session.query(Tag).first().tag == "updated"


def test_delete_tag(client, db_session):
    t = Tag(userId=1, movieId=2, tag="del", timestamp=111)
    db_session.add(t)
    db_session.commit()

    response = client.delete(f"/tags/{t.id}")
    assert response.status_code == 200

    assert db_session.query(Tag).filter_by(id=t.id).first() is None
