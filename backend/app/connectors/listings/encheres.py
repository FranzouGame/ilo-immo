from app.connectors.base import ListingConnector


class EncheresConnector(ListingConnector):
    name = "encheres"
    label = "Enchères judiciaires et des Domaines"
    terms_url = "À renseigner (CGU de la source)"
    # TODO: implémenter fetch()/normalize() après vérification juridique (voir ListingConnector).
