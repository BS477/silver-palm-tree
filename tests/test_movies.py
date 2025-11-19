from models import Movie


def test_get_movies_empty(client):
    response = client.get("/movies")
    assert response.status_code == 200
    assert response.json() == []


def test_create_movie(client, db_session):
    data = {
        "movieId": 1,
        "title": "Matrix",
        "genres": "Action|Sci-Fi"
    }

    response = client.post("/movies/1", json=data)
    assert response.status_code == 200

    movie = db_session.query(Movie).filter_by(movieId=1).first()
    assert movie is not None
    assert movie.title == "Matrix"


def test_get_movie_item(client, db_session):
    db_session.add(Movie(movieId=10, title="TestMovie", genres="Drama"))
    db_session.commit()

    response = client.get("/movies/10")
    assert response.status_code == 200
    assert response.json()["title"] == "TestMovie"


def test_get_movie_not_found(client):
    response = client.get("/movies/9999")
    assert response.status_code == 404


def test_update_movie(client, db_session):
    db_session.add(Movie(movieId=5, title="Old", genres="Drama"))
    db_session.commit()

    response = client.put("/movies/5", json={"title": "New Title"})
    assert response.status_code == 200

    updated = db_session.query(Movie).filter_by(movieId=5).first()
    assert updated.title == "New Title"


def test_delete_movie(client, db_session):
    db_session.add(Movie(movieId=123, title="DeleteMe", genres="Thriller"))
    db_session.commit()

    response = client.delete("/movies/123")
    assert response.status_code == 200

    assert db_session.query(Movie).filter_by(movieId=123).first() is None
