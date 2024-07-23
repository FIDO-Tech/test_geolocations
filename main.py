import csv
from datetime import date, datetime

from fastapi import Depends, FastAPI, HTTPException, Path, Query, status
from geoalchemy2.functions import (
    ST_Area,
    ST_Distance,
    ST_DWithin,
    ST_GeogFromText,
    ST_GeogFromWKB,
    ST_GeomFromText,
    ST_Intersects,
    ST_MakePoint,
    ST_SetSRID,
    ST_Transform,
)
from shapely.wkt import loads
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession
from typing_extensions import Optional

from database import get_async_session
from models import City, Dma, Pipe
from schemas import (
    CitySchema,
    DmaSchema,
    NearbyCitiesByCoordsSchema,
    NearbyCitiesSchema,
)
from services import is_city_table_empty, is_dma_table_empty, is_pipes_table_empty

app = FastAPI()


@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.get("/load-cities")
async def load_cities(db_session: AsyncSession = Depends(get_async_session)):
    if await is_city_table_empty(db_session):
        cities = []
        with open("us_cities.csv", "r") as csv_file:
            csv_reader = csv.reader(csv_file, delimiter=",")

            # Skip the first row (header)
            next(csv_reader)

            for row in csv_reader:
                city = City(
                    state_code=row[1],
                    state_name=row[2],
                    city=row[3],
                    county=row[4],
                    geo_location=f"POINT({row[5]} {row[6]})",
                )
                cities.append(city)

            db_session.add_all(cities)
            await db_session.commit()
            return {"message": "Data loaded successfully"}

    return {"message": "Data is already loaded"}


@app.get("/load-dmas")
async def load_dmas(db_session: AsyncSession = Depends(get_async_session)):
    try:
        if await is_dma_table_empty(db_session):
            csv.field_size_limit(10000000)
            dmas = []
            with open("output.csv", "r") as csv_file:
                csv_reader = csv.reader(csv_file, delimiter=";")

                # Skip the first row (header)
                next(csv_reader)

                for row in csv_reader:
                    wkt_geom = None

                    # Check if the geometry field is not empty
                    if row[6]:
                        polygon = loads(row[6])
                        if (
                            polygon.geom_type == "Polygon"
                            or polygon.geom_type == "MultiPolygon"
                        ):
                            wkt_geom = polygon.wkt
                        else:
                            # Handle the case of unsupported geometry type
                            print(
                                f"Unsupported geometry type for DMA {row[2]}: {polygon.geom_type}"
                            )
                            continue  # Skip this row due to invalid geometry type

                    dma = Dma(
                        # dma_id=row[0],
                        dma_key=row[1],
                        dma_name=row[2],
                        dma_long=row[3],
                        region=row[4],
                        zone=row[5],
                        geom=wkt_geom,
                        max_bug_coverage=float(row[7]) if row[7] else None,
                        start_date=datetime.strptime(row[8], "%Y-%m-%d").date()
                        if row[8]
                        else None,
                        end_date=datetime.strptime(row[9], "%Y-%m-%d").date()
                        if row[9]
                        else None,
                        # geo_location=f"POINT({row[5]} {row[6]})",
                    )
                    dmas.append(dma)
                db_session.add_all(dmas)
                await db_session.commit()
                return {"message": "Data loaded successfully"}
    except Exception as e:
        print(e)
        return {"message": "An error occurred while loading data"}

    return {"message": "Data is already loaded"}


@app.get("/load-pipes")
async def load_pipes(db_session: AsyncSession = Depends(get_async_session)):
    try:
        if await is_pipes_table_empty(db_session):
            csv.field_size_limit(10000000)
            pipes = []
            with open("output_pipes.csv", "r") as csv_file:
                csv_reader = csv.reader(csv_file, delimiter=";")

                # Skip the first row (header)
                next(csv_reader)

                for row in csv_reader:
                    wkt_geom = None
                    # Check if the geometry field is not empty
                    if row[1]:
                        line = loads(row[1])
                        if (
                            line.geom_type == "LineString"
                            or line.geom_type == "MultiLineString"
                        ):
                            wkt_geom = line.wkt
                        else:
                            # Handle the case of unsupported geometry type
                            print(
                                f"Unsupported geometry type for Pipe {row[2]}: {line.geom_type}"
                            )
                            continue  # Skip this row due to invalid geometry type

                    pipe = Pipe(
                        # pipe_id=row[0],
                        geom=wkt_geom,
                        material=row[2],
                        pipe_key=row[3],
                        created_date=datetime.strptime(
                            row[4], "%Y-%m-%d %H:%M:%S"
                        ).date()
                        if row[4]
                        else None,
                        diameter_mm=float(row[5]) if row[5] else None,
                        pipe_type=row[6],
                        pipe_subtype=row[7],
                        standardised_material=row[8],
                        dma_id=int(row[9]) if row[9] else None,
                        company_id=int(row[10]) if row[10] else None,
                    )
                    pipes.append(pipe)
                db_session.add_all(pipes)
                await db_session.commit()
                return {"message": "Data loaded successfully"}
    except Exception as e:
        print(e)
        return {"message": "An error occurred while loading data"}
    return {"message": "Data is already loaded"}


@app.get("/dmas", response_model=list[DmaSchema])
async def get_dmas(
    page: int = Query(1, description="The page number to retrieve.", gt=0),
    per_page: int = Query(10, description="The number of records per page."),
    dma_key: Optional[str] = Query(None, description="The DMA key to filter by."),
    start_date: Optional[date] = Query(
        None, description="The start date to filter by in format YYYY-MM-DD."
    ),
    db_session: AsyncSession = Depends(get_async_session),
):
    """
    A function to retrieve DMAs based on optional filters for DMA key and start date.

    Parameters
    ----------
    pagination : PaginationParams
        The pagination parameters (page and limit). Use separate schema to validate values
    dma_key : Optional[str]
        The DMA key to filter by.
    start_date : Optional[date]
        The start date to filter by in format YYYY-MM-DD.
    db_session : AsyncSession
        The database session to use for executing the query.

    Returns
    -------
    List[Dma]
        A list of Dma objects based on the provided filters, with pagination (skip and limit).
    """
    # This is where you would normally interact with your internal ORM or database to retrieve (and potentially filter) the records.

    query = select(Dma).offset((page - 1) * per_page).limit(per_page)
    if dma_key:
        query = query.where(Dma.dma_key == dma_key)
    if start_date:
        query = query.where(Dma.start_date <= start_date)

    result = await db_session.execute(query)

    return result.scalars().all()


@app.get("/dmas/nearby", response_model=list[DmaSchema])
async def get_nearby_dmas(
    latitude: float = 51.53155502944422,
    longitude: float = -0.15432151225325608,
    distance: int = 1000,  # Distance in meters
    db_session: AsyncSession = Depends(get_async_session),
):
    """
    Get nearby DMAs within a specified distance from a given latitude and longitude.

    Parameters
    ----------
    latitude : float, optional
        The latitude of the point (default is 0.0).
    longitude : float, optional
        The longitude of the point (default is 0.0).
    distance : int, optional
        The distance in meters within which to search for DMAs (default is 1000).
    db_session : AsyncSession, optional
        The database session (default is obtained from `get_async_session`).

    Returns
    -------
    List[Dma]
        A list of nearby DMAs.

    """

    # Point WKT format
    point = f"SRID=4326;POINT({longitude} {latitude})"

    # Query DMAs within the specified distance from the point
    query = select(Dma).where(
        ST_DWithin(
            Dma.geom,  # Assuming your geometry column is named 'geom'
            ST_GeogFromText(point),
            distance,
        )
    )
    result = await db_session.execute(query)
    return result.scalars().all()


@app.get("/dmas/total_area")
async def get_total_area(
    region: str = Query(
        description="The region to calculate the total area for. (europe, usa, india)",
        default="europe",
    ),
    dma_key: str = Query(description="The DMA key to filter by. (314-07)"),
    db_session: AsyncSession = Depends(get_async_session),
):
    epsg_codes = {
        "europe": 3035,
        "usa": 5070,
        "india": 24376,
    }
    if region not in epsg_codes:
        raise HTTPException(status_code=400, detail="Invalid region")
    query = select(ST_Area(ST_Transform(Dma.geom, epsg_codes[region])))
    if dma_key:
        query = query.where(Dma.dma_key == dma_key)

    result = await db_session.execute(query)
    return {"value": result.scalar_one(), "unit": "m²"}


@app.get("/dmas/intersecting", response_model=list[DmaSchema])
async def get_dmas_intersecting_polygon(
    # polygon_wkt: str = "POLYGON((51.52938 -0.15429, 51.53050 -0.14742, 51.52682 -0.14691, 51.52618 -0.15275, 51.52938 -0.15429)",  # Polygon as Well-Known Text (WKT)
    polygon_wkt: str = "-0.15429 51.52938, -0.14742 51.53050, -0.14691 51.52682, -0.15275 51.52618, -0.15429 51.52938",
    db_session: AsyncSession = Depends(get_async_session),
):
    # Convert the WKT polygon to a PostGIS geometry
    polygon = ST_GeomFromText(
        f"POLYGON(({polygon_wkt}))", 4326
    )  # SRID 4326 for GPS coordinates

    query = select(Dma).where(ST_Intersects(Dma.geom, polygon))

    result = await db_session.execute(query)
    return result.scalars().all()


@app.get("/dmas/nearest/distance", response_model=dict)
async def get_distance_to_nearest_dma(
    latitude: float = 51.53409,
    longitude: float = -0.16270,
    db_session: AsyncSession = Depends(get_async_session),
):
    point = ST_SetSRID(ST_MakePoint(longitude, latitude), 4326)
    query = (
        select(
            ST_Distance(
                Dma.geom,
                point,
                True,  # Use spherical geometry for distance calculation
            )
        )
        .order_by(ST_Distance(Dma.geom, point))
        .limit(1)
    )

    result = await db_session.execute(query)
    return {"value": result.scalar_one(), "units": "m"}


@app.get("/cities", response_model=list[CitySchema])
async def get_all_cities(db_session: AsyncSession = Depends(get_async_session)):
    query = select(City)
    result = await db_session.execute(query)
    cities = result.scalars().all()

    return cities


@app.post("/nearby-cities-by-details")
async def get_nearby_cities_by_details(
    nearby_cities_schema: NearbyCitiesSchema,
    db_session: AsyncSession = Depends(get_async_session),
):
    city, county, state_code, km_within = (
        nearby_cities_schema.city,
        nearby_cities_schema.county,
        nearby_cities_schema.state_code,
        nearby_cities_schema.km_within,
    )

    # Check if the target city exists and retrieve its geography
    target_city_query = select(City).where(
        and_(City.city == city, City.state_code == state_code, City.county == county)
    )
    result = await db_session.execute(target_city_query)
    target_city = result.scalar_one_or_none()

    # If the target city is not found, return an error message
    if not target_city:
        raise HTTPException(
            status=status.HTTP_404_NOT_FOUND,
            detail="City with provided deails was not found",
        )

    # Extract the geography of the target city
    target_geography = ST_GeogFromWKB(target_city.geo_location)

    # Query nearby cities within the specified distance from the target city
    nearby_cities_query = select(City.city).where(
        ST_DWithin(City.geo_location, target_geography, 1000 * km_within)
    )
    result = await db_session.execute(nearby_cities_query)
    nearby_cities = result.scalars().all()

    return nearby_cities


@app.post("/nearby-cities-by-coordinates")
async def get_nearby_cities_by_coords(
    coords_schema: NearbyCitiesByCoordsSchema,
    db_session: AsyncSession = Depends(get_async_session),
):
    lat, long, km_within = (
        coords_schema.lat,
        coords_schema.long,
        coords_schema.km_within,
    )

    target_geography = ST_GeogFromText(f"POINT({lat} {long})", srid=4326)

    nearby_cities_query = select(City.city).where(
        ST_DWithin(City.geo_location, target_geography, 1000 * km_within)
    )
    result = await db_session.execute(nearby_cities_query)
    nearby_cities = result.scalars().all()

    return nearby_cities


@app.get("/cities/{state_code}", response_model=list[CitySchema])
async def get_cities_in_state(
    state_code: str = Path(..., min_length=2, max_length=2),
    db_session: AsyncSession = Depends(get_async_session),
):
    query = select(City).where(City.state_code == state_code.upper())
    result = await db_session.execute(query)
    cities = result.scalars().all()

    if not cities:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No cities found for provided state: {state_code}",
        )

    return cities
