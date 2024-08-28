# WorldWideHydraulicModel
Collection of python scripts that use gdal and the hydrosheds dataset to generate Tuflow hydraulic models anywhere in the world

Quick and dirty script for getting a model set-up and off the ground for anywhere in the world with no study area data whatsoever [except the freely availble hydrosheds dataset for DTM and freely availble TRMM Data for rainfall]
Requires 
* Hydrosheds v1 downlaoded (https://www.hydrosheds.org/). the exact files required are stated in the Hydrosheds folder- warnign this is a big dataset
* TRMM data pre-processed to AMAX Grids - a few of these are provided as an example (https://disc.gsfc.nasa.gov/datasets/TRMM_3B42_Daily_7/summary) TRMM data can be replaced with any AMAX grid from any dataset in the same naming format as shown

The scripts are very, very draft
To run, amend the file "WWM_GetStudyArea.py" with the lat/long of the point area of interest. the scripts will find the catchment via hydrosheds, clip out the right area, generate a Tuflow model and develop some extremely crude hydrology.

Upstream catchments are represented by an inflow. The catchment with the study point is represented by rainfall runoff

Currently does not account for routing, so estiamtes are far out for anything with more than one upstream catchment....and likley quite a long way out for even single upstream cactchments as catchment size is far in excess of what the SCS approach was ever designed for. 

