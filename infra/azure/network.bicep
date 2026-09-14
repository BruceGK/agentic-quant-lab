targetScope = 'resourceGroup'

@allowed([
  'centralus'
  'westus3'
])
param location string = 'centralus'
param postgresServerName string

var tags = {
  application: 'agentic-quant-lab'
  phase: '0'
  recording: 'manual-acceptance-only'
  managedBy: 'aql-bicep'
}

resource postgres 'Microsoft.DBforPostgreSQL/flexibleServers@2024-08-01' existing = {
  name: postgresServerName
}

resource workspace 'Microsoft.OperationalInsights/workspaces@2023-09-01' existing = {
  scope: resourceGroup('RiskPulse')
  name: 'workspaceriskpulsebaaf'
}

resource vnet 'Microsoft.Network/virtualNetworks@2024-05-01' = {
  name: 'aql-recorder-vnet'
  location: location
  tags: tags
  properties: {
    addressSpace: {
      addressPrefixes: [
        '10.86.0.0/24'
      ]
    }
    subnets: [
      {
        name: 'jobs'
        properties: {
          addressPrefix: '10.86.0.0/26'
          delegations: [
            {
              name: 'container-apps'
              properties: {
                serviceName: 'Microsoft.App/environments'
              }
            }
          ]
        }
      }
      {
        name: 'private-endpoints'
        properties: {
          addressPrefix: '10.86.0.64/28'
          privateEndpointNetworkPolicies: 'Disabled'
        }
      }
    ]
  }
}

resource zone 'Microsoft.Network/privateDnsZones@2024-06-01' = {
  name: 'privatelink.postgres.database.azure.com'
  location: 'global'
  tags: tags
}

resource dnsLink 'Microsoft.Network/privateDnsZones/virtualNetworkLinks@2024-06-01' = {
  parent: zone
  name: 'aql-recorder-vnet'
  location: 'global'
  properties: {
    registrationEnabled: false
    virtualNetwork: {
      id: vnet.id
    }
  }
}

resource endpoint 'Microsoft.Network/privateEndpoints@2024-05-01' = {
  name: 'aql-postgres-private'
  location: location
  tags: tags
  properties: {
    subnet: {
      id: '${vnet.id}/subnets/private-endpoints'
    }
    privateLinkServiceConnections: [
      {
        name: 'aql-postgres'
        properties: {
          privateLinkServiceId: postgres.id
          groupIds: [
            'postgresqlServer'
          ]
        }
      }
    ]
  }
}

resource dnsGroup 'Microsoft.Network/privateEndpoints/privateDnsZoneGroups@2024-05-01' = {
  parent: endpoint
  name: 'default'
  properties: {
    privateDnsZoneConfigs: [
      {
        name: 'postgres'
        properties: {
          privateDnsZoneId: zone.id
        }
      }
    ]
  }
}

resource environment 'Microsoft.App/managedEnvironments@2025-07-01' = {
  name: 'aql-recorder-env'
  location: location
  tags: tags
  properties: {
    infrastructureResourceGroup: 'aql-phase0-managed'
    vnetConfiguration: {
      infrastructureSubnetId: '${vnet.id}/subnets/jobs'
      internal: true
    }
    workloadProfiles: [
      {
        name: 'Consumption'
        workloadProfileType: 'Consumption'
      }
    ]
    appLogsConfiguration: {
      destination: 'azure-monitor'
    }
  }
}

resource logs 'Microsoft.Insights/diagnosticSettings@2021-05-01-preview' = {
  scope: environment
  name: 'aql-workspace'
  properties: {
    workspaceId: workspace.id
    logAnalyticsDestinationType: 'Dedicated'
    logs: [
      {
        category: 'ContainerAppConsoleLogs'
        enabled: true
      }
      {
        category: 'ContainerAppSystemLogs'
        enabled: true
      }
    ]
  }
}

output subscriptionId string = subscription().subscriptionId
output resourceGroupName string = resourceGroup().name
output location string = location
output environmentId string = environment.id
output environmentName string = environment.name
output infrastructureResourceGroup string = environment.properties.infrastructureResourceGroup
output vnetId string = vnet.id
output privateEndpointId string = endpoint.id
output privateDnsZoneId string = zone.id
output workspaceId string = workspace.id
