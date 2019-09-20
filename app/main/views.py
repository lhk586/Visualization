from flask import render_template, redirect, url_for, abort, flash, request, jsonify
from flask_login import login_required, current_user
from . import main
from .forms import EditProfileForm, EditProfileAdminForm
from .. import db
from ..models import Role, User, Group
from ..decorators import admin_required

from urllib.parse import parse_qs
import csv, io

import numpy as np


@main.route('/')
def index():
    return render_template('index.html')

@main.route('/user/<username>')
def user(username):
    user = User.query.filter_by(username=username).first_or_404()
    return render_template('user.html', user=user)

@main.route('/edit-profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    form = EditProfileForm()
    if form.validate_on_submit():
        current_user.name = form.name.data
        current_user.location = form.location.data
        current_user.about_me = form.about_me.data
        db.session.add(current_user._get_current_object())
        db.session.commit()
        flash('Your profile has been updated.')
        return redirect(url_for('.user', username=current_user.username))
    form.name.data = current_user.name
    form.location.data = current_user.location
    form.about_me.data = current_user.about_me
    return render_template('edit_profile.html', form=form)


@main.route('/edit-profile/<int:id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_profile_admin(id):
    user = User.query.get_or_404(id)
    form = EditProfileAdminForm(user=user)
    if form.validate_on_submit():
        user.email = form.email.data
        user.username = form.username.data
        user.confirmed = form.confirmed.data
        user.role = Role.query.get(form.role.data)
        user.name = form.name.data
        user.location = form.location.data
        user.about_me = form.about_me.data
        db.session.add(user)
        db.session.commit()
        flash('The profile has been updated.')
        return redirect(url_for('.user', username=user.username))
    form.email.data = user.email
    form.username.data = user.username
    form.confirmed.data = user.confirmed
    form.role.data = user.role_id
    form.name.data = user.name
    form.location.data = user.location
    form.about_me.data = user.about_me
    return render_template('edit_profile.html', form=form, user=user)


@main.route('/<int:group_id>/upload', methods=["POST"])
@login_required
def upload_csv(group_id):
    group = Group.query.filter_by(id=group_id).first()
    group.upload = None
    f = request.files["dataset"]
    text = f.read().decode('utf8')
    upload = list(csv.reader(io.StringIO(text)))
    upload = list(upload[1:])
    upload = [[float(i) if '.' in i else int(i) for i in item] for item in upload]
    N = 5
    y_value = min([y for x, y in upload]), max([y for x, y in upload])
    group.upload = str(upload)
    group.N = N
    group.ymin = y_value[0]
    group.ymax = y_value[1]
    group_member = User.query.filter_by(group=group).all()
    for member in group_member:
        member.predict = None
    db.session.add(group)
    db.session.add_all(group_member)
    db.session.commit()
    return redirect('/')


@main.route('/submit/<int:user_id>', methods=["POST"])
@login_required
def submit_result(user_id):
    user = User.query.get(int(user_id))
    result = request.form["predict"]
    user.predict = result
    db.session.add(user)
    db.session.commit()
    return redirect('/')


@main.route('/get/member')
def get_member():
    group = Group.query.get(int(request.values['group']))
    member = User.query.filter_by(group=group).all()
    usernames = [m.username for m in member]
    roles = [m.role.name for m in member]
    predicts = [m.predict for m in member]
    N = group.N
    ymin = group.ymin
    ymax = group.ymax
    p = filter(lambda t: t is not None, predicts)
    p = [np.array(np.matrix(t).tolist()[0]).reshape(-1, 2) for t in p]
    n = len(p)
    if n == 0:
        p = p
        mean = []
        median = []
        quantile = []
    else:
        p = np.dstack(p)
        mean = str(np.mean(p, axis=-1).tolist())
        median = str(np.median(p, axis=-1).tolist())
        quantile = str(np.quantile(p,  np.arange(0, 1.1, 0.1), axis=-1).tolist())

    return jsonify({'usernames': usernames, "predicts": predicts,
                    'N': N, 'ymin': ymin, 'ymax': ymax, 'n': n, 'roles': roles,
                    'mean': mean, 'median': median, 'quantile': quantile})


@main.route('/list/user')
def get_user_list():
    user_role_list = User.query.filter_by(role=Role.query.filter_by(name="User").first()).all()
    usernames = [user.username for user in user_role_list]
    return jsonify({'usernames': usernames})


@main.route('/list/group')
def get_group_admin():
    group_admin_list = User.query.filter_by(role=Role.query.filter_by(name="Moderator").first()).order_by().all()
    adminnames = [admin.username for admin in group_admin_list]
    return jsonify({"adminnames": adminnames})


@main.route('/add/group', methods=["POST"])
def add_group():
    group = Group()
    username = request.form['user-list']
    user = User.query.filter_by(username=username).first()
    user.role = Role.query.filter_by(name="Moderator").first()
    user.group = group
    user.predict = None
    db.session.add_all([group, user])
    db.session.commit()
    return redirect('/')

@main.route('/delete/group', methods=["POST"])
def delete_group():
    username = request.form['group-list']
    g = User.query.filter_by(username=username).first().group
    member = User.query.filter_by(group=g).all()
    for m in member:
        m.role = Role.query.filter_by(name="User").first()
        m.group = None
        m.predict = None

    db.session.delete(g)
    db.session.add_all(member)
    db.session.commit()
    return redirect('/')

@main.route('/delete/member', methods=["POST"])
def delete_member():
    username = request.form['member-list']
    u = User.query.filter_by(username=username).first()

    u.group = None
    u.predict = None

    db.session.add(u)
    db.session.commit()
    return redirect('/')


@main.route('/add/member/<int:group_id>', methods=["POST"])
def add_member(group_id):
    group = Group.query.get(group_id)
    user = User.query.filter_by(username=request.form['user-list']).first()
    user.group = group
    user.predict = None
    db.session.add(user)
    db.session.commit()
    return redirect('/')


@main.route('/group')
def group():
    query = parse_qs(request.query_string.decode('utf8'))
    adminname = query["adminname"][0].rsplit('.', 1)[-1].strip()
    group = User.query.filter_by(username=adminname).first().group
    group_member = User.query.filter_by(group=group).all()
    # usernames = [member.username for member in group_member]
    return render_template('group.html', group_member=group_member)


@main.route('/config/slider/<int:group_id>', methods=["POST"])
def slider_config(group_id):
    group = Group.query.get(int(group_id))
    ymin = float(request.values['ymin'])
    ymax = float(request.values['ymax'])
    group.ymin = ymin
    group.ymax = ymax
    db.session.add(group)
    db.session.commit()
    return redirect('/')


@main.route('/config/predict/<int:group_id>', methods=["POST"])
def predict_config(group_id):
    group = Group.query.get(int(group_id))
    predict = int(request.values['predict'])
    group.N = predict
    db.session.add(group)
    db.session.commit()
    return redirect('/')
