from CTFd.models import Challenges, db, Solves, Fails, Flags, Hints, Tags, ChallengeFiles
from CTFd.utils.uploads import delete_file
from CTFd.plugins.challenges import CHALLENGE_CLASSES, BaseChallenge
from flask import Blueprint
import ast


class KubernetesConfig(db.Model):
    """
    Kubernetes Config Model. This model stores the config for the Kubernetes API.
    """
    __tablename__ = "k8config"
    __table_args__ = (db.UniqueConstraint("id"), {})

    id = db.Column(db.Integer, primary_key=True)
    image = db.Column(db.String(64), index=True)
    secret = db.Column(db.Text, index=True)

    def __init__(self, **kwargs):
        super(KubernetesConfig, self).__init__(**kwargs)


class KubernetesChallengeTracker(db.Model):
    """
    Kubernetes Deployment Tracker. This model stores the users/teams active resources.
    """
    __tablename__ = "k8chaltrack"
    __table_args__ = (db.UniqueConstraint("id"), {})

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, index=True)
    timestamp_start = db.Column(db.Text, index=True)
    timestamp_stop = db.Column(db.Text, index=True, nullable=True)
    revert_time = db.Column(db.Integer, index=True)
    challenge_id = db.Column(db.Integer, db.ForeignKey("challenges.id"))

    def __init__(self, **kwargs):
        super(KubernetesChallengeTracker, self).__init__(**kwargs)


class KubernetesChallenge(Challenges):
    """
        Deployment object for in database.
        """
    __mapper_args__ = {'polymorphic_identity': 'kubedefault'}

    id = db.Column(
        db.Integer, db.ForeignKey("challenges.id", ondelete="CASCADE"), primary_key=True
    )
    compose = db.Column(db.Text)

    def __init__(self, **kwargs):
        super(KubernetesChallenge, self).__init__(**kwargs)


class KubernetesChallengeType(BaseChallenge):
    """
        Kubernetes Challenge Type. This is the type of challenge for Kubernetes related Challenges
        """
    id = "kubedefault"
    name = "kubedefault"
    templates = {
        "create": "/plugins/kubernetes/assets/create.html",
        "update": "/plugins/kubernetes/assets/update.html",
        "view": "/plugins/kubernetes/assets/view.html",
    }
    scripts = {
        "create": "/plugins/kubernetes/assets/create.js",
        "update": "/plugins/kubernetes/assets/update.js",
        "view": "/plugins/kubernetes/assets/view.js",
    }
    route = "/plugins/kubernetes/assets/"

    blueprint = Blueprint(
        "kubedefault", __name__, template_folder="templates", static_folder="assets"
    )
    challenge_model = KubernetesChallenge

    def delete(challenge):
        """
        This method is used to delete the resources used by a challenge.
        :param challenge:
        :return:
        """
        Fails.query.filter_by(challenge_id=challenge.id).delete()
        Solves.query.filter_by(challenge_id=challenge.id).delete()
        Flags.query.filter_by(challenge_id=challenge.id).delete()
        files = ChallengeFiles.query.filter_by(challenge_id=challenge.id).all()
        for f in files:
            delete_file(f.id)
        ChallengeFiles.query.filter_by(challenge_id=challenge.id).delete()
        Tags.query.filter_by(challenge_id=challenge.id).delete()
        Hints.query.filter_by(challenge_id=challenge.id).delete()
        KubernetesChallengeTracker.query.filter_by(
            challenge_id=challenge.id).delete()
        Challenges.query.filter_by(id=challenge.id).delete()
        KubernetesChallenge.query.filter_by(id=challenge.id).delete()
        db.session.commit()
