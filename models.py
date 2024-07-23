from datetime import date

from geoalchemy2 import Geometry, WKBElement
from sqlalchemy import Date, Float, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Mapped, mapped_column

Base = declarative_base()
metadata = Base.metadata


class City(Base):
    __tablename__ = "city"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    state_code: Mapped[str] = mapped_column(String(2))
    state_name: Mapped[str] = mapped_column(String(50))
    city: Mapped[str] = mapped_column(String(50))
    county: Mapped[str] = mapped_column(String(50))
    geo_location: Mapped[WKBElement] = mapped_column(
        Geometry(geometry_type="POINT", srid=4326, spatial_index=True)
    )


class Dma(Base):
    __tablename__ = "dmas"

    # Define columns as per the provided MySQL table schema
    dma_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    dma_key: Mapped[str] = mapped_column(String(200), nullable=True)
    dma_name: Mapped[str] = mapped_column(String(100), nullable=True)
    dma_long: Mapped[str] = mapped_column(String(100), nullable=True)
    region: Mapped[str] = mapped_column(String(100), nullable=True)
    zone: Mapped[str] = mapped_column(String(100), nullable=True)
    geom: Mapped[WKBElement] = mapped_column(
        Geometry(geometry_type="GEOMETRY", srid=4326), nullable=True
    )
    max_bug_coverage: Mapped[float] = mapped_column(Float, nullable=True)
    start_date: Mapped[date] = mapped_column(Date, nullable=True)
    end_date: Mapped[date] = mapped_column(Date, nullable=True)

    # Define constraints and indexes
    # __table_args__ = (UniqueConstraint("dma_key", name="uix_1"),)


class Pipe(Base):
    __tablename__ = "pipes"

    # Using explicit column types with additional parameters such as primary_key and autoincrement
    pipe_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    geom: Mapped[WKBElement] = mapped_column(
        Geometry(geometry_type="GEOMETRY", srid=4326), nullable=True
    )
    material: Mapped[str] = mapped_column(String(200), nullable=True)
    pipe_key: Mapped[str] = mapped_column(String(100), nullable=True)
    created_date: Mapped[date] = mapped_column(Date, nullable=True)
    diameter_mm: Mapped[float] = mapped_column(Float, nullable=True)
    pipe_type: Mapped[str] = mapped_column(String(200), nullable=True)
    pipe_subtype: Mapped[str] = mapped_column(String(45), nullable=True)
    standardised_material: Mapped[str] = mapped_column(String(45), nullable=True)
    dma_id: Mapped[int] = mapped_column(
        Integer, nullable=True
    )  # ForeignKey("dmas.dma_id"),
    company_id: Mapped[int] = mapped_column(Integer, nullable=True)
    # geom_indexed: Mapped[WKBElement] = mapped_column(
    #     Geometry(geometry_type="GEOMETRY", srid=4326, spatial_index=True),
    #     nullable=True,
    # )


class Asset(Base):
    __tablename__ = "assets"
    asset_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    asset_key: Mapped[str] = mapped_column(String(100), nullable=True)
    asset_type: Mapped[str] = mapped_column(String(200), nullable=True)
    asset_subtype: Mapped[str] = mapped_column(String(45), nullable=True)
    geom: Mapped[WKBElement] = mapped_column(
        Geometry(geometry_type="GEOMETRY", srid=4326), nullable=True
    )
    created_date: Mapped[date] = mapped_column(Date, nullable=True)
    diameter_mm: Mapped[float] = mapped_column(Float, nullable=True)
    standardised_asset_type: Mapped[str] = mapped_column(String(65), nullable=True)
    dma_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("dmas.dma_id"), nullable=True
    )
    company_id: Mapped[int] = mapped_column(Integer, nullable=True)
    geom_indexed: Mapped[WKBElement] = mapped_column(
        Geometry(geometry_type="GEOMETRY", srid=4326), nullable=True
    )

    __table_args__ = (
        UniqueConstraint("asset_key", "asset_subtype", name="uooipqspoiqsioqsp"),
    )
