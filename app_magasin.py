import streamlit as st
import pandas as pd
import sqlalchemy
from sqlalchemy import create_engine, Column, Integer, String, Numeric, ForeignKey, DateTime, func
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.ext.declarative import declarative_base
import pyodbc  # Important de l'importer
import plotly.express as px

# --- CONFIGURATION DE LA BASE DE DONNÉES ---
server = 'localhost'
database = 'MagasinDB'
username = 'sa'
password = 'Annan123@'
DATABASE_URL = f"mssql+pyodbc://{username}:{password}@{server}:1433/{database}?driver=ODBC+Driver+17+for+SQL+Server"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
session = SessionLocal()
Base = declarative_base()

# --- DÉFINITION DES MODÈLES DE TABLE ---
class Produit(Base):
    __tablename__ = "produits"
    id = Column(Integer, primary_key=True)
    nom = Column(String(255), unique=True, nullable=False)
    description = Column(String)
    prix = Column(Numeric(10, 2), nullable=False)
    quantite = Column(Integer, nullable=False)
    achats = relationship("Achat", back_populates="produit")

class Achat(Base):
    __tablename__ = "achats"
    id = Column(Integer, primary_key=True)
    produit_id = Column(Integer, ForeignKey('produits.id'), nullable=False)
    quantite = Column(Integer, nullable=False)
    prix_total = Column(Numeric(10, 2), nullable=False)
    date_achat = Column(DateTime, default=func.now())
    produit = relationship("Produit", back_populates="achats")

# --- FONCTIONS CRUD ET MÉTIER ---

def get_all_products():
    return session.query(Produit).all()

def get_all_sales():
    return session.query(Achat).order_by(Achat.date_achat.desc()).all()

def add_product(nom, description, prix, quantite):
    nouveau_produit = Produit(nom=nom, description=description, prix=prix, quantite=quantite)
    session.add(nouveau_produit)
    session.commit()
    st.success(f"Produit '{nom}' ajouté avec succès !")
    st.rerun()

def update_product(id_produit, nom, description, prix, quantite):
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
    produit_a_suppr = session.query(Produit).filter(Produit.id == id_produit).first()
    if produit_a_suppr:
        session.delete(produit_a_suppr)
        session.commit()
        st.success("Produit supprimé avec succès !")
        st.rerun()
    else:
        st.error("Produit non trouvé.")

def sell_product(produit, quantite_vendue):
    if quantite_vendue <= 0:
        st.warning("La quantité doit être supérieure à zéro.")
        return
    if produit.quantite >= quantite_vendue:
        produit.quantite -= quantite_vendue
        prix_total = quantite_vendue * produit.prix
        nouvelle_vente = Achat(produit_id=produit.id, quantite=quantite_vendue, prix_total=prix_total)
        session.add(nouvelle_vente)
        session.commit()
        st.success(f"Vente de {quantite_vendue} x '{produit.nom}' effectuée avec succès !")
        st.rerun()
    else:
        st.error(f"Stock insuffisant pour '{produit.nom}'. Il ne reste que {produit.quantite} unité(s).")

def restock_product(produit, quantite_ajoutee):
    if quantite_ajoutee <= 0:
        st.warning("La quantité doit être supérieure à zéro.")
        return
    produit.quantite += quantite_ajoutee
    session.commit()
    st.success(f"Stock de '{produit.nom}' réapprovisionné de {quantite_ajoutee} unités.")
    st.rerun()

# --- INTERFACE UTILISATEUR (Streamlit) ---

st.set_page_config(page_title="Gestion de Stock", layout="wide")
st.title("📦 Application de Gestion de Stock")

menu = ["Tableau de bord", "Afficher les produits", "Vendre un produit", "Réapprovisionner le stock", "Ajouter un produit", "Modifier un produit", "Supprimer un produit"]
choix = st.sidebar.selectbox("Navigation", menu)

produits = get_all_products()
noms_produits = {p.nom: p for p in produits}

if choix == "Tableau de bord":
    st.header("📊 Tableau de bord")
    
    total_produits = len(produits)
    valeur_stock_total = sum(p.prix * p.quantite for p in produits)
    achats = get_all_sales()
    revenu_total = sum(a.prix_total for a in achats)

    col1, col2, col3 = st.columns(3)
    col1.metric("Nombre total de produits", total_produits)
    col2.metric("Valeur totale du stock", f"{valeur_stock_total:.2f} €")
    col3.metric("Revenu total des ventes", f"{revenu_total:.2f} €")

    st.markdown("---")

    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Niveaux de stock par produit")
        if produits:
            df_stock = pd.DataFrame([(p.nom, p.quantite) for p in produits], columns=["Produit", "Quantité"])
            fig = px.bar(df_stock, x="Produit", y="Quantité", title="Quantité en stock")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Aucun produit en stock.")

    with col2:
        st.subheader("Produits les plus vendus (par quantité)")
        if achats:
            df_achats = pd.DataFrame([(a.produit.nom, a.quantite) for a in achats], columns=["Produit", "Quantité Vendue"])
            df_ventes = df_achats.groupby("Produit")["Quantité Vendue"].sum().sort_values(ascending=False).reset_index()
            fig = px.pie(df_ventes, names="Produit", values="Quantité Vendue", title="Répartition des ventes")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Aucune vente enregistrée.")

    st.subheader("Dernières ventes")
    if achats:
        df_last_sales = pd.DataFrame(
            [(a.produit.nom, a.quantite, f"{a.prix_total:.2f} €", a.date_achat.strftime('%Y-%m-%d %H:%M')) for a in achats[:10]],
            columns=["Produit", "Quantité", "Prix Total", "Date"]
        )
        st.dataframe(df_last_sales, use_container_width=True)
    else:
        st.info("Aucune vente pour le moment.")

elif choix == "Afficher les produits":
    st.header("Liste de tous les produits en stock")
    if produits:
        df = pd.DataFrame(
            [(p.id, p.nom, p.description, f"{p.prix:.2f} €", p.quantite) for p in produits],
            columns=["ID", "Nom", "Description", "Prix", "Quantité"]
        )
        st.dataframe(df, use_container_width=True)
    else:
        st.info("Aucun produit en stock pour le moment.")

elif choix == "Vendre un produit":
    st.header("Effectuer une vente")
    if not produits:
        st.warning("Aucun produit disponible à la vente.")
    else:
        produit_selectionne_nom = st.selectbox("Choisissez un produit à vendre", options=noms_produits.keys())
        produit_selectionne = noms_produits[produit_selectionne_nom]
        
        with st.form("vente_form"):
            st.write(f"Produit : **{produit_selectionne.nom}**")
            st.write(f"Prix unitaire : **{produit_selectionne.prix:.2f} €**")
            st.write(f"En stock : **{produit_selectionne.quantite}**")
            
            quantite_vente = st.number_input("Quantité à vendre", min_value=1, max_value=produit_selectionne.quantite, step=1)
            
            submitted = st.form_submit_button("Vendre")
            if submitted:
                sell_product(produit_selectionne, quantite_vente)

elif choix == "Réapprovisionner le stock":
    st.header("Réapprovisionner le stock d'un produit")
    if not produits:
        st.warning("Aucun produit à réapprovisionner.")
    else:
        produit_selectionne_nom = st.selectbox("Choisissez un produit à réapprovisionner", options=noms_produits.keys())
        produit_selectionne = noms_produits[produit_selectionne_nom]
        
        with st.form("restock_form"):
            st.write(f"Produit : **{produit_selectionne.nom}**")
            st.write(f"Quantité actuelle : **{produit_selectionne.quantite}**")
            
            quantite_ajoutee = st.number_input("Quantité à ajouter", min_value=1, step=1)
            
            submitted = st.form_submit_button("Ajouter au stock")
            if submitted:
                restock_product(produit_selectionne, quantite_ajoutee)

elif choix == "Ajouter un produit":
    st.header("Ajouter un nouveau produit")
    with st.form("ajout_produit_form"):
        nom = st.text_input("Nom du produit")
        description = st.text_area("Description")
        prix = st.number_input("Prix (€)", min_value=0.0, format="%.2f")
        quantite = st.number_input("Quantité initiale", min_value=0, step=1)
        
        submitted = st.form_submit_button("Ajouter")
        if submitted:
            if nom and prix > 0:
                add_product(nom, description, prix, quantite)
            else:
                st.warning("Veuillez remplir au moins le nom et un prix valide.")

elif choix == "Modifier un produit":
    st.header("Modifier les informations d'un produit")
    if not produits:
        st.warning("Aucun produit à modifier.")
    else:
        produit_selectionne_nom = st.selectbox("Choisissez un produit à modifier", options=noms_produits.keys())
        produit_selectionne = noms_produits[produit_selectionne_nom]

        with st.form("maj_produit_form"):
            st.write(f"Modification du produit ID: {produit_selectionne.id}")
            nom_maj = st.text_input("Nom du produit", value=produit_selectionne.nom)
            description_maj = st.text_area("Description", value=produit_selectionne.description)
            prix_maj = st.number_input("Prix (€)", min_value=0.0, value=float(produit_selectionne.prix), format="%.2f")
            quantite_maj = st.number_input("Quantité", min_value=0, value=int(produit_selectionne.quantite), step=1)
            
            submitted = st.form_submit_button("Mettre à jour les informations")
            if submitted:
                update_product(produit_selectionne.id, nom_maj, description_maj, prix_maj, quantite_maj)

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
