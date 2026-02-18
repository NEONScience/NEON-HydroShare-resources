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
# from datetime import datetime
from hsclient import HydroShare
from hsmodels.schemas.fields import PointCoverage
# from hsmodels.schemas.fields import PeriodCoverage
from hsmodels.schemas.fields import AwardInfo
from hsmodels.schemas.fields import Creator

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
# ZN -- need to get this information from someone at NEON

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
siteProducts["data"]["dataProducts"] = [
    dp for dp in siteProducts["data"].get("dataProducts", [])
    if isinstance(dp, dict) and dp.get("dataProductCode") in hydroSet
]

# Load this data as content to the resource
outputPath = "./NEON_"+domainID+"_"+siteID+"_hydroDPs.json"
with open(outputPath, "w") as f:
    json.dump(siteProducts, f, indent=4)
hopb_resource.file_upload(outputPath)

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

#


