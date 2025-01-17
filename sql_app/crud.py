from typing import List
from sqlalchemy.orm import Session, aliased
from sqlalchemy import Uuid, String, update, func, delete

from . import models, schemas

import datetime

# Define functions for executing CRUD operations on the database

###############################################################
# projects table
###############################################################


# GET /projects
def get_projects(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Project).offset(skip).limit(limit).all()


# POST /projects
def create_project(db: Session, project: schemas.ProjectCreate):
    db_project = models.Project(
        name=project.name,
    )
    db.add(db_project)
    db.commit()
    db.refresh(db_project)
    return db_project


# GET /projects/{project_id}
def get_project_by_id(db: Session, project_id: Uuid):
    return db.query(models.Project).filter(models.Project.id == project_id).first()


def get_project_by_name(db: Session, project_name: Uuid):
    return db.query(models.Project).filter(models.Project.name == project_name).first()


# POST /projects/{project_id}
# TODO: implement a way to rename in database

# DELETE /projects/{project_id}
# TODO: implement delete project from database

###############################################################
# videos table
###############################################################


# POST /projects/{project_id}/videos
def create_video(db: Session, video: schemas.VideoCreate):
    # Get local version of current date using %x format, example: 12/31/18
    current_datetime = datetime.datetime.now()
    current_date = current_datetime.strftime("%x")

    db_video = models.Video(
        name=video.name, project_id=video.project_id, date_uploaded=current_date
    )
    db.add(db_video)
    db.commit()
    db.refresh(db_video)
    return db_video


def get_video_by_name(db: Session, video_name: str):
    return db.query(models.Video).filter(models.Video.name == video_name).first()


def get_videos_by_project_id(db: Session, project_id: Uuid):
    return db.query(models.Video).filter(models.Video.project_id == project_id).all()


def get_video_by_id(db: Session, video_id: Uuid):
    return db.query(models.Video).filter(models.Video.id == video_id).first()


def set_video_preprocessing_status(db: Session, video_id: Uuid, status: String):
    stmt = (
        update(models.Video)
        .where(models.Video.id == video_id)
        .values(preprocessing_status=status)
    )
    db.execute(stmt)
    db.commit()


###############################################################
# frames table
###############################################################


def insert_one_frame(db: Session, frame: schemas.FrameCreate):
    db_frame = models.Frame(
        width=frame.width,
        height=frame.height,
        frame_url=frame.frame_url,
        project_id=frame.project_id,
        video_id=frame.video_id,
    )
    db.add(db_frame)
    db.commit()
    db.refresh(db_frame)
    return db_frame


def insert_frames(db: Session, frames: List[schemas.FrameCreate]):
    db_frames = [
        models.Frame(
            width=frame.width,
            height=frame.height,
            frame_url=frame.frame_url,
            project_id=frame.project_id,
            video_id=frame.video_id,
        )
        for frame in frames
    ]
    db.add_all(db_frames)
    db.commit()


def get_frames_by_video_id(db: Session, video_id: Uuid):
    return db.query(models.Frame).filter(models.Frame.video_id == video_id).all()


def get_frames_by_project_id(db: Session, project_id: Uuid):
    return db.query(models.Frame).filter(models.Frame.project_id == project_id).all()


def get_frame_by_id(db: Session, frame_id: Uuid):
    return db.query(models.Frame).filter(models.Frame.id == frame_id).first()


def update_frames(db: Session, updated_frames: List[schemas.Frame]):
    result = db.execute(
        update(models.Frame), [frame.dict() for frame in updated_frames]
    )
    db.commit()
    return result


###############################################################
# bounding_boxes table
###############################################################


def insert_boxes(db: Session, boxes: List[schemas.BoundingBoxCreate]):
    db_boxes = [
        models.BoundingBox(
            x_top_left=box.x_top_left,
            y_top_left=box.y_top_left,
            x_bottom_right=box.x_bottom_right,
            y_bottom_right=box.y_bottom_right,
            width=box.width,
            height=box.height,
            frame_id=box.frame_id,
            label_id=box.label_id,
            image_features=box.image_features,
            prediction=box.prediction,
        )
        for box in boxes
    ]
    db.add_all(db_boxes)
    db.commit()


def get_boxes_by_frame_id(db: Session, frame_id: Uuid):
    return (
        db.query(models.BoundingBox)
        .filter(models.BoundingBox.frame_id == frame_id)
        .all()
    )


def update_boxes(db: Session, updated_boxes: List[schemas.BoundingBox]):
    result = db.execute(
        update(models.BoundingBox), [box.dict() for box in updated_boxes]
    )
    db.commit()
    return result


def get_box_vectors_and_labels_by_video_id(db: Session, video_id: Uuid):
    b = aliased(models.BoundingBox)
    f = aliased(models.Frame)
    l = aliased(models.Label)

    # Find all bounding boxes from every frame that exists in this video
    subquery = db.query(f.id).filter(f.video_id == video_id).subquery()
    query = (
        db.query(b, subquery.c.id, l.name)
        .join(b, b.frame_id == subquery.c.id)
        .join(l, l.id == b.label_id, isouter=True)
    )
    return query.all()


def get_box_by_id(db: Session, box_id: Uuid):
    return db.query(models.BoundingBox).filter(models.BoundingBox.id == box_id).first()


def delete_box_by_id(db: Session, box_id: Uuid):
    db.execute(delete(models.BoundingBox).where(models.BoundingBox.id == box_id))
    db.commit()


###############################################################
# labels table
###############################################################


def insert_labels(db: Session, labels: List[schemas.LabelCreate]):
    db_labels = [
        models.Label(name=label.name, project_id=label.project_id) for label in labels
    ]
    db.add_all(db_labels)
    db.commit()


def get_label_by_name_and_project(db: Session, name: str, project_id: Uuid):
    return (
        db.query(models.Label)
        .filter(models.Label.name == name, models.Label.project_id == project_id)
        .first()
    )


def get_labels_by_project(db: Session, project_id: Uuid):
    return db.query(models.Label).filter(models.Label.project_id == project_id).all()


def get_label_counts_by_project(db: Session, project_id: Uuid):
    return (
        db.query(models.Label.id, models.Label.name, func.count(models.BoundingBox.id))
        .join(models.BoundingBox, models.BoundingBox.label_id == models.Label.id)
        .filter(models.Label.project_id == project_id)
        .group_by(models.Label)
        .order_by(func.count(models.BoundingBox.id).desc())
        .all()
    )


def get_unique_labels_per_frame(db: Session, video_id: Uuid):
    # Define aliases for the tables
    b = aliased(models.BoundingBox)
    f = aliased(models.Frame)
    l = aliased(models.Label)

    # Build the JOIN query to get unique list of label IDs per frame
    # in the specificied video
    subquery = db.query(f.id).filter(f.video_id == video_id).subquery()
    query = (
        db.query(subquery.c.id, func.array_agg(l.id.distinct()))
        .join(b, b.frame_id == subquery.c.id, isouter=True)
        .join(l, l.id == b.label_id, isouter=True)
        .group_by(subquery.c.id)
    )
    return query.all()


def get_label_by_id(db: Session, label_id: Uuid):
    return db.query(models.Label).filter(models.Label.id == label_id).first()


def replace_label(db: Session, label_id: Uuid, replace_id: Uuid):
    db.execute(
        update(models.BoundingBox)
        .where(models.BoundingBox.label_id == label_id)
        .values(label_id=replace_id)
    )
    db.commit()


def delete_label_by_id(db: Session, label_id: Uuid):
    db.execute(delete(models.Label).where(models.Label.id == label_id))
    db.commit()
