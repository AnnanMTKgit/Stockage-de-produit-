import streamlit as st
import pandas as pd
import sqlalchemy
from sqlalchemy import create_engine, Column, Integer, String, Numeric
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
import pyodbc # Important de l'importer

# --- CONFIGURATION DE LA BASE DE DONNÉES (SQLAlchemy pour SQL Server sur macOS) ---

# 1. Informations de connexion
# Le serveur est 'localhost' car Docker expose le port sur le localhost de votre Mac.
server = 'localhost' # Spécifier le port est une bonne pratique
database = 'MagasinDB'
username = 'sa' # L'utilisateur par défaut de SQL Server
password = 'Annan123@' # LE MOT DE PASSE DÉFINI DANS DOCKER !

# 2. Définir l'URL de la base de données pour SQL Server avec Authentification SQL
# Le nom du driver doit être entouré d'accolades {}.
# On utilise UID (User ID) et PWD (Password).
DATABASE_URL = f"mssql+pyodbc://{username}:{password}@{server}:1433/{database}?driver=ODBC+Driver+17+for+SQL+Server"

# 3. Créer le "moteur" de la base de données
engine = create_engine(DATABASE_URL)

# 4. Créer une session pour interagir avec la base de données
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
session = SessionLocal()

# 5. Déclarer une "Base" pour nos modèles de table
Base = declarative_base()

# --- DÉFINITION DU MODÈLE DE TABLE 'PRODUIT' ---
class Produit(Base):
    __tablename__ = "produits"
    # Le modèle reste identique
    id = Column(Integer, primary_key=True)
    nom = Column(String(255), unique=True, nullable=False)
    description = Column(String)
    prix = Column(Numeric(10, 2), nullable=False)
    quantite = Column(Integer, nullable=False)
# --- FONCTIONS CRUD (Create, Read, Update, Delete) ---

def get_all_products():
    """Récupère tous les produits de la base de données."""
    return session.query(Produit).all()

def add_product(nom, description, prix, quantite):
    """Ajoute un nouveau produit dans la base de données."""
    nouveau_produit = Produit(nom=nom, description=description, prix=prix, quantite=quantite)
    session.add(nouveau_produit)
    session.commit()
    st.success(f"Produit '{nom}' ajouté avec succès !")
    st.rerun() # Pour rafraîchir la page et voir le nouveau produit

def update_product(id_produit, nom, description, prix, quantite):
    """Met à jour un produit existant."""
    produit_a_maj = session.query(Produit).filter(Produit.id == id_produit).first()
    if produit_a_maj:
        produit_a_maj.nom = nom
        produit_a_maj.description = description
        produit_a_maj.prix = prix
        produit_a_maj.quantite = quantite
        session.commit()
        st.success("Produit mis à jour avec succès !")
        st.rerun()
    else:
        st.error("Produit non trouvé.")

def delete_product(id_produit):
    """Supprime un produit de la base de données."""
    produit_a_suppr = session.query(Produit).filter(Produit.id == id_produit).first()
    if produit_a_suppr:
        session.delete(produit_a_suppr)
        session.commit()
        st.success("Produit supprimé avec succès !")
        st.rerun()
    else:
        st.error("Produit non trouvé.")


# --- INTERFACE UTILISATEUR (Streamlit) ---

st.set_page_config(page_title="Gestion de Stock", layout="wide")
st.title("📦 Application de Gestion de Stock")

# Menu dans la barre latérale
menu = ["Afficher les produits", "Ajouter un produit", "Mettre à jour un produit", "Supprimer un produit"]
choix = st.sidebar.selectbox("Navigation", menu)

# Récupérer la liste des produits pour les menus déroulants
produits = get_all_products()
noms_produits = {p.nom: p for p in produits}

# --- Section : Afficher les produits ---
if choix == "Afficher les produits":
    st.header("Liste de tous les produits en stock")
    if produits:
        # Convertir la liste d'objets Produit en DataFrame Pandas pour un bel affichage
        df = pd.DataFrame(
            [(p.id, p.nom, p.description, f"{p.prix:.2f} €", p.quantite) for p in produits],
            columns=["ID", "Nom", "Description", "Prix", "Quantité"]
        )
        st.dataframe(df, use_container_width=True)
    else:
        st.info("Aucun produit en stock pour le moment.")

# --- Section : Ajouter un produit ---
elif choix == "Ajouter un produit":
    st.header("Ajouter un nouveau produit")
    with st.form("ajout_produit_form"):
        nom = st.text_input("Nom du produit")
        description = st.text_area("Description")
        prix = st.number_input("Prix (€)", min_value=0.0, format="%.2f")
        quantite = st.number_input("Quantité", min_value=0, step=1)
        
        submitted = st.form_submit_button("Ajouter")
        if submitted:
            if nom and prix > 0:
                add_product(nom, description, prix, quantite)
            else:
                st.warning("Veuillez remplir au moins le nom et un prix valide.")

# --- Section : Mettre à jour un produit ---
elif choix == "Mettre à jour un produit":
    st.header("Mettre à jour un produit existant")
    if not produits:
        st.warning("Aucun produit à mettre à jour. Veuillez d'abord en ajouter.")
    else:
        produit_selectionne_nom = st.selectbox("Choisissez un produit à modifier", options=noms_produits.keys())
        produit_selectionne = noms_produits[produit_selectionne_nom]

        with st.form("maj_produit_form"):
            st.write(f"Modification du produit ID: {produit_selectionne.id}")
            
            # Pré-remplir les champs avec les valeurs actuelles
            nom_maj = st.text_input("Nom du produit", value=produit_selectionne.nom)
            description_maj = st.text_area("Description", value=produit_selectionne.description)
            prix_maj = st.number_input("Prix (€)", min_value=0.0, value=float(produit_selectionne.prix), format="%.2f")
            quantite_maj = st.number_input("Quantité", min_value=0, value=int(produit_selectionne.quantite), step=1)
            
            submitted = st.form_submit_button("Mettre à jour")
            if submitted:
                update_product(produit_selectionne.id, nom_maj, description_maj, prix_maj, quantite_maj)

# --- Section : Supprimer un produit ---
elif choix == "Supprimer un produit":
    st.header("Supprimer un produit")
    if not produits:
        st.warning("Aucun produit à supprimer.")
    else:
        produit_selectionne_nom = st.selectbox("Choisissez un produit à supprimer", options=noms_produits.keys())
        produit_selectionne = noms_produits[produit_selectionne_nom]

        st.warning(f"**Attention !** Vous êtes sur le point de supprimer le produit : **{produit_selectionne.nom}**.")
        
        if st.button("Confirmer la suppression", type="primary"):
            delete_product(produit_selectionne.id)
