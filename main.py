from flask import Flask, render_template, redirect, flash
from flask_bootstrap import Bootstrap
from google.appengine.ext import ndb
from flask.ext.wtf import Form
from wtforms import StringField, SubmitField, IntegerField
from wtforms.validators import DataRequired
import time


class NewForm(Form):
    text = StringField('Text', validators=[DataRequired()])
    position = IntegerField('Position')
    submit = SubmitField('Submit')

class HaramPosition(ndb.Model):
    text = ndb.TextProperty()
    position = ndb.IntegerProperty()

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
        HaramPosition(text=text, position=position).put()

    @classmethod
    def upvote(cls, haram_id):
        haram_position = HaramPosition.get_by_id(haram_id)
        if haram_position.position == 1:
            flash("Already on top")
            return
        harams = HaramPosition.query(HaramPosition.position
                                     < haram_position.position).order(HaramPosition.position).fetch(20000)
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
                                     > haram_position.position).order(HaramPosition.position).fetch(20000)
        for haram in harams:
            haram.position -= 1
            haram.put()
        haram_position.position += 1
        haram_position.put()


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


@app.route('/delete/<haram_id>')
def delete(haram_id):
    return render_template('delete.html', haram_id=haram_id)


@app.route('/deletereally/<haram_id>')
def deletereally(haram_id):
    haram_position = HaramPosition.get_by_id(int(haram_id))
    haram_position.key.delete()
    time.sleep(1)
    flash("Deleted")
    return redirect('/')


@app.route('/robots.txt')
def robots():
    return render_template('robots.txt')

if __name__ == '__main__':
    app.run()
