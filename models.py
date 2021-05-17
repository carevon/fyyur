from flask_sqlalchemy import SQLAlchemy, model
from datetime import datetime, timezone, timedelta
from time import timezone


#----------------------------------------------------------------------------#
# Models.
#----------------------------------------------------------------------------#

db = SQLAlchemy()

class BaseModel(db.Model):
    __abstract__ = True

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    created_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone(timedelta(hours=-3))))
    updated_at = db.Column(db.DateTime(timezone=True), nullable=False)

    def save(self, commit=True):
        db.session.add(self)
        if commit:
            try:
                db.session.commit()
            except Exception as e:
                db.session.rollback()
                raise e

        self.after_save()

    def update(self, *args, **kwargs):
        self.before_update(*args, **kwargs)
        db.session.commit()
        self.after_update(*args, **kwargs)

    def delete(self, commit=True):
        db.session.delete(self)
        if commit:
            db.session.commit()

class Venue(BaseModel):
    __tablename__ = 'Venue'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    address = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    genres = db.Column(db.ARRAY(db.String(200)), server_default='{}')
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))
    website = db.Column(db.String(120))
    seeking_talent = db.Column(db.Boolean, default=True)
    seeking_description = db.Column(db.String(120), default="We are on the lookout for a local artist to play every two weeks. Please call us.")

    # Venue is the parent (one-to-many) of a Show (Artist is also a foreign key, in def. of Show)
    # In the parent is where we put the db.relationship in SQLAlchemy
    shows = db.relationship('Show', backref=db.backref('venue', lazy=True))

    def __repr__(self) -> str:
        return '<Venue {}>'.format(self.name)

class Artist(BaseModel):
    __tablename__ = 'Artist'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    genres = db.Column(db.ARRAY(db.String(200)), server_default='{}')
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(300))
    seeking_venue = db.Column(db.Boolean, default=True)
    seeking_description = db.Column(db.String(120), default="Currently seeking performance venues")
    website = db.Column(db.String(120))
    shows = db.relationship('Show', backref=db.backref('artist', lazy=True))

    def __repr__(self) -> str:
        return '<Artist {}>'.format(self.name)

class Show(BaseModel):
    __tablename__ = 'Show'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    venue_id = db.Column(db.Integer, db.ForeignKey('Venue.id'), primary_key=True, nullable=False)
    artist_id = db.Column(db.Integer, db.ForeignKey('Artist.id'), primary_key=True, nullable=False)
    start_time = db.Column(db.DateTime(timezone=True), nullable=False)

    def __repr__(self) -> str:
        return '<Show {} {}>'.format(self.artist_id, self.venue_id)