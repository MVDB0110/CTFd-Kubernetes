import CTFd
import flask

class ContainerChallengeLog(CTFd.models.db.Model):
    __tablename__ = "container_log"
    __table_args__ = (CTFd.models.db.UniqueConstraint("id"), {})

    id = CTFd.models.db.Column(CTFd.models.db.Integer, primary_key=True)
    challenge_id = CTFd.models.db.Column(CTFd.models.db.Integer, index=True)
    user_id = CTFd.models.db.Column(CTFd.models.db.Integer, index=True)
    start_epoch = CTFd.models.db.Column(CTFd.models.db.Integer, index=True)

    def __init__(self, **kwargs):
        super(ContainerChallengeLog, self).__init__(**kwargs)

class ContainerChallengeConfiguration(CTFd.models.db.Model):
    __tablename__ = "container_configuration"
    __table_args__ = (CTFd.models.db.UniqueConstraint("id"), {})

    id = CTFd.models.db.Column(CTFd.models.db.Integer, primary_key=True)
    username = CTFd.models.db.Column(CTFd.models.db.Text, index=True)
    password = CTFd.models.db.Column(CTFd.models.db.Text, index=True)
    url = CTFd.models.db.Column(CTFd.models.db.Text, index=True)
    image = CTFd.models.db.Column(CTFd.models.db.Text, index=True)

    def __init__(self, **kwargs):
        super(ContainerChallengeConfiguration, self).__init__(**kwargs)

class ContainerChallenge(CTFd.models.Challenges):
    __mapper_args__ = {"polymorphic_identity": "container"}

    id = CTFd.models.db.Column(CTFd.models.db.Integer, CTFd.models.db.ForeignKey("challenges.id", ondelete="CASCADE"), primary_key=True)
    compose = CTFd.models.db.Column(CTFd.models.db.Text)
    challenge_type = CTFd.models.db.Column(CTFd.models.db.Text)

    def __init__(self, **kwargs):
        super(ContainerChallenge, self).__init__(**kwargs)

class ContainerChallengeType(CTFd.plugins.challenges.BaseChallenge):
    id = "container"
    name = "container"
    templates = {
        "create": "/plugins/container_challenges/assets/create.html",
        "update": "/plugins/container_challenges/assets/update.html",
        "view": "/plugins/container_challenges/assets/view.html",
    }
    scripts = {
        "create": "/plugins/container_challenges/assets/create.js",
        "update": "/plugins/container_challenges/assets/update.js",
        "view": "/plugins/container_challenges/assets/view.js",
    }
    route = "/plugins/container_challenges/assets/"
    blueprint = flask.Blueprint("container", __name__, template_folder="templates", static_folder="assets")
    challenge_model = ContainerChallenge

    def delete(challenge):
        CTFd.models.Fails.query.filter_by(challenge_id=challenge.id).delete()
        CTFd.models.Solves.query.filter_by(challenge_id=challenge.id).delete()
        CTFd.models.Flags.query.filter_by(challenge_id=challenge.id).delete()
        files = CTFd.models.ChallengeFiles.query.filter_by(challenge_id=challenge.id).all()
        for f in files:
            CTFd.utils.uploads.delete_file(f.id)
        CTFd.models.ChallengeFiles.query.filter_by(challenge_id=challenge.id).delete()
        CTFd.models.Tags.query.filter_by(challenge_id=challenge.id).delete()
        CTFd.models.Hints.query.filter_by(challenge_id=challenge.id).delete()
        CTFd.models.Challenges.query.filter_by(id=challenge.id).delete()
        ContainerChallenge.query.filter_by(id=challenge.id).delete()
        CTFd.models.db.session.commit()
