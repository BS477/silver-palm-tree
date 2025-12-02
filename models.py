from sqlalchemy import Column, Integer, String, List, Text, Float, ForeignKey
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(100), unique=True, index=True, nullable=False)
    full_name = Column(String(200), nullable=True)
    hashed_password = Column(Text, nullable=False)
    # roles stored as comma-separated string, e.g. "ROLE_ADMIN,ROLE_USER"
    roles = Column(String(500), nullable=False, default="ROLE_USER")

    def get_roles_list(self) -> List[str]:
        return [r.strip() for r in (self.roles or "").split(",") if r.strip()]

    def __repr__(self) -> str:
        return f"User(id={self.id!r}, username={self.username!r})"

# Model danych
class Movie:
    def __init__(self, movieId: int, title: str, genres: str):
        self.movieId = movieId
        self.title = title
        self.genres = genres

class Link:
    def __init__(self, movieId: int, imdbId: str, tmdbId: str):
        self.movieId = movieId
        self.imdbId = imdbId
        self.tmdbId = tmdbId


class Tag:
    def __init__(self, userId: int, movieId: int, tag: str, timestamp: int):
        self.userId = userId
        self.movieId = movieId
        self.tag = tag
        self.timestamp = timestamp


class Rating:
    def __init__(self, userId: int, movieId: int, rating: float, timestamp: int):
        self.userId = userId
        self.movieId = movieId
        self.rating = rating
        self.timestamp = timestamp

class Movie(Base):
    __tablename__ = "movies"

    movieId = Column(Integer, primary_key=True)
    title = Column(String, nullable=False)
    genres = Column(String, nullable=False)

    # relacje
    links = relationship("Link", back_populates="movie", uselist=False)
    tags = relationship("Tag", back_populates="movie")
    ratings = relationship("Rating", back_populates="movie")


class Link(Base):
    __tablename__ = "links"

    movieId = Column(Integer, ForeignKey("movies.movieId"), primary_key=True)
    imdbId = Column(String)
    tmdbId = Column(String)

    movie = relationship("Movie", back_populates="links")


class Tag(Base):
    __tablename__ = "tags"

    id = Column(Integer, primary_key=True, autoincrement=True)
    userId = Column(Integer, nullable=False)
    movieId = Column(Integer, ForeignKey("movies.movieId"), nullable=False)
    tag = Column(String, nullable=False)
    timestamp = Column(Integer, nullable=False)

    movie = relationship("Movie", back_populates="tags")


class Rating(Base):
    __tablename__ = "ratings"

    id = Column(Integer, primary_key=True, autoincrement=True)
    userId = Column(Integer, nullable=False)
    movieId = Column(Integer, ForeignKey("movies.movieId"), nullable=False)
    rating = Column(Float, nullable=False)
    timestamp = Column(Integer, nullable=False)

    movie = relationship("Movie", back_populates="ratings")