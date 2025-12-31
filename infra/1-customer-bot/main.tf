terraform {
  required_version = ">= 1.1.0"
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = ">= 3.0.0"
    }
  }
}

provider "azurerm" {
  features {}
}

# Data sources - read resources created in the foundation layer
data "azurerm_resource_group" "rg" {
  name = var.resource_group_name
}

data "azurerm_service_plan" "plan" {
  name                = var.service_plan_name
  resource_group_name = data.azurerm_resource_group.rg.name
}

data "azurerm_container_registry" "acr" {
  name                = var.acr_name
  resource_group_name = data.azurerm_resource_group.rg.name
}

resource "azurerm_linux_web_app" "bot" {
  name                = var.app_name
  location            = data.azurerm_resource_group.rg.location
  resource_group_name = data.azurerm_resource_group.rg.name
  service_plan_id     = data.azurerm_service_plan.plan.id

  identity {
    type = "SystemAssigned"
  }

  site_config {
    application_stack {
      docker_image_name = "${var.docker_image}"
      docker_registry_url = "https://${data.azurerm_container_registry.acr.login_server}"
      docker_registry_username = data.azurerm_container_registry.acr.admin_username
      docker_registry_password = data.azurerm_container_registry.acr.admin_password
    }
  }

  app_settings = merge(
    var.app_settings,
    {
      "WEBSITES_ENABLE_APP_SERVICE_STORAGE" = "false"
      "SCM_DO_BUILD_DURING_DEPLOYMENT"      = "false"
      "BASE_WEBHOOK_URL" = "https://${var.app_name}.azurewebsites.net"
    }
  )
}