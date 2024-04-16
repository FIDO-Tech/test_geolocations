from datetime import date
from typing import Optional

from geoalchemy2.shape import to_shape
from pydantic import BaseModel, PositiveInt, field_validator
from pydantic_extra_types.coordinate import Latitude, Longitude


class NearbyCitiesSchema(BaseModel):
    city: str
    county: str
    state_code: str
    km_within: PositiveInt


class NearbyCitiesByCoordsSchema(BaseModel):
    lat: Latitude
    long: Longitude
    km_within: PositiveInt


class CitySchema(BaseModel):
    city: str
    county: str
    state_code: str
    state_name: str
    geo_location: str

    @field_validator("geo_location", mode="before")
    def turn_geo_location_into_wkt(cls, value):
        return to_shape(value).wkt

    # Define the DMA model (simplified version)


class DmaSchema(BaseModel):
    dma_id: int
    dma_key: str
    dma_name: str
    dma_long: str
    region: str
    zone: str
    geom: Optional[str]
    start_date: Optional[date]

    class Config:
        json_schema_extra = {
            "example": {
                "dma_id": 1,
                "dma_key": "2300",
                "dma_name": "Example DMA",
                "dma_long": "Example long description",
                "region": "Northwest",
                "zone": "Urban",
                "geom": "POLYGON((-70.6693 43.0722, -70.6693 43.0723, -70.6692 43.0723, -70.6692 43.0722, -70.6693 43.0722))",
                "start_date": "2023-04-01",
            }
        }

    # @classmethod
    # def from_orm(cls, obj):
    #     obj_data = obj.__dict__.copy()
    #     if "geom" in obj_data and isinstance(obj_data["geom"], WKBElement):
    #         geom_wkt = loads(bytes(obj_data["geom"])).wkt
    #         obj_data["geom"] = geom_wkt
    #     return cls(**obj_data)

    @field_validator("geom", mode="before")
    def turn_geo_location_into_wkt(cls, value):
        if value is not None:
            return to_shape(value).wkt
        return value

    # @validator("geom", pre=True, allow_reuse=True)
    # def turn_geo_location_into_wkt(cls, v):
    #     if v is not None:
    #         return shape(json.loads(v)).wkt
    #     return v
