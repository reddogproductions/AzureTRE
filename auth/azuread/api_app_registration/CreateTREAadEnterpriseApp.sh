#!/bin/bash

# Setup Script
set -eou pipefail

usage()
{
    echo "Usage: $(basename $BASH_SOURCE) -n <app-name> [-r <reply-url>] [-i <identifier-uri>]" 1>&2
    echo 1>&2
    echo 'For example:' 1>&2
    echo './CreateTREAadEnterpriseApp.sh -n TRE_App_Name -r https://internal.drelocal/callback' 1>&2
    echo '    or' 1>&2
    echo './CreateTREAadEnterpriseApp.sh -n TRE_App_Name -r https://internal.drelocal/callback -i api://internal.drelocal' 1>&2
    echo 1>&2
    exit 1
}

declare appName
declare replyUrl="https://internal.drelocal/callback"
declare identifierUrl=""
declare scriptDir
declare currentUserId
declare spId

# Initialize parameters specified from command line
while getopts ":n:r:i:" arg; do
  case "${arg}" in
    n)
      appName=${OPTARG}
    ;;
    # r)
    #   replyUrl=${OPTARG}
    # ;;
    i)
      identifierUrl=${OPTARG}
    ;;
  esac
done

if [[ -z "$appName" ]]; then
  echo "Please specify the TRE application name" 1>&2
  usage
fi

scriptDir=$(dirname "$BASH_SOURCE")
echo "Getting Current User"
currentUserId=$(az ad signed-in-user show --query 'objectId' -o tsv)

echo "Creating AD App"
newApp=$(az ad app create \
  --display-name "$appName" \
  --app-roles @"$scriptDir/appRoles.json" \
  --available-to-other-tenants false \
  --oauth2-allow-implicit-flow true \
  --optional-claims @"$scriptDir/optionalClaims.json" \
  --required-resource-accesses @"$scriptDir/requiredResourceAccesses.json" \
  --query "{objectId:objectId, appId:appId }" \
  --output json)

  # DELETE --reply-urls $replyUrl \

newAppId=$(echo "$newApp" | jq -r .appId)
newAppObjectId=$(echo "$newApp" | jq -r .objectId)

echo "New App Registration created or updated with id $newAppId and objectId $newAppObjectId"

# We need to disable the default scope ("user_impersonation") so that we can remove it.
scopes=$(az ad app show --id $newAppId -o json --query "oauth2Permissions[?value=='user_impersonation']")

if [[ $(echo "$scopes" | jq '. | length') -eq 1 ]]; then
  echo "Disabling default scope user_impersonation"
  scopes=$(echo "$scopes" | jq '.[0].isEnabled = false')
  az ad app update --id $newAppId --set oauth2Permissions="$scopes"
fi


# Update to set the identifier URI and the OAuth2 scopes.
echo "Creating scopes"
az ad app update --id $newAppId \
  --identifier-uris "api://${newAppId}" $identifierUrl \
  --set oauth2Permissions=@"$scriptDir/scopes.json"

# Set Access Token version
az rest --method PATCH --headers "Content-Type=application/json" --uri "https://graph.microsoft.com/v1.0/applications/${newAppObjectId}/" --body '{"api":{"requestedAccessTokenVersion": 2}}'
# Make the current user an owner of the application.
az ad app owner add --id $newAppId --owner-object-id $currentUserId

# See if a service principal already exists
spId=$(az ad sp list --filter "appId eq '$newAppId'" --query '[0].objectId' --output tsv)

# If not, create a new service principal
if [[ -z "$spId" ]]; then
    spId=$(az ad sp create --id $newAppId --query 'objectId' --output tsv)
    echo "New Service Principal created with id $spId"
fi

# This tag ensures the app is listed in the "Enterprise applications"
# DELETE az ad sp update --id $spId --set tags="['WindowsAzureActiveDirectoryIntegratedApp']"

# Grant admin consent on the required resource accesses (Graph API)
echo "Granting admin consent"
az ad app permission admin-consent --id $newAppId

echo "done"
