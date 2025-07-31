import pyodbc
from sqlalchemy import create_engine, text

# Configuration de connexion
server = 'localhost'
username = 'sa'
password = 'Annan123@'

# Connexion au serveur SQL Server (sans spécifier de base de données)
try:
    # URL de connexion pour se connecter au serveur (pas à une base spécifique)
    server_url = f"mssql+pyodbc://{username}:{password}@{server}:1433/master?driver=ODBC+Driver+17+for+SQL+Server"
    engine = create_engine(server_url)
    
    with engine.connect().execution_options(isolation_level="AUTOCOMMIT") as conn:
        # Vérifier si la base de données existe
        result = conn.execute(text("SELECT name FROM sys.databases WHERE name = 'MagasinDB'"))
        db_exists = result.fetchone()
        
        if not db_exists:
            print("Création de la base de données MagasinDB...")
            conn.execute(text("CREATE DATABASE MagasinDB"))
            print("Base de données MagasinDB créée avec succès!")
        else:
            print("La base de données MagasinDB existe déjà.")
    
    # Maintenant se connecter à la base MagasinDB pour créer la table
    db_url = f"mssql+pyodbc://{username}:{password}@{server}:1433/MagasinDB?driver=ODBC+Driver+17+for+SQL+Server"
    db_engine = create_engine(db_url)
    
    with db_engine.connect() as conn:
        with conn.begin():
            # Vérifier si la table produits existe
            result = conn.execute(text("SELECT name FROM sys.tables WHERE name = 'produits'"))
            table_exists = result.fetchone()
            
            if not table_exists:
                print("Création de la table produits...")
                create_table_sql = """
                CREATE TABLE produits (
                    id INT IDENTITY(1,1) PRIMARY KEY,
                    nom NVARCHAR(255) UNIQUE NOT NULL,
                    description NVARCHAR(MAX),
                    prix DECIMAL(10,2) NOT NULL,
                    quantite INT NOT NULL
                )
                """
                conn.execute(text(create_table_sql))
                print("Table produits créée avec succès!")
            else:
                print("La table produits existe déjà.")

            # Vérifier si la table achats existe
            result = conn.execute(text("SELECT name FROM sys.tables WHERE name = 'achats'"))
            table_exists = result.fetchone()

            if not table_exists:
                print("Création de la table achats...")
                create_table_sql = """
                CREATE TABLE achats (
                    id INT IDENTITY(1,1) PRIMARY KEY,
                    produit_id INT NOT NULL,
                    quantite INT NOT NULL,
                    prix_total DECIMAL(10, 2) NOT NULL,
                    date_achat DATETIME DEFAULT GETDATE(),
                    FOREIGN KEY (produit_id) REFERENCES produits(id)
                )
                """
                conn.execute(text(create_table_sql))
                print("Table achats créée avec succès!")
            else:
                print("La table achats existe déjà.")
            
    print("Configuration de la base de données terminée!")
    
except Exception as e:
    print(f"Erreur lors de la configuration de la base de données: {e}")
