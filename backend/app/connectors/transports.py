from app.connectors import overpass
from app.connectors.osm import OsmConnector


class TransportsConnector(OsmConnector):
    name = "transports"
    label = "Transports - gares et arrêts (OpenStreetMap)"
    license = "ODbL 1.0 (© contributeurs OpenStreetMap)"
    terms_url = "https://www.openstreetmap.org/copyright"
    update_frequency = "mensuelle"
    kinds = overpass.TRANSPORT_KINDS
    # Alternative officielle : référentiel des arrêts IDFM (data.iledefrance-mobilites.fr, ODbL/LO) -
    # même schéma `poi` (kind=station|stop) ; à brancher ici si l'on veut des lignes/ modes précis.
