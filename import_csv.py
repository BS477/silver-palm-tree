import csv
from sqlalchemy.orm import Session
from setup_db import SessionLocal, init_db
from models import Movie, Link, Tag, Rating


def import_movies(db: Session, path="movies.csv"):
    with open(path, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            movie = Movie(
                movieId=int(row["movieId"]),
                title=row["title"],
                genres=row["genres"]
            )
            db.merge(movie)  # merge => insert lub update
    db.commit()
    print("Zaimportowano movies.csv")


def import_links(db: Session, path="links.csv"):
    with open(path, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            link = Link(
                movieId=int(row["movieId"]),
                imdbId=row["imdbId"] or None,
                tmdbId=row["tmdbId"] or None
            )
            db.merge(link)
    db.commit()
    print("Zaimportowano links.csv")


def import_tags(db: Session, path="tags.csv"):
    with open(path, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            tag = Tag(
                userId=int(row["userId"]),
                movieId=int(row["movieId"]),
                tag=row["tag"],
                timestamp=int(row["timestamp"])
            )
            db.add(tag)
    db.commit()
    print("Zaimportowano tags.csv")


def import_ratings(db: Session, path="ratings.csv"):
    with open(path, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rating = Rating(
                userId=int(row["userId"]),
                movieId=int(row["movieId"]),
                rating=float(row["rating"]),
                timestamp=int(row["timestamp"])
            )
            db.add(rating)
    db.commit()
    print("Zaimportowano ratings.csv")


def run_import():
    init_db()  # utwórz tabelę, jeśli nie istnieje
    db = SessionLocal()

    try:
        import_movies(db)
        import_links(db)
        import_tags(db)
        import_ratings(db)
    finally:
        db.close()


if __name__ == "__main__":
    run_import()
    print("\nImport zakończony!")
