#!/bin/bash

# Setup Script
set -eou pipefail

usage()
{
    echo "Usage: $(basename $BASH_SOURCE) -n <app-name>" 1>&2
    echo 1>&2
    echo 'For example:' 1>&2
    echo './$(basename $BASH_SOURCE) -n TRE_App_Name' 1>&2
    echo 1>&2
    exit 1
}

declare appName
declare appId
declare spId

# Initialize parameters specified from command line
while getopts ":n:" arg; do
  case "${arg}" in
    n)
      appName=${OPTARG}
    ;;
  esac
done

if [[ -z "$appName" ]]; then
  echo "Please specify the TRE application name" 1>&2
  usage
fi

# Find the first app with matching display name.
appId=$(az ad app list --display-name "$appName" --query '[0].appId' -o tsv)
if [[ -z "$appId" ]]; then
  echo "Application '$appName' does not exist."
  exit 0
fi

# See if a service principal exists
spId=$(az ad sp list --filter "appId eq '$appId'" --query '[0].objectId' -o tsv)

# If so, delete it
if [[ -n "$spId" ]]; then
  az ad sp delete --id $spId
fi

# sp delete seems to delete the app registration as well, but just in case ...
appId=$(az ad app list --app-id "$appId" --query '[0].appId' -o tsv)
if [[ -n "$appId" ]]; then
  az ad app delete --id $appId
fi
