from models import Rating


def test_create_rating(client, db_session):
    data = {"userId": 1, "movieId": 2, "rating": 4.5, "timestamp": 123}
    response = client.post("/ratings", json=data)
    assert response.status_code == 200

    rating = db_session.query(Rating).first()
    assert rating.rating == 4.5


def test_get_rating(client, db_session):
    r = Rating(userId=1, movieId=2, rating=3.0, timestamp=444)
    db_session.add(r)
    db_session.commit()

    response = client.get(f"/ratings/{r.id}")
    assert response.status_code == 200
    assert response.json()["rating"] == 3.0


def test_get_rating_not_found(client):
    assert client.get("/ratings/9999").status_code == 404


def test_update_rating(client, db_session):
    r = Rating(userId=1, movieId=2, rating=1.0, timestamp=111)
    db_session.add(r)
    db_session.commit()

    response = client.put(f"/ratings/{r.id}", json={"rating": 4.0})
    assert response.status_code == 200

    assert db_session.query(Rating).first().rating == 4.0


def test_delete_rating(client, db_session):
    r = Rating(userId=1, movieId=2, rating=2.5, timestamp=123)
    db_session.add(r)
    db_session.commit()

    response = client.delete(f"/ratings/{r.id}")
    assert response.status_code == 200

    assert db_session.query(Rating).filter_by(id=r.id).first() is None
