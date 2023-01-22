#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

import babel
import dateutil.parser
import logging
import sys

from datetime import datetime
from flask import Flask, render_template, request, Response, flash, redirect, url_for, abort
from flask_migrate import Migrate
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
from logging import Formatter, FileHandler
from flask_wtf import Form
from forms import *

#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')
db = SQLAlchemy(app)
migrate = Migrate(app, db)

#----------------------------------------------------------------------------#
# Models.
#----------------------------------------------------------------------------#

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
  
#----------------------------------------------------------------------------#
# Filters.
#----------------------------------------------------------------------------#

def format_datetime(value, format='medium'):
  date = dateutil.parser.parse(value)
  if format == 'full':
      format="EEEE MMMM, d, y 'at' h:mma"
  elif format == 'medium':
      format="EE MM, dd, y h:mma"
  return babel.dates.format_datetime(date, format, locale='en')

app.jinja_env.filters['datetime'] = format_datetime

#----------------------------------------------------------------------------#
# Controllers.
#----------------------------------------------------------------------------#

@app.route('/')
def index():
  return render_template('pages/home.html')

#  Venues
#  ----------------------------------------------------------------

@app.route('/venues')
def venues():
  today = datetime.now()
  
  cities_states = Venue.query.distinct(Venue.city, Venue.state).all()
  
  data = []
  for city_state in cities_states:
    venues = Venue.query.filter_by(city=city_state.city, state=city_state.state).all()
    
    for venue in venues:
      venue.num_upcoming_shows = len(venue.get_upcoming_shows(today))
    
    data.append({"city": city_state.city, 
                "state": city_state.state, 
                "venues": venues
                })
  
  return render_template('pages/venues.html', areas=data)

@app.route('/venues/search', methods=['POST'])
def search_venues():
  today = datetime.now()
  
  search_term = request.form.get('search_term', '')
  
  venues = Venue.query.filter(Venue.name.ilike(f"%{search_term}%")).all()
  
  for venue in venues:
    venue.num_upcoming_shows = len(venue.get_upcoming_shows(today))
  
  response = {'count':len(venues),
              'data': venues}
  
  return render_template('pages/search_venues.html', results=response, search_term=search_term)

@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
  today = datetime.now()
  
  data = Venue.query.get(venue_id)
  data.genres = data.genres.split(",")
  
  data.past_shows = data.get_past_shows(today)
  data.past_shows_count = len(data.past_shows)
  data.upcoming_shows = data.get_upcoming_shows(today)
  data.upcoming_shows_count = len(data.upcoming_shows)
  
  # Convert start_time to string
  past_shows = data.past_shows
  upcoming_shows = data.upcoming_shows
  shows = past_shows + upcoming_shows
  for show in shows:
    show.start_time = str(show.start_time)
  
  return render_template('pages/show_venue.html', venue=data)

#  Create Venue
#  ----------------------------------------------------------------

@app.route('/venues/create', methods=['GET'])
def create_venue_form():
  form = VenueForm()
  return render_template('forms/new_venue.html', form=form)

@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
  data = request.form.to_dict()
  
  genres_list = request.form.getlist('genres')
  genres_as_string = ','.join(genres_list)
  data['genres'] = genres_as_string
    
  error = False
  try:  
    venue = Venue()
    venue.update(data)
    
    db.session.add(venue)
    db.session.commit()
    flash('Venue ' + request.form['name'] + ' was successfully listed!')
  except:
    db.session.rollback()
    error = True
    print(sys.exc_info())
    flash('An error occurred. Venue ' + data.name + ' could not be listed.')
  finally:
    db.session.close()
  if error: 
    abort(400)
  else:
    return render_template('pages/home.html')

@app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
  error = False
  try:
    venue = Venue.query.get(venue_id)
    db.session.delete(venue)
    db.session.commit()
  except:
    db.session.rollback()
    error = True
    print(sys.exc_info())
  finally:
    db.session.close()
  if error: 
    abort(500)
  else:
    return '', 200

#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():
  data = Artist.query.all()
  return render_template('pages/artists.html', artists=data)

@app.route('/artists/search', methods=['POST'])
def search_artists():
  today = datetime.now()
  
  search_term = request.form.get('search_term', '')
  
  artists = Artist.query.filter(Artist.name.ilike(f"%{search_term}%")).all()
  
  for artist in artists:
    artist.num_upcoming_shows = len(artist.get_upcoming_shows(today))
  
  response = {'count':len(artists),
              'data': artists}
  
  return render_template('pages/search_artists.html', results=response, search_term=search_term)

@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
  today = datetime.now()
  
  data = Artist.query.get(artist_id)
  data.genres = data.genres.split(",")
  
  data.past_shows = data.get_past_shows(today)
  data.past_shows_count = len(data.past_shows)
  data.upcoming_shows = data.get_upcoming_shows(today)
  data.upcoming_shows_count = len(data.upcoming_shows)
  
  # Convert start_time to string
  past_shows = data.past_shows
  upcoming_shows = data.upcoming_shows
  
  shows = past_shows + upcoming_shows
  
  for show in shows:
    show.start_time = str(show.start_time)
  
  return render_template('pages/show_artist.html', artist=data)

#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
  form = ArtistForm()
  artist = Artist.query.get(artist_id)
  return render_template('forms/edit_artist.html', form=form, artist=artist)

@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
  error = False
  try:
    data = request.form.to_dict()
    
    genres_list = request.form.getlist('genres') 
    genres_as_string = ','.join(genres_list)
    data['genres'] = genres_as_string
  
    artist = Artist.query.get(artist_id)
    artist.update(data)
  
    db.session.add(artist)
    db.session.commit() 
  except:
    db.session.rollback()
    error = True
    print(sys.exc_info())
  finally:
    db.session.close()
  if error: 
    abort(400)
  else:
    return redirect(url_for('show_artist', artist_id=artist_id))
  

@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
  form = VenueForm()
  venue = Venue.query.get(venue_id)
  return render_template('forms/edit_venue.html', form=form, venue=venue)

@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
  error = False
  try:
    data = request.form.to_dict()
  
    genres_list = request.form.getlist('genres') 
    genres_as_string = ','.join(genres_list)
    data['genres'] = genres_as_string
  
    venue = Venue.query.get(venue_id)
    venue.update(data)
  
    db.session.add(venue)
    db.session.commit()
  except:
    db.session.rollback()
    error = True
    print(sys.exc_info())
  finally:
    db.session.close()
  if error: 
    abort(400)
  else:
    return redirect(url_for('show_venue', venue_id=venue_id))

#  Create Artist
#  ----------------------------------------------------------------

@app.route('/artists/create', methods=['GET'])
def create_artist_form():
  form = ArtistForm()
  return render_template('forms/new_artist.html', form=form)

@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
  data = request.form.to_dict()
  
  genres_list = request.form.getlist('genres')
  genres_as_string = ','.join(genres_list)
  data['genres'] = genres_as_string
    
  error = False
  try:
    artist = Artist()
    artist.update(data)
  
    db.session.add(artist)
    db.session.commit()
    flash('Artist ' + request.form['name'] + ' was successfully listed!')
  except:
    db.session.rollback()
    error = True
    print(sys.exc_info())
    flash('An error occurred. Artist ' + data.name + ' could not be listed.')
  finally:
    db.session.close()
  if error: 
    abort(400)
  else:
    return render_template('pages/home.html')
  
#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
  data = Show.query.all()
  
  for show in data:
    show.start_time = str(show.start_time)
    show.venue_name = show.venues.name
    show.artist_name = show.artists.name
    show.artist_image_link = show.artists.image_link
    
  return render_template('pages/shows.html', shows=data)

@app.route('/shows/create')
def create_shows():
  form = ShowForm()
  return render_template('forms/new_show.html', form=form)

@app.route('/shows/create', methods=['POST'])
def create_show_submission():
  error = False
  try:
    data = request.form
    
    show = Show()
    show.update(data)
    
    db.session.add(show)
    db.session.commit()
    flash('Show was successfully listed!')
  except:
    db.session.rollback()
    error = True
    print(sys.exc_info())
    flash('An error occurred. Show could not be listed.')
  finally:
    db.session.close()
  if error: 
    abort(400)
  else:
    return render_template('pages/home.html')

@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def server_error(error):
    return render_template('errors/500.html'), 500

if not app.debug:
    file_handler = FileHandler('error.log')
    file_handler.setFormatter(
        Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
    )
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info('errors')

#----------------------------------------------------------------------------#
# Launch.
#----------------------------------------------------------------------------#

# Default port:
if __name__ == '__main__':
    app.run()

# Or specify port manually:
'''
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
'''
