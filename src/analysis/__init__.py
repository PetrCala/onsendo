import matplotlib.pyplot as plt
from src.db.conn import SessionLocal
from src.db.models import OnsenVisit


def plot_visit_lengths():
    with SessionLocal() as db:
        visits = db.query(OnsenVisit).all()
        lengths = [v.stay_length_minutes for v in visits]

    # Simple histogram of visit lengths:
    plt.hist(lengths)
    plt.title("Distribution of Onsen Visit Lengths")
    plt.xlabel("Length (minutes)")
    plt.ylabel("Frequency")
    plt.show()
