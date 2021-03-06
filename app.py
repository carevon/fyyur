#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

import json
from time import timezone
from typing import final
import dateutil.parser
from datetime import datetime, timezone, timedelta
import sys
import babel
from flask import Flask, render_template, request, Response, flash, redirect, url_for
from flask_moment import Moment
from flask_migrate import Migrate
from flask_wtf.csrf import CSRFProtect
import logging
from logging import Formatter, FileHandler
from wtforms import Form
from models import Venue, Artist, Show, db
from forms import *
#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')
csrf = CSRFProtect(app)
csrf.init_app(app)
db.init_app(app)
migrate = Migrate(app, db)

#----------------------------------------------------------------------------#
# Filters.
#----------------------------------------------------------------------------#

def format_datetime(value, format='medium'):
  if isinstance(value, str):
    date = dateutil.parser.parse(value)
  else:
    date = value

  if format == 'full':
      format="EEEE MMMM, d, y 'at' h:mma"
  elif format == 'medium':
      format="EE MM, dd, y h:mma"
  return babel.dates.format_datetime(date, format, locale='en')

app.jinja_env.filters['datetime'] = format_datetime

def fix_json_array(obj, attr):
    arr = getattr(obj, attr)
    if isinstance(arr, list) and len(arr) > 1 and arr[0] == '{':
        arr = arr[1:-1]
        arr = ''.join(arr).split(",")
        setattr(obj,attr, arr)

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
  # DONE: replace with real venues data.
  #       num_shows should be aggregated based on number of upcoming shows per venue.
  data = []
  for city, state in db.session.query(Venue.city, Venue.state).distinct():
    data.append({
      "city": city,
      "state": state,
      "venues": Venue.query.filter_by(city=city)
    })
  return render_template('pages/venues.html', areas=data);

@app.route('/venues/search', methods=['POST'])
def search_venues():
  # DONE: implement search on artists with partial string search. Ensure it is case-insensitive.
  # seach for Hop should return "The Musical Hop".
  # search for "Music" should return "The Musical Hop" and "Park Square Live Music & Coffee"

  search_term = request.form.get('search_term')
  venues = Venue.query
  if search_term != None or search_term != ''.strip():
    search_term = "%{}%".format(request.form.get('search_term'))
    venues = Venue.query.filter(Venue.name.ilike(search_term))
  
  venues = venues.order_by(Venue.name).all()

  response={
    "count": len(venues),
    "data": venues
  }
  return render_template('pages/search_venues.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
  # shows the venue page with the given venue_id
  # DONE: replace with real venue data from the venues table, using venue_id

  venue = Venue.query.filter_by(id=venue_id).first()
  fix_json_array(venue, "genres")
  if not venue: 
    return render_template('errors/404.html')

  past_shows = []
  upcoming_shows = []
  for show in venue.shows:
    show = {
      "artist_id": show.artist_id,
      "artist_name": show.artist.name,
      "artist_image_link": show.artist.image_link,
      "start_time": show.start_time
    }
    if show["start_time"] <= datetime.now(timezone(timedelta(hours=-3))):
      past_shows.append(show)
    else:
      upcoming_shows.append(show)

  data = {
    "id": venue.id,
    "name": venue.name,
    "genres": venue.genres,
    "address": venue.address,
    "city": venue.city,
    "state": venue.state,
    "phone": venue.phone,
    "website": venue.website,
    "facebook_link": venue.facebook_link,
    "seeking_talent": venue.seeking_talent,
    "seeking_description": venue.seeking_description,
    "image_link": venue.image_link,
    "past_shows": past_shows,
    "past_shows_count": len(past_shows),
    "upcoming_shows": upcoming_shows,
    "upcoming_shows_count": len(upcoming_shows)
  }
  return render_template('pages/show_venue.html', venue=data)

#  Create Venue
#  ----------------------------------------------------------------

@app.route('/venues/create', methods=['GET'])
def create_venue_form():
  form = VenueForm()
  return render_template('forms/new_venue.html', form=form)

@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
  # DONE: insert form data as a new Venue record in the db, instead
  # DONE: modify data to be the data object returned from db insertion
  error = False
  form = VenueForm()
  try:
    if form.validate_on_submit():
      name = request.form['name']
      city = request.form['city']
      state = request.form['state']
      address = request.form['address']
      phone = request.form['phone']
      genres = request.form.getlist('genres')
      fb_link = request.form['facebook_link']
      img_link = request.form['image_link']
      website_link = request.form['website_link']
      seeking_talent = True if 'seeking_talent' in request.form else False
      seeking_description = request.form['seeking_description']

      venue = Venue(name=name, city=city, state=state, address=address, phone=phone, 
      genres=genres, facebook_link=fb_link, image_link=img_link, website=website_link, 
      seeking_talent=seeking_talent, seeking_description=seeking_description, 
      created_at=datetime.now(timezone(timedelta(hours=-3))), 
      updated_at=datetime.now(timezone(timedelta(hours=-3))))
      db.session.add(venue)
      db.session.commit()
    else:
      for e in form.errors:
        flash('An error has occurred. {}'.format(form.errors[e]))
      db.session.rollback()
      return render_template('pages/home.html')
  except:
    error = True
    db.session.rollback()
    print(sys.exc_info())
  finally:
    db.session.close()
  
  # DONE: on unsuccessful db insert, flash an error instead.
  if error:
    flash('An error has occurred. Venue {} could not be listed.'.format(request.form['name']))
  else: # on successful db insert, flash success
    flash('Venue {} was successfully listed.'.format(request.form['name']))

  # e.g., flash('An error occurred. Venue ' + data.name + ' could not be listed.')
  # see: http://flask.pocoo.org/docs/1.0/patterns/flashing/
  return render_template('pages/home.html')

@app.route('/venues/<int:venue_id>/remove', methods=['GET'])
def delete_venue(venue_id):
  # DONE: Complete this endpoint for taking a venue_id, and using
  # SQLAlchemy ORM to delete a record. Handle cases where the session commit could fail.
  error = False
  try:
    venue = Venue.query.get(venue_id)
    if venue:
      db.session.delete(venue)
      db.session.commit()
    else:
      error = True
  except:
    error = True
    db.session.rollback()
    print(sys.exc_info())
  finally:
    db.session.close()
  if error:
    flash('An error has occurred. Venue could not be deleted.')
  else:
    flash('Venue was successfully deleted.')
  # BONUS CHALLENGE: Implement a button to delete a Venue on a Venue Page, have it so that
  # clicking that button delete it from the db then redirect the user to the homepage
  return render_template('pages/home.html')

#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():
  # DONE: replace with real data returned from querying the database
  data = Artist.query.order_by(Artist.id).all()
  return render_template('pages/artists.html', artists=data)

@app.route('/artists/search', methods=['POST'])
def search_artists():
  # DONE: implement search on artists with partial string search. Ensure it is case-insensitive.
  # seach for "A" should return "Guns N Petals", "Matt Quevado", and "The Wild Sax Band".
  # search for "band" should return "The Wild Sax Band".

  search_term = request.form.get('search_term')
  artists = Artist.query
  if search_term != None or search_term != ''.strip():
    search_term = "%{}%".format(request.form.get('search_term'))
    artists = Artist.query.filter(Artist.name.ilike(search_term))
  
  artists = artists.order_by(Artist.name).all()
  response={
    "count": len(artists),
    "data": artists
  }
  return render_template('pages/search_artists.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
  # shows the artist page with the given artist_id
  # DONE: replace with real artist data from the artist table, using artist_id
  artist = Artist.query.filter_by(id=artist_id).first()
  fix_json_array(artist, "genres")

  if not artist: 
    return render_template('errors/404.html')

  past_shows = []
  upcoming_shows = []
  for show in artist.shows:
    show = {
      "venue_id": show.venue_id,
      "venue_name": show.venue.name,
      "venue_image_link": show.venue.image_link,
      "start_time": show.start_time
    }
    if show["start_time"] <= datetime.now(timezone(timedelta(hours=-3))):
      past_shows.append(show)
    else:
      upcoming_shows.append(show)

  data = {
    "id": artist.id,
    "name": artist.name,
    "genres": artist.genres,
    "city": artist.city,
    "state": artist.state,
    "phone": artist.phone,
    "seeking_venue": artist.seeking_venue,
    "seeking_description": artist.seeking_description,
    "facebook_link": artist.facebook_link,
    "website": artist.website,
    "image_link": artist.image_link,
    "past_shows": past_shows,
    "past_shows_count": len(past_shows),
    "upcoming_shows": upcoming_shows,
    "upcoming_shows_count": len(upcoming_shows)
  }

  return render_template('pages/show_artist.html', artist=data)

@app.route('/artists/<artist_id>/remove', methods=['GET'])
def delete_artist(artist_id):
  # DONE: Complete this endpoint for taking a artist_id, and using
  # SQLAlchemy ORM to delete a record. Handle cases where the session commit could fail.
  error = False
  try:
    artist = Artist.query.get(artist_id)
    if artist:
      db.session.delete(artist)
      db.session.commit()
    else:
      error = True
  except:
    error = True
    db.session.rollback()
    print(sys.exc_info())
  finally:
    db.session.close()
  if error:
    flash('An error has occurred. Artist could not be deleted.')
  else:
    flash('Artist was successfully deleted.')
  return render_template('pages/home.html')

#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
  # DONE: populate form with fields from artist with ID <artist_id>
  form = ArtistForm()
  artist = Artist.query.get(artist_id)
  if artist:
    fix_json_array(artist, "genres")
    form.name.data = artist.name
    form.city.data = artist.city
    form.state.data = artist.state
    form.phone.data = artist.phone
    form.genres.data = artist.genres
    form.facebook_link.data = artist.facebook_link
    form.image_link.data = artist.image_link
    form.website_link.data = artist.website
    form.seeking_venue.data = artist.seeking_venue
    form.seeking_description.data = artist.seeking_description
  else:
    flash('Artist was not found.')
    render_template('pages/artists.html')
  return render_template('forms/edit_artist.html', form=form, artist=artist)

@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
  # DONE: take values from the form submitted, and update existing
  # artist record with ID <artist_id> using the new attributes
  error = False
  form = ArtistForm()
  try: 
    if form.validate_on_submit():
      artist = Artist.query.get(artist_id)
      artist.name = request.form['name']
      artist.city = request.form['city']
      artist.state = request.form['state']
      artist.phone = request.form['phone']
      artist.genres = request.form.getlist('genres')
      artist.facebook_link = request.form['facebook_link']
      artist.image_link = request.form['image_link']
      artist.website = request.form['website_link']
      artist.seeking_venue = True if 'seeking_venue' in request.form else False
      artist.seeking_description = request.form['seeking_description']
      artist.updated_at = datetime.now(timezone(timedelta(hours=-3)))
      db.session.commit()
    else:
      for e in form.errors:
        flash('An error has occurred. {}'.format(form.errors[e]))
      db.session.rollback()
      return render_template('pages/edit_artist.html')
  except:
    error = True
    db.session.rollback()
    print(sys.exc_info())
  finally:
    db.session.close()
  return redirect(url_for('show_artist', artist_id=artist_id))

@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
  # DONE: populate form with values from venue with ID <venue_id>
  form = VenueForm()
  venue = Venue.query.get(venue_id)
  if venue:
    fix_json_array(venue, "genres")
    form.name.data = venue.name
    form.city.data = venue.city
    form.state.data = venue.state
    form.address.data = venue.address
    form.phone.data = venue.phone
    form.genres.data = venue.genres
    form.facebook_link.data = venue.facebook_link
    form.image_link.data = venue.image_link
    form.website_link.data = venue.website
    form.seeking_talent.data = venue.seeking_talent
    form.seeking_description.data = venue.seeking_description
  else:
    flash('Venue was not found.')
    return render_template('pages/venues.html')
  return render_template('forms/edit_venue.html', form=form, venue=venue)

@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
  # DONE: take values from the form submitted, and update existing
  # venue record with ID <venue_id> using the new attributes
  error = False
  form = VenueForm()
  try:
    if form.validate_on_submit():
      venue = Venue.query.get(venue_id)
      venue.name = request.form['name']
      venue.city = request.form['city']
      venue.state = request.form['state']
      venue.address = request.form['address']
      venue.phone = request.form['phone']
      venue.genres = request.form.getlist('genres')
      venue.fb_link = request.form['facebook_link']
      venue.img_link = request.form['image_link']
      venue.website_link = request.form['website_link']
      venue.seeking_talent = True if 'seeking_talent' in request.form else False
      venue.seeking_description = request.form['seeking_description']
      venue.updated_at = datetime.now(timezone(timedelta(hours=-3)))
      db.session.commit()
    else:
      for e in form.errors:
          flash('An error has occurred. {}'.format(form.errors[e]))
      db.session.rollback()
      return render_template('pages/edit_venue.html')
  except:
    error = True
    db.session.rollback()
    print(sys.exc_info())
  finally:
    db.session.close()
  return redirect(url_for('show_venue', venue_id=venue_id))

#  Create Artist
#  ----------------------------------------------------------------

@app.route('/artists/create', methods=['GET'])
def create_artist_form():
  form = ArtistForm()
  return render_template('forms/new_artist.html', form=form)

@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
  # called upon submitting the new artist listing form
  # DONE: insert form data as a new Venue record in the db, instead
  # DONE: modify data to be the data object returned from db insertion
  error = False
  form = ArtistForm()
  try:
    if form.validate_on_submit():
      name = request.form['name']
      city = request.form['city']
      state = request.form['state']
      phone = request.form['phone']
      genres = request.form.getlist('genres')
      fb_link = request.form['facebook_link']
      img_link = request.form['image_link']
      website_link = request.form['website_link']
      seeking_venue = True if 'seeking_venue' in request.form else False
      seeking_description = request.form['seeking_description']

      artist = Artist(name=name, city=city, state=state, phone=phone, 
      genres=genres, facebook_link=fb_link, image_link=img_link, website=website_link, 
      seeking_venue=seeking_venue, seeking_description=seeking_description, 
      created_at=datetime.now(timezone(timedelta(hours=-3))), 
      updated_at=datetime.now(timezone(timedelta(hours=-3))))

      db.session.add(artist)
      db.session.commit()
    else:
      for e in form.errors:
          flash('An error has occurred. {}'.format(form.errors[e]))
      db.session.rollback()
      return render_template('pages/artists.html')
  except:
    error = True
    db.session.rollback()
    print(sys.exc_info())
  finally:
    db.session.close()
  
  # DONE: on unsuccessful db insert, flash an error instead.
  # e.g., flash('An error occurred. Artist ' + data.name + ' could not be listed.')
  if error:
    flash('An error has occurred. Artist {} could not be listed.'.format(request.form['name']))
  else: # on successful db insert, flash success
    flash('Artist ' + request.form['name'] + ' was successfully listed!')
  return render_template('pages/home.html')


#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
  # displays list of shows at /shows
  # DONE: replace with real venues data.
  #       num_shows should be aggregated based on number of upcoming shows per venue.
  data = []
  shows = Show.query.all()
  for show in shows:
    data.append({
      "venue_id": show.venue.id,
      "venue_name": show.venue.name,
      "artist_id": show.artist.id,
      "artist_name": show.artist.name,
      "artist_image_link": show.artist.image_link,
      "start_time": show.start_time
    })

  return render_template('pages/shows.html', shows=data)

@app.route('/shows/create')
def create_shows():
  # renders form. do not touch.
  form = ShowForm()
  return render_template('forms/new_show.html', form=form)

@app.route('/shows/create', methods=['POST'])
def create_show_submission():
  # called to create new shows in the db, upon submitting new show listing form
  # DONE: insert form data as a new Show record in the db, instead
  error = False
  form = ShowForm()
  show_id = db.session.query(db.func.max(Show.id)).scalar()
  try:
    if form.validate_on_submit():
      id = show_id + 1
      venue_id = request.form['venue_id']
      artist_id = request.form['artist_id']
      start_time = request.form['start_time']

      show = Show(id=id, venue_id=venue_id, artist_id=artist_id, start_time=start_time, 
      created_at=datetime.now(timezone(timedelta(hours=-3))), 
      updated_at=datetime.now(timezone(timedelta(hours=-3))))
      
      db.session.add(show)
      db.session.commit()
    else:
      for e in form.errors:
          flash('An error has occurred. {}'.format(form.errors[e]))
      db.session.rollback()
      return render_template('pages/shows.html')
  except:
    error = True
    db.session.rollback()
    print(sys.exc_info())
  finally:
    db.session.close()
  
  # DONE: on unsuccessful db insert, flash an error instead.
  if error:
    flash('An error has occurred. Show could not be listed.')
  else: # on successful db insert, flash success
    flash('Show was successfully listed!')
  # e.g., flash('An error occurred. Show could not be listed.')
  # see: http://flask.pocoo.org/docs/1.0/patterns/flashing/
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
