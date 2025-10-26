# Alexandria Chicken Map Generator - Technical Specification

## Overview
Generate a map showing where backyard chickens are legally allowed in Alexandria, VA, based on the city ordinance that chickens cannot be kept within 200 feet of any residence or dwelling not occupied by the land owner.

## Data Inputs

1. `data/land_use_codes.csv` - Zoning codes
2. `data/boundary/Boundary.shp` - City boundary
3. `data/parcels/Alexandria_Parcels.shp` - Parcel boundaries
4. `data/buildings/Buildings.shp` - Building footprints
5. `data/buildings-use.csv` - Building use classification (links via FACILITYID)

## Processing Pipeline

### Function 1: `prepare_data(land_use_df, boundary_gdf, parcels_gdf, buildings_gdf)`

- Ensure all GeoDataFrames use the same CRS (standardize to Alexandria's projection)
- Validate that all datasets have required fields
- Returns: (land_use_df, boundary_gdf, parcels_gdf, buildings_gdf) with standardized CRS

### Function 2: `identify_residential_parcels(parcels_gdf, land_use_df)`

- Join parcels with land use codes
- Filter to only residential zoning codes
- Residential zoning codes all start with the letter "R". E.g., R1, RB, etc.
- Return: residential_parcels_gdf, non_residential_parcels_gdf

### Function 3: `identify_dwelling_buildings(buildings_gdf, buildings_use_csv_path)`

- Load buildings-use.csv
- Join buildings with use data via FACILITYID
- Filter where USE == "Household"
- Return: dwelling_buildings_gdf (only residential buildings)

### Function 4: `calculate_allowed_areas(residential_parcels_gdf, dwelling_buildings_gdf)`

- Spatial join: dwellings → parcels (to know which dwelling is on which parcel)
- For each residential parcel:
  - Get all dwelling buildings NOT on this parcel
  - Create 200-foot buffer around each external dwelling
  - Union all external dwelling buffers
  - Subtract buffer union from parcel geometry
  - Result = allowed area (may be empty geometry)
- Return: GeoDataFrame with columns:
  - `parcel_id`: Original parcel identifier
  - `geometry`: Full parcel geometry
  - `allowed_geometry`: Area where chickens are allowed (MultiPolygon or Polygon, may be empty)
  - `prohibited_geometry`: Area where chickens are prohibited (difference of geometry and allowed_geometry)

### Function 5: `create_visualization_layers(boundary_gdf, residential_parcels_gdf, non_residential_parcels_gdf, results_gdf)`

- Create 4 separate GeoDataFrames for visualization:
  1. **Boundary layer**: City outline (no fill, black border)
  2. **Non-residential layer**: Non-residential parcels (light gray fill)
  3. **Prohibited residential layer**: Prohibited areas from results_gdf (dark gray fill)
  4. **Allowed residential layer**: Allowed areas from results_gdf (bright green fill)
- Return: (boundary_layer, non_res_layer, prohibited_layer, allowed_layer)

### Function 6: `generate_map(boundary_layer, non_res_layer, prohibited_layer, allowed_layer, output_dir)`

- Create matplotlib figure with appropriate size
- Plot layers in order (bottom to top):
  1. Non-residential (light gray)
  2. Prohibited residential (dark gray)
  3. Allowed residential (bright green)
  4. Boundary outline (black)
- Add title: "Alexandria, VA: Backyard Chicken Zoning"
- Add legend
- Remove axis ticks/labels for clean map
- Save as PNG and SVG to output_dir
- Return: figure object

### Function 7: `export_shapefile(results_gdf, output_path)`

- Export the complete results GeoDataFrame as shapefile
- Include all geometries and attributes
- Return: output path

## Data Flow

```
read_data()
    ↓
prepare_data()
    ↓
├─→ identify_residential_parcels()
│       ↓
│   (residential_parcels_gdf, non_residential_parcels_gdf)
│
└─→ identify_dwelling_buildings()
        ↓
    (dwelling_buildings_gdf)
        ↓
calculate_allowed_areas(residential_parcels_gdf, dwelling_buildings_gdf)
        ↓
    (results_gdf with allowed/prohibited areas)
        ↓
create_visualization_layers(boundary, residential, non_residential, results)
        ↓
    (4 layer GeoDataFrames)
        ↓
├─→ generate_map() → PNG + SVG
└─→ export_shapefile() → SHP
```

## Output Files

1. `output/chicken_zones.shp` (+ .shx, .dbf, .prj, etc.) - Complete shapefile with all data
2. `output/chicken_map.png` - Static map image
3. `output/chicken_map.svg` - Vector map graphic

## Color Scheme

- **Boundary outline**: Black, 2pt line
- **Non-residential parcels**: #CCCCCC (light gray)
- **Prohibited residential areas**: #666666 (dark gray)
- **Allowed residential areas**: #00FF00 or #4CAF50 (bright green)

## Key Implementation Notes

1. Use `geopandas.sjoin()` for spatial joins
2. Use `.buffer(200, cap_style=1)` for 200-foot buffers (200 feet, square caps)
3. Use `.unary_union` to combine multiple buffer geometries
4. Use `.difference()` to subtract buffers from parcels
5. Handle empty geometries gracefully (parcels with no allowed area)
6. Ensure CRS is in a projected coordinate system (feet) for accurate 200-foot buffers

## Legal Requirements

Based on Alexandria city ordinance:
- Chickens CAN be kept within 200 feet of the owner's own dwelling
- Chickens CANNOT be kept within 200 feet of other people's dwellings
- A dwelling is defined as a building with one or more rooms used for living or sleeping purposes
- Buildings are classified as dwellings if their USE field in buildings-use.csv is "Household"
