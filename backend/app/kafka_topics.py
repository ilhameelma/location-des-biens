"""
Étape 10 — Collecte des données (Kafka)

Noms des topics métier publiés par le back-end. Un topic par type
d'événement, repris ensuite par Spark (étape 11) pour alimenter le data
lake (étape 12) puis le data warehouse (étape 14).
"""

BIEN_CREE = "smartrent.bien.cree"
RESERVATION_CREEE = "smartrent.reservation.creee"
RESERVATION_STATUT_MAJ = "smartrent.reservation.statut_maj"
CONTRAT_SIGNE = "smartrent.contrat.signe"
PAIEMENT_EFFECTUE = "smartrent.paiement.effectue"
# Complément — ces 3 événements n'étaient pas captés jusqu'ici : le pipeline
# analytique (data lake -> data warehouse -> Power BI) ne "voyait" donc ni
# les avis, ni les réclamations, ni les inscriptions. Ajoutés pour permettre
# une dimension utilisateur (dw.dim_utilisateur) et deux nouvelles tables de
# faits (dw.fait_avis, dw.fait_reclamation) — voir load_to_warehouse.py.
AVIS_CREE = "smartrent.avis.cree"
RECLAMATION_CREEE = "smartrent.reclamation.creee"
UTILISATEUR_INSCRIT = "smartrent.utilisateur.inscrit"

# Liste exhaustive, utile pour créer les topics à l'avance (voir scripts/create_topics.py)
ALL_TOPICS = [
    BIEN_CREE,
    RESERVATION_CREEE,
    RESERVATION_STATUT_MAJ,
    CONTRAT_SIGNE,
    PAIEMENT_EFFECTUE,
    AVIS_CREE,
    RECLAMATION_CREEE,
    UTILISATEUR_INSCRIT,
]
