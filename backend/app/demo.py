from geoalchemy2.shape import from_shape
from shapely.geometry import Point
from sqlalchemy.orm import Session

from app.compute import recompute
from app.models import Property

DEMO = [  # biens fictifs, uniquement pour essayer l'interface
    ("Démo - T3 lumineux Évry", 2.4297, 48.6299, "Évry-Courcouronnes", 235000, 62, 3, 7, 9, "S"),
    ("Démo - T4 Palaiseau", 2.2467, 48.7130, "Palaiseau", 349000, 78, 4, 5, 6, "SW"),
    ("Démo - T2 Massy", 2.2711, 48.7309, "Massy", 215000, 41, 2, 2, 5, "E"),
    ("Démo - T3 Arpajon", 2.2459, 48.5900, "Arpajon", 198000, 60, 3, 4, 5, None),
]


def seed(session: Session) -> int:
    for title, lon, lat, commune, price, surface, rooms, floor, total, orient in DEMO:
        p = Property(source="demo", title=title, type="appartement", price=price, surface=surface, rooms=rooms,
                     floor=floor, floors_total=total, orientation=orient, commune=commune, tags=["démo"],
                     custom={}, photos=[], computed={}, geom=from_shape(Point(lon, lat), srid=4326))
        session.add(p)
        session.flush()
        recompute(session, p)
    session.commit()
    return len(DEMO)
