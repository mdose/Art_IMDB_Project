"""Utility file to seed masterpieces database from seed_data/"""

from sqlalchemy import func
from model import Art
from model import Artist
from model import ArtType
from model import Collection
from model import ArtMovement
from model import SubjectMatter
from model import ArtistArt
from model import User
from model import Label
from model import LabelArt
from model import connect_to_db, db
from server import app
import io
import os
from passlib.hash import pbkdf2_sha256
# import VisionAPIcredentials.json

# Imports the Google Cloud client library
from google.cloud import vision
from google.cloud.vision import types

# GOOGLE_APPLICATION_CREDENTIALS = VisionAPIcredentials.json

# Instantiate Vision API
client = vision.ImageAnnotatorClient()


def load_art():
    """Load artworks from u.art into database."""

    print "Art"

    # Delete all rows in table, so if we need to run this a second time,
    # we won't be trying to add duplicate art
    Art.query.delete()

    # Read u.art file and insert data
    for row in open("seed_data/u.art"):
        # NOTE: Google puts carriage return \n AND new feed combo at the end of
        # coverted tvs files (hence the janky fix).
        # Possible TO DO: refactor with built-in cvs module (using tvs for now b/c of commas)
        # ALSO: look into range data types for Postgresql to make date searching eaiser
        row = row.rstrip("\n").strip(chr(13))
        row = row.split("\t")
        art_id = row[0]
        title = row[1]
        image_path = row[2]
        circa = row[3]
        year = row[4] if row[4] else None
        year_range = row[5] if row[5] else None
        year_description = row[6]
        medium = row[7]
        description = row[8]
        height_cm = row[9]
        width_cm = row[10] if row[10] else None
        art_type_id = row[11]
        collection_id = row[12]
        art_movement_id = row[13]
        subject_matter_id = row[14]
        artist_id = row[15]

        art = Art(art_id=art_id, title=title, image=image_path, circa=circa,
                  year=year, year_range=year_range, year_description=year_description,
                  medium=medium, description=description, height_cm=height_cm,
                  width_cm=width_cm, art_type_id=art_type_id, collection_id=collection_id,
                  art_movement_id=art_movement_id, subject_matter_id=subject_matter_id)

        # We need to add to the session or it won't ever be stored
        db.session.add(art)

        # Once we're done, we should commit our work
        db.session.commit()

        new_artist_artwork = ArtistArt(art_id=art_id, artist_id=artist_id)

        print "Artists Artworks"

        db.session.add(new_artist_artwork)

        db.session.commit()

        # for each artwork get labels from Vision API and then insert each label
        load_labels(art, image_path)

        print "Labels"


def load_labels(art, image_path):
    # this is where you use the vision api to get the list of labels
    # labels = junk
    # for label in labels:
    #    insert label.description into db

    # for each artwork run everything below
    # The name of the image file to annotate
    image_path = image_path[1:]

    file_name = os.path.join(os.path.dirname(__file__), image_path)

        # Loads the image into memory
    with io.open(file_name, 'rb') as image_file:
        content = image_file.read()

    image = types.Image(content=content)
    # Performs label detection on the image file
    response = client.label_detection(image=image)
    labels = response.label_annotations

    # print "labels for", image_path.split('/')[-1]
    for label in labels:
        attach_label_to_art(art, label)
        # print(label.description)

def attach_label_to_art(art, vision_label):
    """"""

    if vision_label.score < 0.7:
        return

    label = find_or_create_label(vision_label)

    new_label_art = LabelArt(art_id=art.art_id, label_id=label.label_id, score=vision_label.score)

    print "LabelArt"

    db.session.add(new_label_art)

    db.session.commit()

def find_or_create_label(vision_label):
    """"""

    label = Label.query.filter(Label.label == vision_label.description).first()

    if not label:
        label = Label(label=vision_label.description)
        db.session.add(label)
        db.session.commit()

    return label

def load_artists():
    """Load artists from u.artists into database."""

    print "Artists"

    Artist.query.delete()

    for row in open("seed_data/u.artists"):
        row = row.rstrip("\n").strip(chr(13))
        row = row.split("\t")
        # NOTE: look into range data types in Postgresql to make searching for years eaiser
        artist_id = row[0]
        primary_name = row[1]
        secondary_name = row[2] if row[2] else None
        birth_year = row[3] if row[3] else None
        death_year = row[4] if row[4] else None
        bio = row[5]
        image_url = row[6] if row[6] else None
        image_caption = row[7] if row[7] else None

        artist = Artist(artist_id=artist_id, primary_name=primary_name,
                        secondary_name=secondary_name, birth_year=birth_year,
                        death_year=death_year, bio=bio, image_url=image_url,
                        image_caption=image_caption)

        db.session.add(artist)

    db.session.commit()


def load_art_types():
    """Load art types from u.art_types into database."""

    print "Art Types"

    ArtType.query.delete()

    for row in open("seed_data/u.art_types"):
        row = row.rstrip("\n").strip(chr(13))
        row = row.split("\t")
        art_type_id, art_type = row

        art_type = ArtType(art_type_id=art_type_id, art_type=art_type)
        db.session.add(art_type)

    db.session.commit()


def load_collections():
    """Load collections from u.collecetions into database."""

    print "Collections"

    Collection.query.delete()

    for row in open("seed_data/u.collections"):
        row = row.rstrip("\n").strip(chr(13))
        row = row.split("\t")
        collection_id, name, location, image_url, address, lat, lng, website = row

        collection = Collection(collection_id=collection_id, name=name,
                                location=location, image_url=image_url,
                                address=address, lat=lat, lng=lng, website=website)
        db.session.add(collection)

    db.session.commit()


def load_art_movements():
    """Load art movements from u.art_movements into database."""

    print "Art Movements"

    ArtMovement.query.delete()

    for row in open("seed_data/u.art_movements"):
        row = row.rstrip("\n").strip(chr(13))
        row = row.split("\t")
        # make sure to add descriptions to the table and add an extra "description"
        # variable to unpacked
        art_movement_id, movement_name = row

        art_movement = ArtMovement(art_movement_id=art_movement_id,
                                   movement_name=movement_name)
        db.session.add(art_movement)

    db.session.commit()


def load_subject_matters():
    """Load subject matters from u.subject_matters into database."""

    print "Subject Matters"

    SubjectMatter.query.delete()

    for row in open("seed_data/u.subject_matters"):
        row = row.rstrip("\n").strip(chr(13))
        row = row.split("\t")
        subject_matter_id, category = row

        subject_matter = SubjectMatter(subject_matter_id=subject_matter_id,
                                       category=category)
        db.session.add(subject_matter)

    db.session.commit()


def load_users():
    """Load test users from u.user into database"""

    print "Users"

    User.query.delete()

    for row in open("seed_data/u.users"):
        row = row.rstrip("\n").strip(chr(13))
        row = row.split("\t")
        user_id, email, password, username = row
        hashed = pbkdf2_sha256.hash(password)
        del password

        user = User(user_id=user_id, email=email, password=hashed,
                    username=username)
        db.session.add(user)

    db.session.commit()


def set_val_user_id():
    """Set value for the next user_id after seeding database"""

    # Get the Max user_id in the database
    result = db.session.query(func.max(User.user_id)).one()
    max_id = int(result[0])

    # Set the value for the next user_id to be max_id + 1
    query = "SELECT setval('users_user_id_seq', :new_id)"
    db.session.execute(query, {'new_id': max_id + 1})
    db.session.commit()

##############################################################################
# for 3.0 add more info to db forms; the "set_val_user_id" is for if it's just one
# table. If more than one, Katie has a solution to make more d.r.y. with special
# func she sent via Slack!


if __name__ == "__main__":
    connect_to_db(app)

    # In case tables haven't been created, create them
    db.drop_all()
    db.create_all()

    # Import different types of data
    load_art_types()
    load_collections()
    load_art_movements()
    load_subject_matters()
    load_artists()
    load_art()
    load_users()
    set_val_user_id()
