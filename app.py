import os
from datetime import datetime, timedelta
from typing import Optional, List

from fastapi import FastAPI, Depends, HTTPException, status, Header
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel
from sqlalchemy.orm import Session

import jwt
from passlib.context import CryptContext

from setup_db import SessionLocal, create_tables
from models import *

# settings
JWT_SECRET = os.environ.get("JWT_SECRET", "supersecret_change_me")
JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

app = FastAPI()

# create tables at start
create_tables()

# --- Pydantic schemas ---
class UserCreate(BaseModel):
    username: str
    password: str
    full_name: Optional[str] = None
    roles: Optional[List[str]] = None  # optional list of roles

class Token(BaseModel):
    access_token: str
    token_type: str

class UserDetails(BaseModel):
    sub: str
    roles: List[str]
    full_name: Optional[str] = None
    exp: int

# --- helpers ---
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": int(expire.timestamp())})
    token = jwt.encode(to_encode, JWT_SECRET, algorithm=JWT_ALGORITHM)
    return token

def decode_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

# --- utility: fetch user by username ---
def get_user_by_username(db: Session, username: str) -> Optional[User]:
    return db.query(User).filter(User.username == username).first()

# --- Auth dependency: get payload from Bearer token ---
def get_payload_from_authorization(authorization: Optional[str] = Header(None)):
    if not authorization:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing Authorization header")
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid Authorization header")
    token = authorization.split(" ", 1)[1].strip()
    payload = decode_token(token)
    return payload

# --- role check dependency ---
def require_roles(required_roles: List[str]):
    def dep(payload: dict = Depends(get_payload_from_authorization)):
        roles = payload.get("roles", [])
        if not isinstance(roles, list):
            # accept comma-separated roles if needed
            if isinstance(roles, str):
                roles = [r.strip() for r in roles.split(",") if r.strip()]
            else:
                roles = []
        for r in required_roles:
            if r in roles:
                return payload
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
    return dep

# --- endpoints ---
@app.post("/login", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """
    Form fields: username, password
    Returns JWT token with payload: sub (username), roles (list), full_name
    """
    user = get_user_by_username(db, form_data.username)
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect username or password")
    payload = {
        "sub": user.username,
        "roles": user.get_roles_list(),
        "full_name": user.full_name,
    }
    token = create_access_token(payload)
    return {"access_token": token, "token_type": "bearer"}

@app.post("/users", response_model=dict)
def create_user(user_in: UserCreate, payload: dict = Depends(require_roles(["ROLE_ADMIN"])), db: Session = Depends(get_db)):
    """
    Create new user. Only ROLE_ADMIN can call this endpoint.
    """
    # check username uniqueness
    existing = get_user_by_username(db, user_in.username)
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Username already exists")
    hashed = get_password_hash(user_in.password)
    roles_list = user_in.roles or ["ROLE_USER"]
    roles_str = ",".join(roles_list)
    new_user = User(username=user_in.username, full_name=user_in.full_name, hashed_password=hashed, roles=roles_str)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return {"id": new_user.id, "username": new_user.username, "roles": new_user.get_roles_list()}

@app.get("/user_details", response_model=UserDetails)
def user_details(payload: dict = Depends(get_payload_from_authorization)):
    """
    Return details from JWT payload (no DB lookup necessary).
    """
    roles = payload.get("roles", [])
    if isinstance(roles, str):
        roles = [r.strip() for r in roles.split(",") if r.strip()]
    return {
        "sub": payload.get("sub"),
        "roles": roles,
        "full_name": payload.get("full_name"),
        "exp": payload.get("exp"),
    }

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
