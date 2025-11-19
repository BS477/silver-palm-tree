from fastapi import FastAPI, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from setup_db import SessionLocal
from models import Movie, Link, Tag, Rating

app = FastAPI()


# ------------------------------
# DB SESSION
# ------------------------------
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ------------------------------
# Pydantic MODELS
# ------------------------------

class MovieCreate(BaseModel):
    movieId: int
    title: str
    genres: str


class MovieUpdate(BaseModel):
    title: str | None = None
    genres: str | None = None


class LinkCreate(BaseModel):
    movieId: int
    imdbId: str | None = None
    tmdbId: str | None = None


class LinkUpdate(BaseModel):
    imdbId: str | None = None
    tmdbId: str | None = None


class TagCreate(BaseModel):
    userId: int
    movieId: int
    tag: str
    timestamp: int


class TagUpdate(BaseModel):
    tag: str | None = None
    timestamp: int | None = None


class RatingCreate(BaseModel):
    userId: int
    movieId: int
    rating: float
    timestamp: int


class RatingUpdate(BaseModel):
    rating: float | None = None
    timestamp: int | None = None


# ============================================================
# MOVIES CRUD
# ============================================================

@app.post("/movies/{movie_id}")
def create_movie(movie: MovieCreate, db: Session = Depends(get_db)):
    db_movie = Movie(**movie.dict())
    db.add(db_movie)
    db.commit()
    return {"status": "created", "movie": movie}


@app.get("/movies/{movie_id}")
def get_movie(movie_id: int, db: Session = Depends(get_db)):
    movie = db.query(Movie).filter(Movie.movieId == movie_id).first()
    if not movie:
        raise HTTPException(404, "Movie not found")
    return movie


@app.get("/movies")
def list_movies(db: Session = Depends(get_db)):
    movies = db.query(Movie).all()
    return [
        {"movieId": m.movieId, "title": m.title, "genres": m.genres}
        for m in movies
    ]


@app.put("/movies/{movie_id}")
def update_movie(movie_id: int, data: MovieUpdate, db: Session = Depends(get_db)):
    movie = db.query(Movie).filter(Movie.movieId == movie_id).first()
    if not movie:
        raise HTTPException(404, "Movie not found")

    if data.title is not None:
        movie.title = data.title
    if data.genres is not None:
        movie.genres = data.genres

    db.commit()
    return {"status": "updated"}


@app.delete("/movies/{movie_id}")
def delete_movie(movie_id: int, db: Session = Depends(get_db)):
    movie = db.query(Movie).filter(Movie.movieId == movie_id).first()
    if not movie:
        raise HTTPException(404, "Movie not found")

    db.delete(movie)
    db.commit()
    return {"status": "deleted"}


# ============================================================
# LINKS CRUD
# ============================================================

@app.post("/links")
def create_link(link: LinkCreate, db: Session = Depends(get_db)):
    db_link = Link(**link.dict())
    db.add(db_link)
    db.commit()
    return {"status": "created", "link": link}


@app.get("/links/{movie_id}")
def get_link(movie_id: int, db: Session = Depends(get_db)):
    link = db.query(Link).filter(Link.movieId == movie_id).first()
    if not link:
        raise HTTPException(404, "Link not found")
    return link


@app.put("/links/{movie_id}")
def update_link(movie_id: int, data: LinkUpdate, db: Session = Depends(get_db)):
    link = db.query(Link).filter(Link.movieId == movie_id).first()
    if not link:
        raise HTTPException(404, "Link not found")

    if data.imdbId is not None:
        link.imdbId = data.imdbId
    if data.tmdbId is not None:
        link.tmdbId = data.tmdbId

    db.commit()
    return {"status": "updated"}


@app.delete("/links/{movie_id}")
def delete_link(movie_id: int, db: Session = Depends(get_db)):
    link = db.query(Link).filter(Link.movieId == movie_id).first()
    if not link:
        raise HTTPException(404, "Link not found")

    db.delete(link)
    db.commit()
    return {"status": "deleted"}


# ============================================================
# TAGS CRUD
# ============================================================

@app.post("/tags")
def create_tag(tag: TagCreate, db: Session = Depends(get_db)):
    db_tag = Tag(**tag.dict())
    db.add(db_tag)
    db.commit()
    return {"status": "created", "tag": tag}


@app.get("/tags/{tag_id}")
def get_tag(tag_id: int, db: Session = Depends(get_db)):
    tag = db.query(Tag).filter(Tag.id == tag_id).first()
    if not tag:
        raise HTTPException(404, "Tag not found")
    return tag


@app.put("/tags/{tag_id}")
def update_tag(tag_id: int, data: TagUpdate, db: Session = Depends(get_db)):
    tag = db.query(Tag).filter(Tag.id == tag_id).first()
    if not tag:
        raise HTTPException(404, "Tag not found")

    if data.tag is not None:
        tag.tag = data.tag
    if data.timestamp is not None:
        tag.timestamp = data.timestamp

    db.commit()
    db.refresh(tag)
    return {"status": "updated"}


@app.delete("/tags/{tag_id}")
def delete_tag(tag_id: int, db: Session = Depends(get_db)):
    tag = db.query(Tag).filter(Tag.id == tag_id).first()
    if not tag:
        raise HTTPException(404, "Tag not found")

    db.delete(tag)
    db.commit()
    return {"status": "deleted"}


# ============================================================
# RATINGS CRUD
# ============================================================

@app.post("/ratings")
def create_rating(rating: RatingCreate, db: Session = Depends(get_db)):
    db_rating = Rating(**rating.dict())
    db.add(db_rating)
    db.commit()
    return {"status": "created", "rating": rating}


@app.get("/ratings/{rating_id}")
def get_rating(rating_id: int, db: Session = Depends(get_db)):
    rating = db.query(Rating).filter(Rating.id == rating_id).first()
    if not rating:
        raise HTTPException(404, "Rating not found")
    return rating


@app.put("/ratings/{rating_id}")
def update_rating(rating_id: int, data: RatingUpdate, db: Session = Depends(get_db)):
    rating = db.query(Rating).filter(Rating.id == rating_id).first()
    if not rating:
        raise HTTPException(404, "Rating not found")

    if data.rating is not None:
        rating.rating = data.rating
    if data.timestamp is not None:
        rating.timestamp = data.timestamp

    db.commit()
    db.refresh(rating)
    return {"status": "updated"}


@app.delete("/ratings/{rating_id}")
def delete_rating(rating_id: int, db: Session = Depends(get_db)):
    rating = db.query(Rating).filter(Rating.id == rating_id).first()
    if not rating:
        raise HTTPException(404, "Rating not found")

    db.delete(rating)
    db.commit()
    return {"status": "deleted"}
