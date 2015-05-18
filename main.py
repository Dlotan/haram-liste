from flask import Flask, render_template, redirect
from flask_bootstrap import Bootstrap
from google.appengine.ext import ndb
from flask.ext.wtf import Form
from wtforms import StringField, SubmitField, IntegerField
from wtforms.validators import DataRequired
import time


class NewForm(Form):
    text = StringField('Text', validators=[DataRequired()])
    priority = IntegerField('Priority')
    submit = SubmitField('Submit')

class HaramPosition(ndb.Model):
    text = ndb.TextProperty()
    priority = ndb.IntegerProperty()

app = Flask(__name__)
app.secret_key = 'asd123'
Bootstrap(app)

@app.route('/')
def index():
    harams = HaramPosition.query().order(-HaramPosition.priority).fetch(1000)
    return render_template('index.html', harams=harams)

@app.route('/new', methods=('GET', 'POST'))
def new():
    form = NewForm()
    if form.validate_on_submit():
        text = form.text.data
        priority = form.priority.data
        haramposition = HaramPosition(text=text, priority=priority)
        haramposition.put()
        time.sleep(1)
        return redirect('/')
    return render_template('new.html', form=form)


@app.route('/upvote/<haram_id>')
def upvote(haram_id):
    haram_position = HaramPosition.get_by_id(int(haram_id))
    haram_position.priority += 1
    haram_position.put()
    time.sleep(1)
    return redirect('/')


@app.route('/downvote/<haram_id>')
def downvote(haram_id):
    haram_position = HaramPosition.get_by_id(int(haram_id))
    haram_position.priority -= 1
    haram_position.put()
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
    return redirect('/')


@app.route('/robots.txt')
def robots():
    return render_template('robots.txt')

if __name__ == '__main__':
    app.run()
