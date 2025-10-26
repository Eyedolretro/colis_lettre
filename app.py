import os
from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail, Message

app = Flask(__name__)
app.secret_key = 'ton_secret_key'

# Base SQLite
basedir = os.path.abspath(os.path.dirname(__file__))
db_path = os.path.join(basedir, 'data', 'users.db')
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Mail
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'hiflo83@gmail.com'
app.config['MAIL_PASSWORD'] = 'wfwl heto evin skab'
mail = Mail(app)

# Modèles
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)

class Livraison(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), nullable=False)
    produit = db.Column(db.String(120), nullable=False)
    date_confirmation = db.Column(db.DateTime, default=db.func.current_timestamp())
    confirme = db.Column(db.Boolean, default=False)

# Création tables
with app.app_context():
    db.create_all()

# Produits
produits = [
    {"nom": "Tasse blanche", "prix": 12},
    {"nom": "Tasse personnalisée", "prix": 18},
    {"nom": "Mug isotherme", "prix": 25}
]

# Routes
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
            session['user_email'] = email
            flash("Vous êtes déjà inscrit, connexion réussie !")
            return redirect(url_for('index'))

        new_user = User(email=email, password=password)
        db.session.add(new_user)
        db.session.commit()

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

    # Lien ngrok avec email + produit
    lien_autorisation = f"https://sherry-unfurbished-terisa.ngrok-free.dev/autoriser_livraison?produit={nom_produit}&email={email}"

    # Envoi mail avec bouton
    msg = Message("Autorisez la livraison en boîte aux lettres",
                  sender=app.config['MAIL_USERNAME'],
                  recipients=[email])
    msg.html = f"""
    <p>Bonjour {email},</p>
    <p>Votre achat de <b>{nom_produit}</b> est confirmé 🎉</p>
    <p>Pour autoriser la livraison de votre colis en boîte aux lettres demain,
    cliquez simplement sur le bouton ci-dessous :</p>
    <p>
      <a href="{lien_autorisation}" style="
          background-color:#4CAF50;
          color:white;
          padding:12px 24px;
          text-decoration:none;
          border-radius:6px;
          display:inline-block;
          font-weight:bold;
      ">
        Autoriser la livraison
      </a>
    </p>
    <p>Merci de votre confiance,<br>L’équipe Projet-Colis</p>
    """
    mail.send(msg)

    flash(f"Achat confirmé pour {nom_produit} ! Un email d’autorisation de livraison a été envoyé.")
    return redirect(url_for('index'))


@app.route('/autoriser_livraison')
def autoriser_livraison():
    produit = request.args.get('produit', 'Produit inconnu')
    email = request.args.get('email')

    if email:
        # Crée la livraison confirmée
        livraison = Livraison(email=email, produit=produit, confirme=True)
        db.session.add(livraison)
        db.session.commit()

        # Mail de confirmation
        msg = Message("Livraison confirmée ✅",
                      sender=app.config['MAIL_USERNAME'],
                      recipients=[email])
        msg.body = f"""
Bonjour {email},

Votre autorisation a bien été enregistrée ✅
Votre colis de {produit} sera déposé dans votre boîte aux lettres demain.

Merci pour votre confiance,
L’équipe Projet-Colis
"""
        mail.send(msg)

        flash("✅ Livraison autorisée ! Un e-mail de confirmation vous a été envoyé.")
    else:
        flash("Erreur : impossible de récupérer votre email pour confirmer la livraison.")

    return render_template('autoriser_livraison.html')


@app.route('/appli_livreur')
def appli_livreur():
    livraisons = Livraison.query.filter_by(confirme=True).all()
    return render_template('appli_livreur.html', livraisons=livraisons)

@app.route('/logout')
def logout():
    session.pop('user_email', None)
    flash('Vous avez été déconnecté.')
    return redirect(url_for('index'))

# Désactive l'avertissement ngrok
@app.after_request
def skip_ngrok_warning(response):
    response.headers['ngrok-skip-browser-warning'] = 'true'
    return response

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
