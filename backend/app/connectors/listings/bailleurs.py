from app.connectors.base import ListingConnector


class BailleursConnector(ListingConnector):
    name = "bailleurs"
    label = "Bailleurs sociaux (vente du parc)"
    terms_url = "À renseigner (CGU de la source)"
    # TODO: implémenter fetch()/normalize() après vérification juridique (voir ListingConnector).
