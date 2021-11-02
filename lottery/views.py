# IMPORTS
import logging
import copy
from flask import Blueprint, render_template, request, flash
from flask_login import login_required, current_user
from app import db, requires_roles
from models import Draw, User

# CONFIG
lottery_blueprint = Blueprint('lottery', __name__, template_folder='templates')

# VIEWS
# view lottery page
@lottery_blueprint.route('/lottery')
@login_required
@requires_roles('user')
def lottery():
    return render_template('lottery.html')


@lottery_blueprint.route('/add_draw', methods=['POST'])
@login_required
@requires_roles('user')
def add_draw():
    submitted_draw = ''
    for i in range(6):
        submitted_draw += request.form.get('no' + str(i + 1)) + ' '
    submitted_draw.strip()

    # create a new draw with the form data.
    new_draw = Draw(user_id=current_user.id, draw=submitted_draw, win=False, round=0, drawkey=current_user.drawkey)

    # add the new draw to the database
    db.session.add(new_draw)
    db.session.commit()

    # re-render lottery.page
    flash('Draw %s submitted.' % submitted_draw)
    return lottery()


# view all draws that have not been played
@lottery_blueprint.route('/view_draws', methods=['POST'])
@login_required
@requires_roles('user')
def view_draws():

    # get all draws that have not been played [played=0]
    playable_draws = Draw.query.filter_by(played=False, user_id=current_user.id).all()

    # creates a list of copied draw objects which are independent of database.
    draw_copies = list(map(lambda x: copy.deepcopy(x), playable_draws))

    # empty list for decrypted copied draw objects
    decrypted_draws = []

    # decrypt each copied draw object and add it to decrypted_draws array.
    for d in draw_copies:
        user = User.query.filter_by(id=d.user_id).first()
        d.view_draw(user.drawkey)
        decrypted_draws.append(d)

    # if playable draws exist
    if len(decrypted_draws) != 0:
        # re-render lottery page with playable draws
        return render_template('lottery.html', playable_draws=decrypted_draws)
    else:
        flash('No playable draws.')
        return lottery()


# view lottery results
@lottery_blueprint.route('/check_draws', methods=['POST'])
@login_required
@requires_roles('user')
def check_draws():
    # get played draws
    played_draws = Draw.query.filter_by(played=True, user_id=current_user.id).all()

    # creates a list of copied draw objects which are independent of database.
    played_draw_copies = list(map(lambda x: copy.deepcopy(x), played_draws))

    # empty list for decrypted copied draw objects
    decrypted_played_draws = []

    # decrypt each copied draw object and add it to decrypted_played_draws array.
    for d in played_draw_copies:
        user = User.query.filter_by(id=d.user_id).first()
        d.view_draw(user.drawkey)
        decrypted_played_draws.append(d)

    # if played draws exist
    if len(decrypted_played_draws) != 0:
        return render_template('lottery.html', results=decrypted_played_draws, played=True)

    # if no played draws exist [all draw entries have been played therefore wait for next lottery round]
    else:
        flash("Next round of lottery yet to play. Check you have playable draws.")
        return lottery()


# delete all played draws
@lottery_blueprint.route('/play_again', methods=['POST'])
@login_required
@requires_roles('user')
def play_again():
    delete_played = Draw.__table__.delete().where(Draw.played).where(Draw.user_id == current_user.id)  # TODO: delete played draws for current user only
    db.session.execute(delete_played)
    db.session.commit()

    flash("All played draws deleted.")
    return lottery()


