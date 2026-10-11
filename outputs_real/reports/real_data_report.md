# Real-data analysis - Pune administrative wards

Generated 2026-10-11T23:27:43. Unit: 14 analysis units from the 15 PMC administrative wards (2017 boundaries, OpenCity KML); Kondhwa-Wanavdi is merged into Bibwewadi because the 2011 census office "Bibvewadi" contains the Kondhva wards.

## Data actually used

- **Population, Households, Children_Pct, SC_Pct, ST_Pct, Literacy_Rate**: Census of India 2011, PMC ward-wise tables (OpenCity)
- **Area_sqkm, Center_Latitude/Longitude**: computed from the PMC administrative ward polygons
- **PM2_5, PM10, NO2**: IITM / MPCB station readings 2024-25 (OpenCity), daily means with QC, interpolated to ward centroids by inverse-distance weighting (power 2)
- **AQI**: CPCB sub-index method on daily PM2.5, PM10 and NO2 (max sub-index), averaged over days
- **Schools, Hospitals, Banks, Shopping_Malls, Markets, Bus_Stops, Parks_Count**: OpenStreetMap point counts inside each ward (Overpass API)
- **Road_Length_km, Road_Network_Density**: OpenStreetMap highway lengths clipped to each ward

### Proxies (not measurements)

- **Congestion_Index**: NOT measured congestion. Population per km of OSM road, min-max scaled to 0-100 across the analysis units.
- **Green_Cover_Percentage**: Share of ward area covered by OSM parks, gardens, forest, grass, scrub and meadow polygons. Depends on OSM completeness; not satellite NDVI.
- **Open_Spaces_sqkm**: Same OSM green polygons, in km2.

### Not available

Average_Income, Peak_Hour_Volume, Average_Speed_kmh, Noise_Level_dB, SO2 (sensor values implausible), Water_Supply_Hours, Electricity_Reliability_Pct, Tree counts

## Clustering (K-Means, k = 3)

- Silhouette by k: k=2: 0.384, k=3: 0.287, k=4: 0.255, k=5: 0.283, k=6: 0.246, k=7: 0.197, k=8: 0.125
- PCA: 4 components explain 93.5% of variance
- Stability over 30 re-seeded runs (adjusted Rand index vs. seed 42): mean 1.0, min 1.0

| Group | Wards | n | Pop. density | Pollution load | Congestion proxy | Green % | Mean stress z |
|---|---|---|---|---|---|---|---|
| Highest-stress group (cluster 2) | Kasba-Vishrambaugwada, Bhavani Peth | 2 | 57400 | 177 | 77 | 1.0 | 1.64 |
| Intermediate group (cluster 0) | Ghole Road, Warje-Karve Nagar, Dhole Patil Road, Yerawada-Sangamwadi, Nagar Road, Bibwewadi-Kondhwa, Hadapsar | 7 | 11704 | 164 | 12 | 7.0 | -0.04 |
| Lowest-stress group (cluster 1) | Aundh, Kothrud-Karve Road, Tilak Road, Sahakarnagar, Dhankawadi | 5 | 17227 | 141 | 21 | 19.3 | -0.6 |

## Highest composite stress (z-score mean of density, pollution load, congestion proxy, low green)

1. Bhavani Peth (1.99, cluster 2)
2. Kasba-Vishrambaugwada (1.29, cluster 2)
3. Hadapsar (0.37, cluster 0)
4. Ghole Road (0.22, cluster 0)
5. Sahakarnagar (0.07, cluster 1)

## Correlations (n = 14)

| Pair | Pearson r | p | Spearman rho | p |
|---|---|---|---|---|
| Congestion_Index vs PM2_5 | 0.356 | 0.2109 | 0.315 | 0.2727 |
| Congestion_Index vs AQI | 0.303 | 0.2918 | 0.323 | 0.2593 |
| Population_Density_Calc vs Pollution_Load_Index_Calc | 0.331 | 0.247 | 0.143 | 0.6257 |
| Green_Cover_Percentage vs Pollution_Load_Index_Calc | -0.558 | 0.0382 | -0.568 | 0.0342 |

## Limitations

- Only 7 air-quality stations; most wards receive interpolated, not measured, values.
- Station coordinates come from geocoding the station's locality name and are approximate.
- Census is 2011 while air quality is 2024-25 and boundaries are 2017; population density therefore mixes years.
- Aundh and Bibwewadi-Kondhwa include areas merged into PMC after 2011, so their 2011-based density is understated.
- Fourteen units is a small sample for clustering.
- 2011 census ward offices and 2017 administrative wards share names but not exact boundaries; apart from the Bibwewadi/Kondhwa merge, densities are approximate.
- The congestion proxy is derived from population and road length, so its correlation with population density is partly built in.
- Correlations on a small number of neighbouring wards are affected by spatial autocorrelation and are indicative only.