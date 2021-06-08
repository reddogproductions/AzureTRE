# Terraform Runner

## Build
```cmd
cd devops/runners/terraform
docker build -t tre-terraform-runner .  
```

## Apply
```
docker run -it \
    -e TEMPLATE_PATH=workspaces/vanilla/terraform \
    -e TEMPLATE_GIT_REF=develop \
    -e TF_VAR_workspace_id=0001 \
    -e TF_VAR_address_space=10.2.1.0/24 \
    -e TF_VAR_location=westeurope \
    -e TF_VAR_tre_id=__CHANGE_ME__ \
    -e ARM_TENANT_ID=__CHANGE_ME__ \
    -e ARM_SUBSCRIPTION_ID=__CHANGE_ME__ \
    -e ARM_CLIENT_ID=__CHANGE_ME__ \
    -e ARM_CLIENT_SECRET=__CHANGE_ME__ \
    -e TF_VAR_state_storage=__CHANGE_ME__ \
    -e TF_VAR_mgmt_res_group=__CHANGE_ME__ \
    -e TF_VAR_state_container=tfstate \
    tre-terraform-runner apply
```

## Destroy
```
docker run -it \
    -e TEMPLATE_PATH=workspaces/vanilla/terraform \
    -e TEMPLATE_GIT_REF=develop \
    -e TF_VAR_workspace_id=0001 \
    -e TF_VAR_address_space=10.2.1.0/24 \
    -e TF_VAR_location=westeurope \
    -e TF_VAR_tre_id=__CHANGE_ME__ \
    -e ARM_TENANT_ID=__CHANGE_ME__ \
    -e ARM_SUBSCRIPTION_ID=__CHANGE_ME__ \
    -e ARM_CLIENT_ID=__CHANGE_ME__ \
    -e ARM_CLIENT_SECRET=__CHANGE_ME__ \
    -e TF_VAR_state_storage=__CHANGE_ME__ \
    -e TF_VAR_mgmt_res_group=__CHANGE_ME__ \
    -e TF_VAR_state_container=tfstate \
    tre-terraform-runner destroy
```
```