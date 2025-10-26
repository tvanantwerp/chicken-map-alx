#!/usr/bin/env python3
# /// script
# requires-python = ">=3.14"
# dependencies = [
#     "pandas",
#     "geopandas",
# ]
# ///
"""
Generate a map showing where backyard chickens are legally allowed in Alexandria, VA.

This script processes:
1. Land use codes (zoning) data
2. Parcel shapefiles
3. Building shapefiles

To determine which areas of residential parcels meet the legal requirements for keeping chickens.
"""

from pathlib import Path
import pandas as pd
import geopandas as gpd


def read_data():
    """
    Read all required data files.

    Returns:
        tuple: (land_use_df, parcels_gdf, buildings_gdf)
            - land_use_df: DataFrame with zoning codes
            - parcels_gdf: GeoDataFrame with parcel boundaries
            - buildings_gdf: GeoDataFrame with building footprints
    """
    # Define data paths
    data_dir = Path(__file__).parent.parent / "data"

    # Read land use codes CSV
    land_use_path = data_dir / "land_use_codes.csv"
    print(f"Reading land use codes from {land_use_path}")
    land_use_df = pd.read_csv(land_use_path)

    # Read parcels shapefile
    parcels_path = data_dir / "parcels" / "Alexandria_Parcels.shp"
    print(f"Reading parcels from {parcels_path}")
    parcels_gdf = gpd.read_file(parcels_path)

    # Read buildings shapefile
    buildings_path = data_dir / "buildings" / "Buildings.shp"
    print(f"Reading buildings from {buildings_path}")
    buildings_gdf = gpd.read_file(buildings_path)

    print("\nData loaded successfully:")
    print(f"  - Land use codes: {len(land_use_df)} rows")
    print(f"  - Parcels: {len(parcels_gdf)} features")
    print(f"  - Buildings: {len(buildings_gdf)} features")

    return land_use_df, parcels_gdf, buildings_gdf


def main():
    """Main entry point for the script."""
    land_use_df, parcels_gdf, buildings_gdf = read_data()

    # Display basic info about the data
    print("\n" + "=" * 60)
    print("LAND USE CODES")
    print("=" * 60)
    print(land_use_df.head())
    print(f"\nColumns: {list(land_use_df.columns)}")

    print("\n" + "=" * 60)
    print("PARCELS")
    print("=" * 60)
    print(parcels_gdf.head())
    print(f"\nColumns: {list(parcels_gdf.columns)}")
    print(f"CRS: {parcels_gdf.crs}")

    print("\n" + "=" * 60)
    print("BUILDINGS")
    print("=" * 60)
    print(buildings_gdf.head())
    print(f"\nColumns: {list(buildings_gdf.columns)}")
    print(f"CRS: {buildings_gdf.crs}")


if __name__ == "__main__":
    main()
