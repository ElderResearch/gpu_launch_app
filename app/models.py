from launchapp import db

class ActivityLog(db.Model):
    id = db.Column(db.String(64), primary_key=True)
    username = db.Column(db.String(32))
    image_type = db.Column(db.String(8))
    num_gpus = db.Column(db.Integer)
    start_time = db.Column(db.DateTime, default=datetime.utcnow)
    stop_time = db.Column(db.DateTime, nullable=True)

    def __repr__(self):
        return "<ActivityLog {}".format(self.id)

    def stop(self):
        self.stop_time = datetime.utcnow()
