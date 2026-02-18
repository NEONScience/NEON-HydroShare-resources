#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Filename: neon_dp_hs_explore.py

Author: Zachary Nickerson
Date: 2026-02-18

Description: 
Each NEON site has a resource in CUAHSI HydroShare that provides site metadata,
geolocation information, and a downloadable list of all the hydrologic data 
products available for that site. This R script serves as a helper to explore
the list of hydrologic data saved in a NEON site resource in HydroShare. This
script will read in the JSON, present all the data products available for a
site, and give the user the opportunity to directly download a data product and
load it into Python for exploration.
"""

from hsclient import HydroShare
import json
import pandas as pd
import os
import neonutilities as nu

# Make dir for outputs
local_gh_dir = "C:/Users/nickerson/Documents/GitHub/NEON-HydroShare-resources/"
os.makedirs(local_gh_dir+"resource-metadata/output_jsons", exist_ok=True)

# Change directory to local Github directory
os.chdir(local_gh_dir+"resource-metadata/output_jsons")

# Set the domain and site you want to view
domain_id = "D01"
site_id = "HOPB"

# Set the HydroShare resource ID for this site
hs_id = "8c46db88647d46578337400d961965a6"

# Sign on to CUAHSI HydroShare
hs = HydroShare()
hs.sign_in()

# Retrieve resource from HydroShare
hs_resource = hs.resource(hs_id)

# Retrieve the JSON file from the resource
file_name = "NEON_"+domain_id+"_"+site_id+"_hydroDPs.json"
json_download = hs_resource.file_download(path = file_name,
                                          save_path="./")

# Load JSON data
with open(json_download, 'r') as f:
    hydro_dps = json.load(f)

# Convert to DataFrame for easier manipulation
# Extract the data products list and upstream data
data_dict = hydro_dps['data']
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

# Extract which release we are working with
# Handle releases as either a single value or a dictionary with 'release' key
current_release = hydro_dps_df['releases'][0][0]['release']

# Users can get more information about this site by visiting the DEIMS-SDR page
# (Dynamic Ecological Information Management System - Site and dataset registry)
print(f"DEIMS-SDR page for {domain_id} {site_id} - {hydro_dps_df['deimsId'].iloc[0]}")

# Now, user can explore the hydrologic data products available for this site
print(f"Hydrologic Data Products available for NEON site {domain_id} {site_id}")

# Print data products with their codes and titles
for code, title in zip(hydro_dps_df['dataProductCode'], 
                       hydro_dps_df['dataProductTitle']):
    print(f"{code} - {title}")

# Next, users can choose a data product to explore by row number in the DF

# Set row number
r = 0

# Get the ID and name of the data product to be explored
dp_code = hydro_dps_df['dataProductCode'].iloc[r]
dp_title = hydro_dps_df['dataProductTitle'].iloc[r]
dp_num_name = f"{dp_code} - {dp_title}"
print(f"Exploring: {dp_num_name}")

# Users can get more information about this data product by visiting the
# Data product landing page on the NEON data portal
neon_url = f"https://data.neonscience.org/data-products/{dp_code}/{current_release}"
print(f"URL for NEON Data Product: {dp_num_name} - {neon_url}")

# Print the availability of a specific data product by row number
available_months = hydro_dps_df['availableMonths'].iloc[r]
print(f"Months available for download for NEON Data Product: {dp_num_name}")
print(available_months)

# Download this data product from the NEON Data Portal
# By default, date ranges are commented out, so a user will get the full period
# of record for a data product. Users can set specific date ranges (YYYY-MM).
portal_download = nu.load_by_product(
    dpid=dp_code,
    site=site_id,
    release=current_release,
    # startdate="2023-10",
    # enddate="2024-09",
    token=os.environ.get("NEON_TOKEN"), # https://www.neonscience.org/resources/learning-hub/tutorials/neon-api-tokens-tutorial
    check_size=False
    )

# For more on how to explore NEON data downloads, see:
# https://www.neonscience.org/resources/learning-hub/tutorials/download-explore-neon-data#download-files-and-load-directly-to-r-loadbyproduct

# Please contact NEON if you have any questions about the data product:
# https://www.neonscience.org/about/contact-us

# End