from app.connectors.base import ListingConnector


class Appels_projetsConnector(ListingConnector):
    name = "appels_projets"
    label = "Appels à projets des collectivités"
    terms_url = "À renseigner (CGU de la source)"
    # TODO: implémenter fetch()/normalize() après vérification juridique (voir ListingConnector).
