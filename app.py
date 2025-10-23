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
    code_livraison = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))

    # Génération du lien unique avec le code
    lien_autorisation = url_for('autoriser_livraison', code=code_livraison, _external=True)

    msg = Message("Autorisez la livraison en boîte aux lettres",
                  sender=app.config['MAIL_USERNAME'],
                  recipients=[email])
    msg.html = f"""
    <p>Bonjour {email},</p>
    <p>Votre achat de <b>{nom_produit}</b> est confirmé 🎉</p>
    <p>Voici votre code unique&nbsp;: <b>{code_livraison}</b></p>
    <p>Pour autoriser la livraison en boîte aux lettres demain, cliquez simplement sur le bouton ci-dessous&nbsp;:</p>
    <p>
      <a href="{lien_autorisation}" style="
          background-color:#4CAF50;
          color:white;
          padding:12px 24px;
          text-decoration:none;
          border-radius:6px;
          display:inline-block;
      ">
        Autoriser la livraison
      </a>
    </p>
    <p>Merci de votre confiance,<br>L’équipe Projet-Colis</p>
    """

    mail.send(msg)
    session['code_livraison'] = code_livraison
    session['message'] = f"Achat confirmé pour {nom_produit} ! Un email contenant votre lien d’autorisation a été envoyé."
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
    code_attendu = session.get('code_livraison')
    code_recu = request.args.get('code') or request.form.get('code')

    if not code_attendu:
        flash("Aucun code de livraison trouvé. Veuillez effectuer un achat d'abord.")
        return redirect(url_for('index'))

    if code_recu and code_recu == code_attendu:
        session['livraison_autorisee'] = True
        flash("✅ Ok pour la livraison en boîte aux lettres demain. Merci pour votre validation !")
        return redirect(url_for('index'))

    if request.method == 'POST':
        flash("❌ Code incorrect. Vérifiez le code reçu par email.")
        return redirect(url_for('autoriser_livraison'))

    return render_template('autoriser_livraison.html')




if __name__ == '__main__':
    app.run(debug=True)
