from flask import Flask, render_template, redirect, url_for, flash
from flask_wtf.file import FileField, FileAllowed, FileRequired
from flask_wtf import FlaskForm
from wtforms import SubmitField, StringField
from wtforms.validators import DataRequired
from werkzeug.utils import secure_filename
from sklearn.cluster import KMeans
from PIL import Image
from colormap import rgb2hex
import os
import cv2
import glob


app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY')


class ImageUpload(FlaskForm):
    count = StringField('The number of colors on the palette', validators=[DataRequired()])
    image = FileField('PNG or JPG file', validators=[FileAllowed(['png', 'jpg'], 'Only png and jpg!'), FileRequired('File is empty!')])
    submit = SubmitField('Upload')


class DominantColors:
    CLUSTERS = None
    IMAGE = None
    COLORS = None
    LABELS = None

    def __init__(self, image, clusters=3):
        self.CLUSTERS = clusters
        self.IMAGE = image

    def dominantColors(self):
        img = cv2.imread(self.IMAGE)
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        img = img.reshape((img.shape[0] * img.shape[1], 3))
        self.IMAGE = img
        kmeans = KMeans(n_clusters=self.CLUSTERS)
        kmeans.fit(img)
        self.COLORS = kmeans.cluster_centers_
        self.LABELS = kmeans.labels_
        return self.COLORS.astype(int)


def scale_image(input_image, output_image, width=None, height=None):
    original_image = Image.open(input_image)
    w, h = original_image.size
    if width and height:
        max_size = (width, height)
    elif width:
        max_size = (width, h)
    elif height:
        max_size = (w, height)
    else:
        raise RuntimeError('Width or height required!')
    original_image.thumbnail(max_size, Image.ANTIALIAS)
    original_image.save('static/images/' + output_image)


@app.route('/', methods=['GET', 'POST'])
def home():
    files = glob.glob('static/images/'+'\\*')
    for f in files:
        os.remove(f)
    form = ImageUpload()
    if form.validate_on_submit():
        try:
            count = int(form.count.data)
        except ValueError:
            flash('Enter a number in the field "The number of colors on the palette"')
            return redirect(url_for('home'))
        filename = secure_filename(form.image.data.filename)
        form.image.data.save('static/images/' + filename)
        if os.path.isfile('static/images/' + filename):
            return redirect(url_for('palette', path=filename, count=count))
    return render_template('index.html', form=form)


@app.route('/<path>/<int:count>')
def palette(path, count):
    extension = path.split('.')[-1]
    scale_image('static/images/' + path, f'photo.{extension}', 700)
    dc = DominantColors(f'static/images/photo.{extension}', count)
    colors = dc.dominantColors()
    rgbs = []
    hexs = []
    for i in range(len(colors)):
        rgb = (colors[i][0], colors[i][1], colors[i][2])
        hex = rgb2hex(colors[i][0], colors[i][1], colors[i][2])
        rgbs.append(rgb)
        hexs.append(hex)
    length = len(hexs)
    return render_template('palette.html', rgbs=rgbs, hexs=hexs, length=length, path=f'photo.{extension}')


if __name__ == '__main__':
    app.run(debug=True)
