import os
from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail, Message
import random
import string

app = Flask(__name__)
app.secret_key = 'ton_secret_key'

# Chemin vers la base SQLite
basedir = os.path.abspath(os.path.dirname(__file__))
db_path = os.path.join(basedir, 'data', 'users.db')
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Configuration pour l'envoi de mails
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'hiflo83@gmail.com'  # ton Gmail
app.config['MAIL_PASSWORD'] = 'wfwl heto evin skab'  # mot de passe d'application
mail = Mail(app)

# Modèle utilisateur
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)

with app.app_context():
    db.create_all()

# Produits
produits = [
    {"nom": "Tasse blanche", "prix": 12},
    {"nom": "Tasse personnalisée", "prix": 18},
    {"nom": "Mug isotherme", "prix": 25}
]

@app.route('/')
def index():
    email = session.get('user_email')
    message = session.pop('message', None)
    return render_template('index.html', produits=produits, email=email, message=message)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        existing_user = User.query.filter_by(email=email).first()

        if existing_user:
            # Connecte l'utilisateur déjà inscrit
            session['user_email'] = email
            flash("Vous êtes déjà inscrit, connexion réussie !")
            return redirect(url_for('index'))

        # Création d'un nouvel utilisateur
        new_user = User(email=email, password=password)
        db.session.add(new_user)
        db.session.commit()

        # Envoi mail d'inscription
        msg = Message("Inscription réussie",
                      sender=app.config['MAIL_USERNAME'],
                      recipients=[email])
        msg.body = f"Bonjour {email}, votre inscription est confirmée !"
        mail.send(msg)

        session['user_email'] = email
        flash("Inscription réussie !")
        return redirect(url_for('index'))

    return render_template('register.html')

@app.route('/achat/<nom_produit>')
def achat(nom_produit):
    if 'user_email' not in session:
        flash('Veuillez vous inscrire avant d’acheter.')
        return redirect(url_for('register'))

    email = session['user_email']

    # Génération du code de livraison (6 caractères alphanumériques)
    code_livraison = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))

    # Envoi mail de confirmation d'achat avec le code de livraison
    msg = Message("Confirmation d'achat et code de livraison",
                  sender=app.config['MAIL_USERNAME'],
                  recipients=[email])
    msg.body = f"""
    Bonjour {email},

    Votre achat de '{nom_produit}' est confirmé !

    Voici votre code de livraison : {code_livraison}

    Ce code sera à présenter au livreur lors de la réception du colis.

    Merci pour votre confiance,
    L'équipe Projet-Colis
    """
    mail.send(msg)

    # Stockage du code dans la session (temporairement)
    session['code_livraison'] = code_livraison
    session['message'] = f"Achat confirmé pour {nom_produit} ! Un code de livraison a été envoyé à votre adresse e-mail."

    return redirect(url_for('index'))

@app.route('/users')
def list_users():
    users = User.query.all()
    emails = [user.email for user in users]
    return '<br>'.join(emails)


@app.route('/logout')
def logout():
    session.pop('user_email', None)
    flash('Vous avez été déconnecté.')
    return redirect(url_for('index'))




from flask import Flask, render_template, request, redirect, url_for, flash, session
import random, string

# ... ton code existant ...

@app.route('/autoriser_livraison', methods=['GET', 'POST'])
def autoriser_livraison():
    if request.method == 'POST':
        code_saisi = request.form['code']
        code_attendu = session.get('code_livraison')

        if not code_attendu:
            flash("Aucun code de livraison trouvé. Veuillez effectuer un achat d'abord.")
            return redirect(url_for('index'))

        if code_saisi == code_attendu:
            session['livraison_autorisee'] = True
            flash("✅ Livraison autorisée : votre colis sera déposé dans votre boîte aux lettres.")
            return redirect(url_for('index'))
        else:
            flash("❌ Code incorrect. Vérifiez le code reçu par email.")
            return redirect(url_for('autoriser_livraison'))

    return render_template('autoriser_livraison.html')



if __name__ == '__main__':
    app.run(debug=True)
