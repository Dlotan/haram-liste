from flask import Flask, render_template, redirect, flash
from flask_bootstrap import Bootstrap
from google.appengine.ext import ndb
from google.appengine.api import mail
from flask.ext.wtf import Form
from wtforms import StringField, SubmitField, IntegerField
from wtforms.validators import DataRequired
import time


class NewForm(Form):
    text = StringField('Text', validators=[DataRequired()])
    position = IntegerField('Position')
    submit = SubmitField('Submit')


class EditForm(Form):
    text = StringField('Text', validators=[DataRequired()])
    position = IntegerField('Position')
    submit = SubmitField('Submit')


class HaramPosition(ndb.Model):
    text = ndb.TextProperty()
    position = ndb.IntegerProperty()
    created = ndb.DateTimeProperty(auto_now_add=True)

    def is_newest(self):
        newest_list = HaramPosition.query().order(-HaramPosition.created).fetch(1)
        for newest in newest_list:
            if newest.position == self.position:
                return True
        return False

    @classmethod
    def get_highest_position(cls):
        harams = HaramPosition.query().order(-HaramPosition.position).fetch(1)
        for haram in harams:
            return haram.position

    @classmethod
    def new(cls, text, position):
        harams = HaramPosition.query(HaramPosition.position >= position).order(HaramPosition.position).fetch(20000)
        has_higher = False
        for haram in harams:
            has_higher = True
            haram.position += 1
            haram.put()
        if not has_higher:
            highest_position = HaramPosition.get_highest_position()
            if highest_position:
                position = highest_position + 1
            if not highest_position:
                position = 1
        return HaramPosition(text=text, position=position).put()

    @classmethod
    def upvote(cls, haram_id):
        haram_position = HaramPosition.get_by_id(haram_id)
        if haram_position.position == 1:
            flash("Already on top")
            return
        harams = HaramPosition.query(HaramPosition.position
                                     < haram_position.position).order(-HaramPosition.position).fetch(1)
        for haram in harams:
            haram.position += 1
            haram.put()
        haram_position.position -= 1
        haram_position.put()

    @classmethod
    def downvote(cls, haram_id):
        haram_position = HaramPosition.get_by_id(haram_id)
        if haram_position.position == HaramPosition.get_highest_position():
            flash("Already on bottom")
            return
        harams = HaramPosition.query(HaramPosition.position
                                     > haram_position.position).order(HaramPosition.position).fetch(1)
        for haram in harams:
            haram.position -= 1
            haram.put()
        haram_position.position += 1
        haram_position.put()

    @classmethod
    def delete(cls, haram_id):
        haram_position = HaramPosition.get_by_id(haram_id)
        harams = HaramPosition.query(HaramPosition.position
                                     > haram_position.position).order(HaramPosition.position).fetch(20000)
        for haram in harams:
            haram.position -= 1
            haram.put()
        haram_position.key.delete()

    @classmethod
    def edit(cls, haram_id, text, position):
        HaramPosition.delete(haram_id)
        time.sleep(0.5)
        return HaramPosition.new(text=text, position=position)


app = Flask(__name__)
app.secret_key = 'asd123'
Bootstrap(app)


@app.route('/')
def index():
    harams = HaramPosition.query().order(HaramPosition.position).fetch(20000)
    return render_template('index.html', harams=harams)


@app.route('/new', methods=('GET', 'POST'))
def new():
    form = NewForm()
    if form.validate_on_submit():
        text = form.text.data
        position = form.position.data
        HaramPosition.new(text, position)
        mail.send_mail(
            sender='florian.groetzner@gmail.com',
            to='florian.groetzner@gmail.com',
            subject='New Haram: ' + text,
            body='There is a new Haram:\n\n ' + text
        )
        time.sleep(1)
        flash("Created")

        return redirect('/')
    return render_template('new.html', form=form)


@app.route('/upvote/<haram_id>')
def upvote(haram_id):
    HaramPosition.upvote(int(haram_id))
    time.sleep(1)
    return redirect('/')


@app.route('/downvote/<haram_id>')
def downvote(haram_id):
    HaramPosition.downvote(int(haram_id))
    time.sleep(1)
    return redirect('/')


@app.route('/edit/<haram_id>', methods=('GET', 'POST'))
def edit(haram_id):
    haram_position = HaramPosition.get_by_id(int(haram_id))
    edit_form = EditForm(text=haram_position.text, position=haram_position.position)
    if edit_form.validate_on_submit():
        HaramPosition.edit(int(haram_id), edit_form.text.data, edit_form.position.data)
        time.sleep(1)
        flash('Updated')
        return redirect('/')
    return render_template('edit.html', edit_form=edit_form, haram_id=haram_id)


@app.route('/delete/<haram_id>')
def delete(haram_id):
    haram_position = HaramPosition.get_by_id(int(haram_id))
    mail.send_mail(
        sender='florian.groetzner@gmail.com',
        to='florian.groetzner@gmail.com',
        subject='Deleted Haram: ' + haram_position.text,
        body='There is a deleted Haram:\n\n ' + haram_position.text
    )
    HaramPosition.delete(int(haram_id))
    time.sleep(1)
    flash("Deleted")
    return redirect('/')


@app.route('/robots.txt')
def robots():
    return render_template('robots.txt')


if __name__ == '__main__':
    app.run()
