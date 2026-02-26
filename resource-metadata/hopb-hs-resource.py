#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Filename: hopb-hs-resource.py

Author: Zachary Nickerson
Date: 2026-02-18

Description: 
Script to create or edit the D01-HOPB NEON site resource in CUAHSI HydroShare
"""

import os
import requests
import json
import pandas as pd
from hsclient import HydroShare
from hsmodels.schemas.fields import PointCoverage
from hsmodels.schemas.fields import AwardInfo
from hsmodels.schemas.fields import Creator
from hsmodels.schemas.fields import Rights

# Make dir for outputs
local_gh_dir = "C:/Users/nickerson/Documents/GitHub/NEON-HydroShare-resources/"
os.makedirs(local_gh_dir+"resource-metadata/output_jsons", exist_ok=True)

# Change directory to local Github directory
os.chdir(local_gh_dir+"resource-metadata/output_jsons")

# What is the most recent release?
currentRelease = "RELEASE-2026"

# Set NEON site metadata
domainID = "D01"
siteID = "HOPB"
siteName = "Lower Hop Brook"
siteLocation = "Franklin County, MA, USA"
siteLat = 42.471941
siteLon = -72.329526

# Sign on to CUAHSI HydroShare
hs = HydroShare()
hs.sign_in()

# Create the new, empty resource - only need to do once
# hopb_resource = hs.create()

# Retrieve resource already created
hopb_resource = hs.resource("8c46db88647d46578337400d961965a6")

# Get the HydroShare identifier for the resource
res_identifier = hopb_resource.resource_id
print(f'The HydroShare Identifier for your resource is: {res_identifier}')

# Construct a hyperlink to access the HydroShare landing page for the resource
print(f'Your resource is available at: {hopb_resource.metadata.url}')

### GENERATE RESOURCE METADATA ###

# Set the Title for the resource
siteText = siteName+" ("+domainID+"-"+siteID+", "+siteLocation+")"
titleName = "NEON Hydrologic Data Products at "+siteText
hopb_resource.metadata.title = titleName

# Set the Abstract text for the resource
hopb_resource.metadata.abstract = (
    'This resource provides information on the hydrologic data products '
    'offered by the National Ecological Observatory Network (NEON) at the '
    +siteText+
    ' site. Users can find details on all hydrologic data products published '
    'from observational, instrumented, or remote sensing methods across air, '
    'land, and water. No NEON data are stored in this resource, but users can '
    'use direct links and code resources to be quickly directed to data '
    'products of interest.'
    '\n\n'
    'For more information on the site, please visit: '
    'https://www.neonscience.org/field-sites/'+siteID+
    '\n\n'
    'The subject keywords for this resource identify the hydrologic data '
    'products published from this site. Each of these data products is '
    'available for download, for free, from the NEON Data Portal '
    '(https://data.neonscience.org/data-products/explore). '
    'One file in the content of this resource is a JSON file listing each '
    'hydrologic data product published at this site, the availability of the '
    'data by year-month as of the most recent data release, and the URLs for '
    'each year-month download package. The other file in the content is a '
    'README text file that directs users to a Github repository containing '
    'code resources in R and Python that allow users to parse the JSON into '
    'a more user friendly environment to explore and download the available '
    'data products.'
    '\n\n'
    'If you have questions about this resource or would like to chat with a '
    'NEON scientist about one or more of these data products, please follow '
    'this link to get in contact with us: '
    'https://www.neonscience.org/about/contact-us'
)

# Set spatial and temporal coverage
hopb_resource.metadata.spatial_coverage = PointCoverage(
    name=siteLocation,
    north=siteLat,
    east=siteLon,
    projection='WGS 84 EPSG:4326',
    type='point',
    units='Decimal degrees')

# Set award information
newAwardInfo = AwardInfo(funding_agency_name='National Science Foundation',
                         title=('NEON Operations and Maintenance: ' 
                                'Evolving from a Strong Foundation'),
                         number='BIO 2217817',
                         funding_agency_url='https://www.nsf.gov/awardsearch/show-award?AWD_ID=2217817')
hopb_resource.metadata.awards.append(newAwardInfo)

# Instantiate a new Creator object for a Creator that is an organization
newCreator = Creator(organization='National Ecological Observatory Network',
                     address='1685 38th St., Suite 100',
                     homepage='https://www.neonscience.org/about/contact-us')
hopb_resource.metadata.creators.append(newCreator)
# Make NEON only creator (only needs to be run once when resource is created)
# del hopb_resource.metadata.creators[0]

# Set License statement
# Set the rights statement and the URL that points to its description
hopb_resource.metadata.rights.statement = (
    'This resource is shared under the Creative Commons '
    'Creative Commons CC0 1.0 “No Rights Reserved”'
)
hopb_resource.metadata.rights.url = 'https://www.neonscience.org/usage-policies'

# Call the save function to save the metadata edits to HydroShare
hopb_resource.save()

### QUERY AND ORGANIZE NEON HYDROLOGY DATA PRODUCTS ###

# Query all ecohydrology data products in most recent release
catalogURL = 'https://data.neonscience.org/api/v0/products?release='+currentRelease
responseCatalog = requests.get(catalogURL,
                               headers={"X-API-TOKEN": os.environ.get("NEON_TOKEN"),
                                        "accept": "application/json"},)
catalog = responseCatalog.json()
listKey = "data"
# Subset to DPIDs within the 'Ecohydrology' theme
hydroProducts = [
    rec for rec in catalog.get(listKey, [])
    if isinstance(rec.get("themes"), list) and "Ecohydrology" in rec["themes"]
]
hydroDPIDs = [rec["productCode"] for rec in hydroProducts]
hydroSet = set(hydroDPIDs)

# Query the NEON API for all the available data products for a site and release
siteURL = 'https://data.neonscience.org/api/v0/releases/'+currentRelease+'/sites/'+siteID
responseSite = requests.get(
    siteURL,
    headers={"X-API-TOKEN": os.environ.get("NEON_TOKEN"),
             "accept": "application/json"},)
siteProducts = responseSite.json()

# Subset down to only the 'Ecohydrology' data products
# Produce the JSON to write out to resource
siteProducts["data"]["dataProducts"] = [
    dp for dp in siteProducts["data"].get("dataProducts", [])
    if isinstance(dp, dict) and dp.get("dataProductCode") in hydroSet
]

# Covert JSON to data frame to write out to resource
data_dict = siteProducts['data']
data_products = data_dict['dataProducts']

# Get upstream data (everything except dataProducts)
upstream_data = {k: v for k, v in data_dict.items() if k != 'dataProducts'}

# Create list of dictionaries where each data product is merged with upstream data
rows = []
for product in data_products:
    # Merge upstream data with each data product
    row = {**upstream_data, **product}
    rows.append(row)

# Convert to DataFrame
hydro_dps_df = pd.DataFrame(rows)

### LOAD THE HYDROLOGIC DATA PRODUCT CATALOG (JSON) TO THE RESOURCE ###

# Load this data as content to the resource
outputPathJSON = "./NEON_"+domainID+"_"+siteID+"_hydroDPs.json"
with open(outputPathJSON, "w") as f:
    json.dump(siteProducts, f, indent=4)
hopb_resource.file_upload(outputPathJSON)

### LOAD THE AVAILABLE DATA PRODUCTS AS A DATA FRAME TO THE RESOURCE ###

# Load this data as content to the resource
outputPathCSV = "./NEON_"+domainID+"_"+siteID+"_hydroDPs.csv"
hydro_dps_df.to_csv(outputPathCSV, index=False) 
hopb_resource.file_upload(outputPathCSV)

# Update metadata descriptions for each column in the csv
agg = hopb_resource.aggregation(type="CSV")
table = agg.metadata.tableSchema.table
table.columns[0].description = "Abbreviated four-letter site code for a NEON site"
table.columns[1].description = "Full name for NEON site"
table.columns[2].description = "Full name for NEON site"
table.columns[3].description = "Type of NEON site: either CORE (more pristine) or GRADIENT (more impacted)"
table.columns[4].description = "Decimal Latitude - in degrees"
table.columns[5].description = "Decimal Longitude - in degrees"
table.columns[6].description = "Abbreviated United States state or territory name"
table.columns[7].description = "Full United States state or territory name"
table.columns[8].description = "Three digit code for the NEON Ecoclimate Domain of the site"
table.columns[9].description = "Name for the NEON Ecoclimatic Domain of the site"
table.columns[10].description = "URL to the site webpage in the Dynamic Ecological Information Management System"
table.columns[11].description = "Information (name, generation date, URL) on the most recent NEON Data Release for this site and data product"
table.columns[12].description = "Standard NEON Data Product ID for this hydrologic data product"
table.columns[13].description = "NEON Data Product name for this hydrology data product"
table.columns[14].description = "Each site-month available for this site and data product for the most recent NEON Data Release"
table.columns[15].description = "URLs to the download package for each site-month available for this site and data product for the most recent NEON Data Release"
table.columns[16].description = "Each site-month available for this site and data product for the most recent NEON Data Release"
agg.save()

### LOAD THE HELPER SCRIPT README TO THE RESOURCE ###

# The readme file will be the same for each resource
# take it from the GitHub subdirectory and load it to the resource
hopb_resource.file_upload(
    local_gh_dir+"resource-metadata/README.md"
    )

### ADD KEYWORDS TO RESOURCE SPECIFIC TO THE DATA PRODUCTS ###

# The keywords will be all the available data products
DPNames = [
    dp["dataProductTitle"]
    for dp in siteProducts["data"]["dataProducts"]
    if "dataProductTitle" in dp
]

# Write out the keyword list
hopb_resource.metadata.subjects = DPNames

# Call the save function to save the metadata edits to HydroShare
hopb_resource.save()

# End