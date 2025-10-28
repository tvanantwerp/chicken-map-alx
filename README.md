# Where can you legally keep backyard chickens in Alexandria, VA?

The [Alexandria city ordinance](https://library.municode.com/va/alexandria/codes/code_of_ordinances?nodeId=PTIITHCOGEOR_TIT5TRENSE_CH7ANFO_ARTAGEPR_S5-7-2KEFO) says:

> **Sec. 5-7-2 - Keeping fowl.**
>
> It shall be unlawful for any person to keep or allow to be kept within the city, within 200 feet of any residence or dwelling not occupied by such person, any fowl. The word "fowl," as used in this section, shall include, but is not limited to, chickens, hens, roosters, ducks, geese, pigeons or any domesticated barnyard bird. (Code 1963, Sec. 4-2)

This repository attempts to map exactly where you can and can't have backyard chickens according to the local law.

## GIS data sources

Data used to create this map was downloaded from the [City of Alexandria, VA GIS Open Data Hub](https://cityofalexandria-alexgis.opendata.arcgis.com/) on October 26th, 2025. The following data sets were used:

- [Buildings data](https://cityofalexandria-alexgis.opendata.arcgis.com/datasets/aec4d1c6ee894e1b821ff39d30bdfc30_0/explore) from which to draw 200 foot boundaries
- [Buildings use data](https://cityofalexandria-alexgis.opendata.arcgis.com/datasets/8ecb044012bf47f0959fee76e9cc559b_0/explore) to know what kind of buildings I was looking at
- [Parcel data](https://cityofalexandria-alexgis.opendata.arcgis.com/datasets/ab8f3a147ddc47deb6d82c5afda65708_0/explore) to know what land is available
- [Land use codes](https://cityofalexandria-alexgis.opendata.arcgis.com/datasets/122a2b6d20ea4e1ba8bb831e932ffa56_0/explore) to know how the land is zoned