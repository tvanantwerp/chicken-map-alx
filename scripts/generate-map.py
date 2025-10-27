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
        tuple: (land_use_df, boundary_gdf, parcels_gdf, buildings_gdf)
            - land_use_df: DataFrame with zoning codes
            - boundary_gdf: GeoDataFrame with boundary of Alexandria
            - parcels_gdf: GeoDataFrame with parcel boundaries
            - buildings_gdf: GeoDataFrame with building footprints
    """
    # Define data paths
    data_dir = Path(__file__).parent.parent / "data"

    # Read land use codes CSV
    land_use_path = data_dir / "land_use_codes.csv"
    print(f"Reading land use codes from {land_use_path}")
    land_use_df = pd.read_csv(land_use_path)

    # Read boundary shapefile
    boundary_path = data_dir / "boundary" / "Boundary.shp"
    print(f"Reading parcels from {boundary_path}")
    boundary_gdf = gpd.read_file(boundary_path)

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

    return land_use_df, boundary_gdf, parcels_gdf, buildings_gdf


def prepare_data(land_use_df, boundary_gdf, parcels_gdf, buildings_gdf):
    """
    Ensure all GeoDataFrames use the same CRS and validate required fields.
    Also merges building use data with buildings GeoDataFrame.

    Args:
        land_use_df: DataFrame with zoning codes
        boundary_gdf: GeoDataFrame with city boundary
        parcels_gdf: GeoDataFrame with parcel boundaries
        buildings_gdf: GeoDataFrame with building footprints

    Returns:
        tuple: (land_use_df, boundary_gdf, parcels_gdf, buildings_gdf) with standardized CRS
               buildings_gdf will include USE data merged from buildings-use.csv
    """
    print("\nPreparing data...")

    # Check current CRS of all GeoDataFrames
    print(f"  Boundary CRS: {boundary_gdf.crs}")
    print(f"  Parcels CRS: {parcels_gdf.crs}")
    print(f"  Buildings CRS: {buildings_gdf.crs}")

    # Use the parcels CRS as the standard (should be Alexandria's local projection)
    target_crs = parcels_gdf.crs
    print(f"\n  Standardizing all data to CRS: {target_crs}")

    # Convert all GeoDataFrames to the same CRS
    if boundary_gdf.crs != target_crs:
        boundary_gdf = boundary_gdf.to_crs(target_crs)
        print("    - Boundary converted")

    if buildings_gdf.crs != target_crs:
        buildings_gdf = buildings_gdf.to_crs(target_crs)
        print("    - Buildings converted")

    # Load and merge building use data
    print("\n  Merging building use data...")
    data_dir = Path(__file__).parent.parent / "data"
    buildings_use_path = data_dir / "buildings-use.csv"
    buildings_use_df = pd.read_csv(buildings_use_path)

    print(f"    - Loaded {len(buildings_use_df)} building use records")
    print(f"    - Buildings before merge: {len(buildings_gdf)}")

    # Merge building use data with buildings (keeping all buildings even if no use data)
    buildings_gdf = buildings_gdf.merge(
        buildings_use_df[['FACILITYID', 'UUSE', 'SIZE', 'UNITS', 'OWNERSHIP']],
        on='FACILITYID',
        how='left'
    )

    # Rename UUSE to USE for consistency with spec
    buildings_gdf = buildings_gdf.rename(columns={'UUSE': 'USE'})

    print(f"    - Buildings after merge: {len(buildings_gdf)}")
    print(f"    - Buildings with USE data: {buildings_gdf['USE'].notna().sum()}")

    # Validate required fields
    print("\n  Validating required fields...")

    # Check parcels has geometry
    if 'geometry' not in parcels_gdf.columns:
        raise ValueError("Parcels GeoDataFrame missing 'geometry' column")

    # Check buildings has geometry, FACILITYID, and USE
    if 'geometry' not in buildings_gdf.columns:
        raise ValueError("Buildings GeoDataFrame missing 'geometry' column")
    if 'FACILITYID' not in buildings_gdf.columns:
        raise ValueError("Buildings GeoDataFrame missing 'FACILITYID' column")
    if 'USE' not in buildings_gdf.columns:
        raise ValueError("Buildings GeoDataFrame missing 'USE' column")

    # Check boundary has geometry
    if 'geometry' not in boundary_gdf.columns:
        raise ValueError("Boundary GeoDataFrame missing 'geometry' column")

    print("    - All required fields present")
    print("  Data preparation complete!")

    return land_use_df, boundary_gdf, parcels_gdf, buildings_gdf


def identify_residential_parcels(parcels_gdf, land_use_df):
    """
    Identify residential and non-residential parcels based on zoning codes.

    Parcels are classified as residential if their DESCRIPTION contains "residential" (case-insensitive).

    Args:
        parcels_gdf: GeoDataFrame with parcel boundaries and ZONING column
        land_use_df: DataFrame with zoning codes and descriptions

    Returns:
        tuple: (residential_parcels_gdf, non_residential_parcels_gdf)
    """
    print("\nIdentifying residential parcels...")

    # Join parcels with land use codes to get descriptions
    parcels_with_use = parcels_gdf.merge(
        land_use_df[['ZONING', 'DESCRIPTION']],
        on='ZONING',
        how='left'
    )

    print(f"  Total parcels: {len(parcels_with_use)}")

    # Filter to residential parcels (DESCRIPTION contains "residential", case-insensitive)
    residential_mask = parcels_with_use['DESCRIPTION'].str.contains('residential', case=False, na=False)
    residential_parcels_gdf = parcels_with_use[residential_mask].copy()
    non_residential_parcels_gdf = parcels_with_use[~residential_mask].copy()

    print(f"  Residential parcels: {len(residential_parcels_gdf)}")
    print(f"  Non-residential parcels: {len(non_residential_parcels_gdf)}")

    # Show unique residential zoning codes
    residential_zones = sorted(residential_parcels_gdf['ZONING'].unique())
    print(f"  Residential zoning codes found: {', '.join(residential_zones)}")

    return residential_parcels_gdf, non_residential_parcels_gdf


def identify_dwelling_buildings(buildings_gdf):
    """
    Filter buildings to only those used as dwellings (households).

    A dwelling is defined as a building with USE == "Household" based on the
    buildings-use.csv data that was already merged in prepare_data().

    Args:
        buildings_gdf: GeoDataFrame with building footprints and USE column

    Returns:
        GeoDataFrame: dwelling_buildings_gdf (only residential/household buildings)
    """
    print("\nIdentifying dwelling buildings...")

    print(f"  Total buildings: {len(buildings_gdf)}")
    print(f"  Buildings with USE data: {buildings_gdf['USE'].notna().sum()}")

    # Filter to only household buildings
    dwelling_buildings_gdf = buildings_gdf[buildings_gdf['USE'] == 'Household'].copy()

    print(f"  Dwelling buildings (USE='Household'): {len(dwelling_buildings_gdf)}")

    # Show sample of unique USE types for context
    use_counts = buildings_gdf['USE'].value_counts().head(10)
    print("\n  Top 10 building use types:")
    for use_type, count in use_counts.items():
        print(f"    - {use_type}: {count}")

    return dwelling_buildings_gdf


def calculate_allowed_areas(residential_parcels_gdf, dwelling_buildings_gdf):
    """
    Calculate areas where chickens are allowed on residential parcels.

    Chickens cannot be kept within 200 feet of dwellings not on the same parcel.

    Args:
        residential_parcels_gdf: GeoDataFrame with residential parcels
        dwelling_buildings_gdf: GeoDataFrame with dwelling buildings only

    Returns:
        GeoDataFrame with columns:
            - parcel_id: Original parcel identifier
            - geometry: Full parcel geometry
            - allowed_geometry: Area where chickens are allowed
            - prohibited_geometry: Area where chickens are prohibited
    """
    print("\nCalculating allowed areas for chicken keeping...")

    # Spatial join: which dwellings are on which parcels
    print("  Performing spatial join of dwellings to parcels...")
    dwellings_on_parcels = gpd.sjoin(
        dwelling_buildings_gdf,
        residential_parcels_gdf[['OBJECTID', 'geometry']],
        how='inner',
        predicate='within'
    )
    print(f"    - {len(dwellings_on_parcels)} dwellings matched to residential parcels")

    # Create 200-foot buffers around all dwellings (more efficient to do once)
    print("  Creating 200-foot buffers around all dwellings...")
    dwelling_buffers = dwelling_buildings_gdf.geometry.buffer(200, cap_style='round')
    print(f"    - Created {len(dwelling_buffers)} buffers")

    # Process each residential parcel
    print("  Processing each residential parcel...")
    results = []

    for idx, parcel in residential_parcels_gdf.iterrows():
        parcel_id = parcel['OBJECTID']

        # Get dwellings that ARE on this parcel
        dwellings_on_this_parcel = dwellings_on_parcels[
            dwellings_on_parcels['OBJECTID'] == parcel_id
        ]['FACILITYID'].tolist()

        # Get indices of dwellings that are NOT on this parcel
        external_dwelling_mask = ~dwelling_buildings_gdf['FACILITYID'].isin(dwellings_on_this_parcel)
        external_buffers = dwelling_buffers[external_dwelling_mask]

        # Union all external dwelling buffers
        if len(external_buffers) > 0:
            external_buffers_union = external_buffers.unary_union
            # Subtract external buffers from parcel to get allowed area
            allowed_geom = parcel.geometry.difference(external_buffers_union)
        else:
            # No external dwellings, entire parcel is allowed
            allowed_geom = parcel.geometry

        # Calculate prohibited area
        prohibited_geom = parcel.geometry.difference(allowed_geom)

        results.append({
            'parcel_id': parcel_id,
            'geometry': parcel.geometry,
            'allowed_geometry': allowed_geom,
            'prohibited_geometry': prohibited_geom
        })

    # Create results GeoDataFrame
    results_gdf = gpd.GeoDataFrame(results, crs=residential_parcels_gdf.crs)

    print("\n  Results:")
    print(f"    - Total residential parcels processed: {len(results_gdf)}")

    # Count parcels with some allowed area
    has_allowed = results_gdf['allowed_geometry'].apply(lambda g: not g.is_empty).sum()
    print(f"    - Parcels with some allowed area: {has_allowed}")
    print(f"    - Parcels with no allowed area: {len(results_gdf) - has_allowed}")

    return results_gdf


def main():
    """Main entry point for the script."""
    land_use_df, boundary_gdf, parcels_gdf, buildings_gdf = read_data()

    # Display basic info about the data
    print("\n" + "=" * 60)
    print("LAND USE CODES")
    print("=" * 60)
    print(land_use_df.head())
    print(f"\nColumns: {list(land_use_df.columns)}")

    print("\n" + "=" * 60)
    print("BOUNDARY")
    print("=" * 60)
    print(boundary_gdf.head())
    print(f"\nColumns: {list(boundary_gdf.columns)}")
    print(f"CRS: {boundary_gdf.crs}")

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
