provider "azurerm" {
  features {}
}

resource "azurerm_resource_group" "rg" {
    name = "rg-customer-bot-${terraform.workspace}"
    location = var.location
}

resource "azurerm_service_plan" "plan" {
    name = "plan-bot-${terraform.workspace}"
    resource_group_name = azurerm_resource_group.rg.name
    location = azurerm_resource_group.rg.location
    os_type = "Linux"

    sku_name = var.app_service_sku
}

resource "azurerm_linux_web_app" "app" {
  name = "app-customer-bot-${terraform.workspace}-${var.random_suffix}"
  resource_group_name = azurerm_resource_group.rg.name
  location = azurerm_service_plan.plan.location
  service_plan_id = azurerm_service_plan.plan.id
  site_config {
    application_stack {
      python_version = "3.12"
    }
  }

  app_settings = {
    # Networking
    "WEBSITES_PORT" = "8443"
    "BASE_WEBHOOK_URL" = "https://app-customer-bot-${terraform.workspace}-${var.random_suffix}.azurewebsites.net"


    # Database
    "DATABASE_URL" = var.database_url

    # Secrets
    "BOT_TOKEN" = var.customer_service_bot_api_key
    "FORUM_GROUP_ID" = tostring(var.customer_service_forum_id)
    "WEBHOOK_SECRET_TOKEN" = var.customer_service_webhook_secret_token

    # Environment
    "ENVIRONMENT" = var.environment
  }
}
