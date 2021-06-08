#!/bin/sh

git init
git remote add tre https://github.com/microsoft/AzureTRE.git
git fetch tre
git checkout tre/$TEMPLATE_GIT_REF -- $TEMPLATE_PATH

cd /repo/$TEMPLATE_PATH

terraform init -input=false -backend=true -reconfigure \
    -backend-config="resource_group_name=$TF_VAR_mgmt_res_group" \
    -backend-config="storage_account_name=$TF_VAR_state_storage" \
    -backend-config="container_name=$TF_VAR_state_container" \
    -backend-config="key=$TF_VAR_tre_id$TF_VAR_workspace_id"

terraform $@ -auto-approve