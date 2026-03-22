from sqlalchemy.orm import Session


class Repository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, model, entity_id: int):
        return self.db.get(model, entity_id)

    def save(self, entity):
        self.db.add(entity)
        self.db.flush()
        return entity

    def delete(self, entity):
        self.db.delete(entity)
        self.db.flush()

    def exists(self, model, entity_id: int) -> bool:
        return self.get_by_id(model, entity_id) is not None
