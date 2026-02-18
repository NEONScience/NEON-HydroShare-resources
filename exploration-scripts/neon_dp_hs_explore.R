##############################################################################################
#' @title EXPLORE NEON DATA PRODUCTS FROM HYDROSHARE RESOURCE DOWNLOAD

#' @author
#' Zachary Nickerson \email{nickerson@battelleecology.org} \cr

#' @description Each NEON site has a resource in CUAHSI HydroShare that provides
#' site metadata, geolocation information, and a downloadable list of all the 
#' hydrologic data products available for that site. This R script serves as a 
#' helper to explore the list of hydrologic data saved in a NEON site resource 
#' in HydroShare. Users must first download the JSON file in the content of the 
#' resource. This script will read in the JSON, present all the data products 
#' available for a site, and give the user the opportunity to directly 
#' download a data product and load it into R for exploration.

#' @return Information about the data products available for a site, plus the 
#' ability to get specific information and download data for a specific data
#' product at a site

# changelog and author contributions / copyrights
#   Zachary Nickerson (2026-02-18)
#     original creation
##############################################################################################

# Load libraries
library(jsonlite)
library(neonUtilities)

# Set the domain and site you want to view
domainID <- "D01"
siteID <- "HOPB"

# Unlike python, R currently does not contain a client package to access 
# HydroShare resources. To run this R script, users must download the JSON file
# from a NEON site resource in HydroShare and load the JSON into R.

# Set path to downloaded json file 
# If downloaded as a compressed file, must extract the file first
fileName <- paste("NEON",
                  domainID,
                  siteID,
                  "hydroDPs.json",
                  sep = "_")
hydroDPs <- jsonlite::fromJSON(
  paste0("C:/Users/nickerson/Downloads/5a84c3c2-2d1f-40ae-b5ff-21d286b5347f/",
         fileName)
  )
hydroDPs_df <- as.data.frame(hydroDPs)

# Extract which relese we are working with
currentRelease <- unique(hydroDPs_df$data.releases.release)

# Users can get more information about this site by visiting the DEIMS-SDR page
# (Dynamic Ecological Information Management System - Site and dataset registry)
print(paste("DEIMS-SDR page for",
            domainID,siteID,"-",
            unique(hydroDPs_df$data.deimsId)))

# Now, user can explore the hydrologic data products available for this site
print(paste("Hydrologic Data Products available for NEON site",
            domainID,
            siteID))
print(paste(hydroDPs_df$data.dataProducts.dataProductCode,
            hydroDPs_df$data.dataProducts.dataProductTitle,
            sep = " - "))

# Next, users can choose a data product to explore by row number in the DF

# Set row number
r=1

# Get the ID and name of the data product to be explored
DP_num_name <- paste(hydroDPs_df$data.dataProducts.dataProductCode[r],
                     hydroDPs_df$data.dataProducts.dataProductTitle[r],
                     sep = " - ")
print(paste("Exploring:",DP_num_name))

# Users can get more information about this data product by visiting the
# Data product landing page on the NEON data portal
print(paste0("URL for NEON Data Product: ",DP_num_name," - ",
            "https://data.neonscience.org/data-products/",
            hydroDPs_df$data.dataProducts.dataProductCode[r],"/",
            currentRelease))

# Print the availability of a specific data product by row number
print(paste("Months available for download for NEON Data Product:",
            DP_num_name))
print(hydroDPs_df$data.dataProducts.availableMonths[r])

# Download this data product from the NEON Data Portal
# By default, date ranges are commented out, so a user will get the full period
# of record for a data product. Users can set specific date ranges (YYYY-MM).
# See help file for loadByProduct() to details on inputs
portalDownload <- neonUtilities::loadByProduct(
  dpID = hydroDPs_df$data.dataProducts.dataProductCode[r],
  site = siteID,
  release = currentRelease,
  package = "expanded",
  # startdate = "2023-10",
  # enddate = "2024-09",
  token = Sys.getenv("NEON_TOKEN"),# https://www.neonscience.org/resources/learning-hub/tutorials/neon-api-tokens-tutorial
  check.size = F,
)

# For more on how to explore NEON data downloads via loadByProduct(), see:
# https://www.neonscience.org/resources/learning-hub/tutorials/download-explore-neon-data#download-files-and-load-directly-to-r-loadbyproduct

# Please contact NEON if you have any questions about the data product:
# https://www.neonscience.org/about/contact-us

# End 