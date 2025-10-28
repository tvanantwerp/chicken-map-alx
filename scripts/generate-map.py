#!/usr/bin/env python3
# /// script
# requires-python = ">=3.14"
# dependencies = [
#     "pandas",
#     "geopandas",
#     "matplotlib",
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
import matplotlib.pyplot as plt
from matplotlib.patches import Patch


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

    # Normalize zoning codes by removing spaces to handle mismatches
    # (e.g., "R 8" in shapefile vs "R8" in CSV)
    parcels_normalized = parcels_gdf.copy()
    parcels_normalized['ZONING_NORMALIZED'] = parcels_normalized['ZONING'].str.replace(' ', '', regex=False)

    land_use_normalized = land_use_df.copy()
    land_use_normalized['ZONING_NORMALIZED'] = land_use_normalized['ZONING'].str.replace(' ', '', regex=False)

    # Join parcels with land use codes to get descriptions
    parcels_with_use = parcels_normalized.merge(
        land_use_normalized[['ZONING_NORMALIZED', 'DESCRIPTION']],
        on='ZONING_NORMALIZED',
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

    This function uses spatial indexing to efficiently process large datasets.

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

    # Pre-compute dwelling-to-parcel mapping for fast lookup
    print("  Building dwelling-to-parcel lookup...")
    parcel_to_dwellings = (
        dwellings_on_parcels
        .groupby('OBJECTID_right')['FACILITYID']
        .apply(set)
        .to_dict()
    )
    print(f"    - Created lookup for {len(parcel_to_dwellings)} parcels with dwellings")

    # Create 200-foot buffers around all dwellings
    print("  Creating 200-foot buffers around all dwellings...")
    dwelling_buffers = dwelling_buildings_gdf.geometry.buffer(200, cap_style='round')

    # Create GeoDataFrame of buffers for spatial indexing
    dwelling_buffers_gdf = gpd.GeoDataFrame(
        dwelling_buildings_gdf[['FACILITYID']].copy(),
        geometry=dwelling_buffers,
        crs=dwelling_buildings_gdf.crs
    )
    print(f"    - Created {len(dwelling_buffers_gdf)} buffers")

    # Spatial join: which buffers intersect which parcels (uses spatial index)
    print("  Finding buffers that intersect parcels (using spatial index)...")
    # Reset index of parcels to ensure OBJECTID is a column, not index
    parcels_for_join = residential_parcels_gdf[['OBJECTID', 'geometry']].reset_index(drop=True)

    buffers_intersecting_parcels = gpd.sjoin(
        dwelling_buffers_gdf,
        parcels_for_join,
        how='inner',
        predicate='intersects'
    )
    print(f"    - Found {len(buffers_intersecting_parcels)} buffer-parcel intersections")

    # Group by parcel for efficient processing
    print("  Processing parcels in groups...")
    results = []

    # Create a mapping of parcel_id to external buffers that intersect it
    parcel_to_external_buffers = {}

    # After sjoin, OBJECTID from the right dataframe should be in the result
    # Check if we need to use OBJECTID or OBJECTID_right
    parcel_id_col = 'OBJECTID' if 'OBJECTID_right' not in buffers_intersecting_parcels.columns else 'OBJECTID_right'

    for parcel_id, group in buffers_intersecting_parcels.groupby(parcel_id_col):
        # Get dwellings that are ON this parcel
        dwellings_on_this_parcel = parcel_to_dwellings.get(parcel_id, set())

        # Filter to only external dwellings (not on this parcel)
        external_buffer_indices = group[
            ~group['FACILITYID'].isin(dwellings_on_this_parcel)
        ].index

        # Store the geometries of external buffers
        if len(external_buffer_indices) > 0:
            parcel_to_external_buffers[parcel_id] = dwelling_buffers_gdf.loc[external_buffer_indices, 'geometry']

    # Process each residential parcel
    for idx, parcel in residential_parcels_gdf.iterrows():
        parcel_id = parcel['OBJECTID']

        # Get external buffers that intersect this parcel
        external_buffers = parcel_to_external_buffers.get(parcel_id)

        # Calculate allowed area
        if external_buffers is not None and len(external_buffers) > 0:
            # Union only the relevant external buffers
            external_buffers_union = external_buffers.union_all()
            # Subtract external buffers from parcel to get allowed area
            allowed_geom = parcel.geometry.difference(external_buffers_union)
        else:
            # No external dwellings nearby, entire parcel is allowed
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


def create_visualization_layers(boundary_gdf, residential_parcels_gdf, non_residential_parcels_gdf, results_gdf):
    """
    Create separate GeoDataFrames for each visualization layer.

    Args:
        boundary_gdf: GeoDataFrame with city boundary
        residential_parcels_gdf: GeoDataFrame with residential parcels
        non_residential_parcels_gdf: GeoDataFrame with non-residential parcels
        results_gdf: GeoDataFrame with allowed/prohibited areas

    Returns:
        tuple: (boundary_layer, non_res_layer, prohibited_layer, allowed_layer)
    """
    print("\nCreating visualization layers...")

    # Layer 1: Boundary - city outline
    boundary_layer = boundary_gdf.copy()
    print(f"  - Boundary layer: {len(boundary_layer)} features")

    # Layer 2: Non-residential parcels
    non_res_layer = non_residential_parcels_gdf[['geometry']].copy()
    print(f"  - Non-residential layer: {len(non_res_layer)} features")

    # Layer 3: Prohibited residential areas
    # Extract prohibited geometries from results
    prohibited_geoms = []
    for idx, row in results_gdf.iterrows():
        if not row['prohibited_geometry'].is_empty:
            prohibited_geoms.append({'geometry': row['prohibited_geometry']})

    prohibited_layer = gpd.GeoDataFrame(prohibited_geoms, crs=results_gdf.crs)
    print(f"  - Prohibited residential layer: {len(prohibited_layer)} features")

    # Layer 4: Allowed residential areas
    # Extract allowed geometries from results
    allowed_geoms = []
    for idx, row in results_gdf.iterrows():
        if not row['allowed_geometry'].is_empty:
            allowed_geoms.append({'geometry': row['allowed_geometry']})

    allowed_layer = gpd.GeoDataFrame(allowed_geoms, crs=results_gdf.crs)
    print(f"  - Allowed residential layer: {len(allowed_layer)} features")

    print("  Visualization layers created!")

    return boundary_layer, non_res_layer, prohibited_layer, allowed_layer


def generate_map(boundary_layer, non_res_layer, prohibited_layer, allowed_layer, output_dir):
    """
    Generate a map visualization showing chicken zoning areas.

    Args:
        boundary_layer: GeoDataFrame with city boundary
        non_res_layer: GeoDataFrame with non-residential parcels
        prohibited_layer: GeoDataFrame with prohibited residential areas
        allowed_layer: GeoDataFrame with allowed residential areas
        output_dir: Path to directory for saving output files

    Returns:
        matplotlib.figure.Figure: The generated figure object
    """
    print("\nGenerating map visualization...")

    # Create output directory if it doesn't exist
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Create figure with appropriate size (16x12 inches for good detail)
    fig, ax = plt.subplots(figsize=(16, 12))

    # Plot layers in order (bottom to top)
    # Layer 1: Non-residential parcels (light gray)
    if len(non_res_layer) > 0:
        non_res_layer.plot(ax=ax, color='#CCCCCC', edgecolor='none', label='Non-residential')
        print(f"  - Plotted {len(non_res_layer)} non-residential parcels")

    # Layer 2: Prohibited residential areas (dark gray)
    if len(prohibited_layer) > 0:
        prohibited_layer.plot(ax=ax, color='#666666', edgecolor='none', label='Prohibited (within 200ft of dwelling)')
        print(f"  - Plotted {len(prohibited_layer)} prohibited areas")

    # Layer 3: Allowed residential areas (bright green)
    if len(allowed_layer) > 0:
        allowed_layer.plot(ax=ax, color='#4CAF50', edgecolor='none', label='Allowed for chickens')
        print(f"  - Plotted {len(allowed_layer)} allowed areas")

    # Layer 4: Boundary outline (black, 2pt line)
    boundary_layer.plot(ax=ax, facecolor='none', edgecolor='black', linewidth=2, label='City boundary')
    print(f"  - Plotted city boundary")

    # Add title
    ax.set_title('Alexandria, VA: Backyard Chicken Zoning', fontsize=20, fontweight='bold', pad=20)

    # Add legend
    ax.legend(loc='upper right', fontsize=12, framealpha=0.9)

    # Remove axis ticks and labels for clean map
    ax.set_xticks([])
    ax.set_yticks([])
    ax.set_xlabel('')
    ax.set_ylabel('')

    # Remove axis spines for cleaner look
    for spine in ax.spines.values():
        spine.set_visible(False)

    # Tight layout
    plt.tight_layout()

    # Save as PNG
    png_path = output_dir / 'chicken_map.png'
    plt.savefig(png_path, dpi=300, bbox_inches='tight')
    print(f"\n  Saved PNG to: {png_path}")

    # Save as SVG
    svg_path = output_dir / 'chicken_map.svg'
    plt.savefig(svg_path, format='svg', bbox_inches='tight')
    print(f"  Saved SVG to: {svg_path}")

    print("  Map generation complete!")

    return fig


def export_shapefile(results_gdf, output_path):
    """
    Export the complete results GeoDataFrame as a shapefile.

    Args:
        results_gdf: GeoDataFrame with parcel_id, geometry, allowed_geometry, prohibited_geometry
        output_path: Path where the shapefile should be saved

    Returns:
        Path: The output path where the shapefile was saved
    """
    print("\nExporting results to shapefile...")

    # Ensure output path is a Path object
    output_path = Path(output_path)

    # Create output directory if it doesn't exist
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Export the complete results GeoDataFrame
    # Note: Shapefiles have column name limitations (10 chars max), so we'll use shorter names
    export_gdf = results_gdf.copy()
    export_gdf = export_gdf.rename(columns={
        'parcel_id': 'PARCEL_ID',
        'allowed_geometry': 'ALLOWED_GM',
        'prohibited_geometry': 'PROHIB_GM'
    })

    # Export to shapefile
    export_gdf.to_file(output_path)

    print(f"  Exported {len(export_gdf)} parcels to: {output_path}")
    print(f"  Shapefile includes: geometry, PARCEL_ID, ALLOWED_GM, PROHIB_GM")

    return output_path


def main():
    """Main entry point for the script."""
    print("=" * 60)
    print("ALEXANDRIA CHICKEN MAP GENERATOR")
    print("=" * 60)

    # Step 1: Read all data files
    land_use_df, boundary_gdf, parcels_gdf, buildings_gdf = read_data()

    # Step 2: Prepare data (standardize CRS, merge building use data)
    land_use_df, boundary_gdf, parcels_gdf, buildings_gdf = prepare_data(
        land_use_df, boundary_gdf, parcels_gdf, buildings_gdf
    )

    # Step 3: Identify residential parcels
    residential_parcels_gdf, non_residential_parcels_gdf = identify_residential_parcels(
        parcels_gdf, land_use_df
    )

    # Step 4: Identify dwelling buildings
    dwelling_buildings_gdf = identify_dwelling_buildings(buildings_gdf)

    # Step 5: Calculate allowed areas (core logic)
    results_gdf = calculate_allowed_areas(residential_parcels_gdf, dwelling_buildings_gdf)

    # Step 6: Create visualization layers
    boundary_layer, non_res_layer, prohibited_layer, allowed_layer = create_visualization_layers(
        boundary_gdf, residential_parcels_gdf, non_residential_parcels_gdf, results_gdf
    )

    # Step 7: Generate map outputs
    output_dir = Path(__file__).parent.parent / "output"

    # Generate map visualization
    fig = generate_map(boundary_layer, non_res_layer, prohibited_layer, allowed_layer, output_dir)

    # Export shapefile
    shapefile_path = output_dir / "chicken_zones.shp"
    export_shapefile(results_gdf, shapefile_path)

    print("\n" + "=" * 60)
    print("PROCESSING COMPLETE!")
    print("=" * 60)
    print(f"Output directory: {output_dir}")
    print("\nGenerated files:")
    print(f"  - {output_dir / 'chicken_map.png'}")
    print(f"  - {output_dir / 'chicken_map.svg'}")
    print(f"  - {output_dir / 'chicken_zones.shp'} (+ associated files)")
    print("=" * 60)


if __name__ == "__main__":
    main()
