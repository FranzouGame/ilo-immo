from app.connectors.base import ListingConnector


class NotairesConnector(ListingConnector):
    name = "notaires"
    label = "Annonces notariales"
    terms_url = "À renseigner (CGU de la source)"
    # TODO: implémenter fetch()/normalize() après vérification juridique (voir ListingConnector).
