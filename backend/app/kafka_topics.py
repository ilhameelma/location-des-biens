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

# Liste exhaustive, utile pour créer les topics à l'avance (voir scripts/create_topics.py)
ALL_TOPICS = [
    BIEN_CREE,
    RESERVATION_CREEE,
    RESERVATION_STATUT_MAJ,
    CONTRAT_SIGNE,
    PAIEMENT_EFFECTUE,
]
