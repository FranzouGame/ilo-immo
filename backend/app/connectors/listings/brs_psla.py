from app.connectors.base import ListingConnector


class Brs_pslaConnector(ListingConnector):
    name = "brs_psla"
    label = "Offres BRS/PSLA"
    terms_url = "À renseigner (CGU de la source)"
    # TODO: implémenter fetch()/normalize() après vérification juridique (voir ListingConnector).
