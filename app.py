#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

import babel
import dateutil.parser
import logging
import sys

from datetime import datetime
from flask import Flask, render_template, request, flash, redirect, url_for, abort
from flask_migrate import Migrate
from flask_moment import Moment
from flask_wtf import Form
from forms import *
from logging import Formatter, FileHandler
from models import Artist, Venue, Show, db


#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')
db.init_app(app)
migrate = Migrate(app, db)
  
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
  today = datetime.today()
  
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
  today = datetime.today()
  
  search_term = request.form.get('search_term', '')
  
  venues = Venue.query.filter(Venue.name.ilike(f"%{search_term}%")).all()
  
  for venue in venues:
    venue.num_upcoming_shows = len(venue.get_upcoming_shows(today))
  
  response = {'count':len(venues),
              'data': venues}
  
  return render_template('pages/search_venues.html', results=response, search_term=search_term)

@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
  today = datetime.today()
  
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
  form = VenueForm(request.form, meta={'csrf': False})
  if form.validate():
    try:
      data = request.form.to_dict()
    
      genres_list = request.form.getlist('genres')
      genres_as_string = ','.join(genres_list)
      data['genres'] = genres_as_string
      
      venue = Venue()
      venue.update(data)
      
      db.session.add(venue)
      db.session.commit()
      flash('Venue ' + request.form['name'] + ' was successfully listed!')
    except:
      db.session.rollback()
      print(sys.exc_info())
      flash('An error occurred. Venue ' + request.form['name'] + ' could not be listed.')
    finally:
      db.session.close()
  else:
    message = []
    for _, err in form.errors.items():
        message.append(' '.join(err))
    flash('Errors ' + str(message) + '. Venue could not be listed.')
  
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
  today = datetime.today()
  
  search_term = request.form.get('search_term', '')
  
  artists = Artist.query.filter(Artist.name.ilike(f"%{search_term}%")).all()
  
  for artist in artists:
    artist.num_upcoming_shows = len(artist.get_upcoming_shows(today))
  
  response = {'count':len(artists),
              'data': artists}
  
  return render_template('pages/search_artists.html', results=response, search_term=search_term)

@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
  today = datetime.today()
  
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
  form = ArtistForm(request.form, meta={'csrf': False})
  if form.validate():
    try:
      data = request.form.to_dict()
      
      genres_list = request.form.getlist('genres') 
      genres_as_string = ','.join(genres_list)
      data['genres'] = genres_as_string
    
      artist = Artist.query.get(artist_id)
      artist.update(data)
    
      db.session.add(artist)
      db.session.commit() 
      
      return redirect(url_for('show_artist', artist_id=artist_id))
    except:
      db.session.rollback()
      print(sys.exc_info())
      flash('An error occurred. Artist ' + request.form['name'] + ' could not be updated.')
    finally:
      db.session.close()
  else:
    message = []
    for _, err in form.errors.items():
        message.append(' '.join(err))
    flash('Errors ' + str(message) + '. Artist could not be updated.')
  
  return render_template('pages/home.html')

@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
  form = VenueForm()
  venue = Venue.query.get(venue_id)
  return render_template('forms/edit_venue.html', form=form, venue=venue)

@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
  form = VenueForm(request.form, meta={'csrf': False})
  if form.validate():
    try:
      data = request.form.to_dict()
    
      genres_list = request.form.getlist('genres') 
      genres_as_string = ','.join(genres_list)
      data['genres'] = genres_as_string
    
      venue = Venue.query.get(venue_id)
      venue.update(data)
    
      db.session.add(venue)
      db.session.commit()
      
      return redirect(url_for('show_venue', venue_id=venue_id))
    except:
      db.session.rollback()
      error = True
      print(sys.exc_info())
      flash('An error occurred. Venue ' + request.form['name'] + ' could not be updated.')
    finally:
      db.session.close()
  else:
    message = []
    for _, err in form.errors.items():
        message.append(' '.join(err))
    flash('Errors ' + str(message) + '. Venue could not be updated.')
    
  return render_template('pages/home.html')

#  Create Artist
#  ----------------------------------------------------------------

@app.route('/artists/create', methods=['GET'])
def create_artist_form():
  form = ArtistForm()
  return render_template('forms/new_artist.html', form=form)

@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
  form = ArtistForm(request.form, meta={'csrf': False})
  if form.validate():
    try:
      data = request.form.to_dict()
    
      genres_list = request.form.getlist('genres')
      genres_as_string = ','.join(genres_list)
      data['genres'] = genres_as_string
    
      artist = Artist()
      artist.update(data)
    
      db.session.add(artist)
      db.session.commit()
      flash('Artist ' + request.form['name'] + ' was successfully listed!')
    except:
      db.session.rollback()
      print(sys.exc_info())
      flash('An error occurred. Artist ' + request.form['name'] + ' could not be listed.')
    finally:
      db.session.close()
  else:
    message = []
    for _, err in form.errors.items():
        message.append(' '.join(err))
    flash('Errors ' + str(message) + '. Artist could not be listed.')
  
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
  try:
    data = request.form
    
    show = Show()
    show.update(data)
    
    db.session.add(show)
    db.session.commit()
    flash('Show was successfully listed!')
  except:
    db.session.rollback()
    print(sys.exc_info())
    flash('An error occurred. Show could not be listed.')
  finally:
    db.session.close()
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