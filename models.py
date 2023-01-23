from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Venue(db.Model):
    __tablename__ = 'Venue'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    city = db.Column(db.String(120), nullable=False)
    state = db.Column(db.String(120), nullable=False) 
    address = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(120))
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))
    genres = db.Column(db.String(120), nullable=False)
    website = db.Column(db.String)
    seeking_talent = db.Column(db.Boolean)
    seeking_description = db.Column(db.String)
    
    __table_args__ = (db.UniqueConstraint('name', 'city', 'state'),)
    
    # Function for updating venue data
    def update(cls, data):
      for key, value in data.items():
        if key=="seeking_talent":  # request.form.get don't return bool values
          if value=="y":
            value = True
          else:
            value = False 
        setattr(cls, key, value)
      return cls
    
    # Get shows that happened in the past
    def get_past_shows(cls, date):
      shows = cls.shows
      past_shows = [] 
      for show in shows:
        if show.start_time <= date:
          show.artist_name = show.artists.name
          show.artist_image_link = show.artists.image_link
          past_shows.append(show)
      return past_shows
    
    # Get shows that will happen in the future
    def get_upcoming_shows(cls, date):
      shows = cls.shows
      upcoming_shows = [] 
      for show in shows:
        if show.start_time > date:
          show.artist_name = show.artists.name
          show.artist_image_link = show.artists.image_link
          upcoming_shows.append(show)
      return upcoming_shows
class Artist(db.Model):
    __tablename__ = 'Artist'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)  
    city = db.Column(db.String(120), nullable=False)  
    state = db.Column(db.String(120), nullable=False) 
    phone = db.Column(db.String(120))
    genres = db.Column(db.String(120), nullable=False)
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))
    website = db.Column(db.String)
    seeking_venue = db.Column(db.Boolean)
    seeking_description = db.Column(db.String)
    
    __table_args__ = (db.UniqueConstraint('name', 'city', 'state'),)
    
    # Function for updating artist data
    def update(cls, data):
      for key, value in data.items():
        if key=="seeking_talent":  # request.form.get don't return bool values
          if value=="y":
            value = True
          else:
            value = False 
        setattr(cls, key, value)
      return cls
    
     # Get shows that happened in the past
    def get_past_shows(cls, date):
      shows = cls.shows
      past_shows = [] 
      for show in shows:
        if show.start_time <= date:
          show.venue_name = show.venues.name
          show.venue_image_link = show.venues.image_link
          past_shows.append(show)
      return past_shows
    
    # Get shows that will happen in the future
    def get_upcoming_shows(cls, date):
      shows = cls.shows
      upcoming_shows = [] 
      for show in shows:
        if show.start_time > date:
          show.venue_name = show.venues.name
          show.venue_image_link = show.venues.image_link
          upcoming_shows.append(show)
      return upcoming_shows
    
class Show(db.Model):
  __tablename__ = "Show"
  
  id = db.Column(db.Integer, primary_key=True)
  
  venue_id = db.Column(db.Integer, db.ForeignKey("Venue.id"), nullable=False)
  artist_id = db.Column(db.Integer, db.ForeignKey("Artist.id"), nullable=False)
  
  start_time = db.Column(db.DateTime)
  
  venues = db.relationship("Venue", backref="shows", lazy=True)
  artists = db.relationship("Artist", backref="shows", lazy=True)
  
  # Function for updating show data
  def update(cls, data):
    for key, value in data.items():
      setattr(cls, key, value)
    return cls