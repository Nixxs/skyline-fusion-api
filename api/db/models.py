# api/db/models.py
from sqlalchemy import Column, Integer, String, Float, Text, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from api.db.session import Base

class Image(Base):
    __tablename__ = "images"

    image_id = Column(Integer, primary_key=True, index=True)
    name = Column(Text, nullable=False)
    lon = Column(Float)
    lat = Column(Float)
    alt_m = Column(Float)
    yaw_deg = Column(Float)
    created = Column(DateTime)
    url = Column(Text, nullable=False)
    imported_utc = Column(Text, nullable=False)

    # relationships
    classes = relationship("ImageLookup", back_populates="image")

class ImageClass(Base):
    __tablename__ = "image_classes"

    class_id = Column(String, primary_key=True, index=True)
    name = Column(Text)
    lon = Column(Float, nullable=False)
    lat = Column(Float, nullable=False)
    alt_m = Column(Float)
    yaw_deg = Column(Float)
    image_count = Column(Integer, nullable=False, default=0)
    updated_utc = Column(Text)

    images = relationship("ImageLookup", back_populates="image_class")

class ImageLookup(Base):
    __tablename__ = "image_lookup"

    image_id = Column(Integer, ForeignKey("images.image_id"), primary_key=True)
    class_id = Column(String, ForeignKey("image_classes.class_id"), primary_key=True)

    image = relationship("Image", back_populates="classes")
    image_class = relationship("ImageClass", back_populates="images")
