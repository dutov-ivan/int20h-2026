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

resource "azurerm_role_assignment" "acr_pull" {
  scope                = data.azurerm_container_registry.acr.id
  role_definition_name = "AcrPull"
  principal_id         = azurerm_linux_web_app.bot.identity[0].principal_id
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
    }
  }

  app_settings = merge(
    var.app_settings,
    {
      "WEBSITES_ENABLE_APP_SERVICE_STORAGE" = "false"
      "SCM_DO_BUILD_DURING_DEPLOYMENT"      = "false"
      "BASE_WEBHOOK_URL" = "https://${var.app_name}.azurewebsites.net"
      BOT_TOKEN            = var.BOT_TOKEN 
      FORUM_GROUP_ID       = var.FORUM_GROUP_ID
      DATABASE_URL         = var.DATABASE_URL
      WEBHOOK_SECRET_TOKEN = var.WEBHOOK_SECRET_TOKEN
      ENVIRONMENT          = var.ENVIRONMENT
      WEBSITES_PORT        = var.WEBSITES_PORT
    }
  )

}