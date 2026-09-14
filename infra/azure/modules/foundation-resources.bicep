param location string
param postgresLocation string
param administratorObjectId string
param administratorPrincipalName string
param approvedIpv4Addresses string[]
param createTestDatabase bool
param tags object

var suffix = uniqueString(subscription().subscriptionId, resourceGroup().id, 'aql-phase0')

resource runtime 'Microsoft.ManagedIdentity/userAssignedIdentities@2023-01-31' = {
  name: 'aql-recorder-runtime'
  location: location
  tags: tags
}

resource github 'Microsoft.ManagedIdentity/userAssignedIdentities@2023-01-31' = {
  name: 'aql-github'
  location: location
  tags: tags
}

resource federation 'Microsoft.ManagedIdentity/userAssignedIdentities/federatedIdentityCredentials@2023-01-31' = {
  parent: github
  name: 'github-azure-production'
  properties: {
    issuer: 'https://token.actions.githubusercontent.com'
    subject: 'repo:BruceGK/agentic-quant-lab:environment:azure-production'
    audiences: [
      'api://AzureADTokenExchange'
    ]
  }
}

resource storage 'Microsoft.Storage/storageAccounts@2023-05-01' = {
  name: 'aql${suffix}'
  location: location
  kind: 'StorageV2'
  sku: {
    name: 'Standard_LRS'
  }
  tags: tags
  properties: {
    accessTier: 'Hot'
    allowBlobPublicAccess: false
    allowSharedKeyAccess: false
    defaultToOAuthAuthentication: true
    minimumTlsVersion: 'TLS1_2'
    supportsHttpsTrafficOnly: true
    publicNetworkAccess: 'Enabled'
    // Private data, public TLS endpoint: the existing Consumption environment has no VNet.
    networkAcls: {
      bypass: 'None'
      defaultAction: 'Allow'
    }
    encryption: {
      keySource: 'Microsoft.Storage'
      services: {
        blob: {
          enabled: true
          keyType: 'Account'
        }
        file: {
          enabled: true
          keyType: 'Account'
        }
      }
    }
  }
}

resource blobs 'Microsoft.Storage/storageAccounts/blobServices@2023-05-01' = {
  parent: storage
  name: 'default'
  properties: {
    isVersioningEnabled: true
    deleteRetentionPolicy: {
      enabled: true
      days: 14
    }
    containerDeleteRetentionPolicy: {
      enabled: true
      days: 14
    }
  }
}

resource ledger 'Microsoft.Storage/storageAccounts/blobServices/containers@2023-05-01' = {
  parent: blobs
  name: 'aql-audit-ledger'
  properties: {
    publicAccess: 'None'
  }
}

resource acceptanceLedger 'Microsoft.Storage/storageAccounts/blobServices/containers@2023-05-01' = if (createTestDatabase) {
  parent: blobs
  name: 'aql-audit-acceptance'
  properties: {
    publicAccess: 'None'
  }
}

resource operatorLedgerReader 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(ledger.id, administratorObjectId, 'reader')
  scope: ledger
  properties: {
    principalId: administratorObjectId
    principalType: 'User'
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', '2a2b9908-6ea1-4ae2-8e65-a410df84e7d1')
  }
}

resource operatorAcceptanceWriter 'Microsoft.Authorization/roleAssignments@2022-04-01' = if (createTestDatabase) {
  name: guid(acceptanceLedger!.id, administratorObjectId, 'acceptance-contributor')
  scope: acceptanceLedger
  properties: {
    principalId: administratorObjectId
    principalType: 'User'
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', 'ba92f5b4-2d11-453d-a403-e96b0029c9fe')
  }
}

resource ledgerWriterRole 'Microsoft.Authorization/roleDefinitions@2022-04-01' = {
  name: guid(resourceGroup().id, 'aql-ledger-read-write-no-delete')
  properties: {
    roleName: 'AQL ledger read-write without delete (${suffix})'
    description: 'AQL only. Read/write block blobs; no delete, keys, ACL changes, or delegation keys. Blob write is NOT WORM.'
    type: 'CustomRole'
    assignableScopes: [
      resourceGroup().id
    ]
    permissions: [
      {
        actions: [
          'Microsoft.Storage/storageAccounts/blobServices/containers/read'
        ]
        notActions: []
        dataActions: [
          'Microsoft.Storage/storageAccounts/blobServices/containers/blobs/read'
          'Microsoft.Storage/storageAccounts/blobServices/containers/blobs/write'
        ]
        notDataActions: []
      }
    ]
  }
}

resource ledgerWriter 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(ledger.id, runtime.id, ledgerWriterRole.id)
  scope: ledger
  properties: {
    principalId: runtime.properties.principalId
    principalType: 'ServicePrincipal'
    roleDefinitionId: ledgerWriterRole.id
  }
}

resource postgres 'Microsoft.DBforPostgreSQL/flexibleServers@2024-08-01' = {
  name: 'aql-pg-${suffix}'
  location: postgresLocation
  tags: tags
  sku: {
    name: 'Standard_B1ms'
    tier: 'Burstable'
  }
  properties: {
    version: '16'
    authConfig: {
      activeDirectoryAuth: 'Enabled'
      passwordAuth: 'Disabled'
      tenantId: tenant().tenantId
    }
    storage: {
      storageSizeGB: 32
      autoGrow: 'Disabled'
    }
    backup: {
      backupRetentionDays: 7
      geoRedundantBackup: 'Disabled'
    }
    highAvailability: {
      mode: 'Disabled'
    }
    network: {
      publicNetworkAccess: 'Enabled'
    }
  }
}

resource administrator 'Microsoft.DBforPostgreSQL/flexibleServers/administrators@2024-08-01' = {
  parent: postgres
  name: administratorObjectId
  properties: {
    principalName: administratorPrincipalName
    principalType: 'User'
    tenantId: tenant().tenantId
  }
  // Firewall updates temporarily make the server unavailable to Entra principal operations.
  dependsOn: [
    firewall
  ]
}

resource firewall 'Microsoft.DBforPostgreSQL/flexibleServers/firewallRules@2024-08-01' = [
  for ip in approvedIpv4Addresses: {
    parent: postgres
    name: 'aql-${replace(ip, '.', '-')}'
    properties: {
      startIpAddress: ip
      endIpAddress: ip
    }
  }
]

resource database 'Microsoft.DBforPostgreSQL/flexibleServers/databases@2024-08-01' = {
  parent: postgres
  name: 'aql'
  properties: {
    charset: 'UTF8'
    collation: 'en_US.utf8'
  }
  dependsOn: [
    administrator
  ]
}

resource testDatabase 'Microsoft.DBforPostgreSQL/flexibleServers/databases@2024-08-01' = if (createTestDatabase) {
  parent: postgres
  name: 'aql_test'
  properties: {
    charset: 'UTF8'
    collation: 'en_US.utf8'
  }
  dependsOn: [
    administrator
  ]
}

output postgresServerName string = postgres.name
output postgresServerId string = postgres.id
output postgresHost string = postgres.properties.fullyQualifiedDomainName
output storageAccountName string = storage.name
output storageAccountId string = storage.id
output storageAccountUrl string = 'https://${storage.name}.blob.${environment().suffixes.storage}'
output runtimeIdentityId string = runtime.id
output runtimeClientId string = runtime.properties.clientId
output runtimePrincipalId string = runtime.properties.principalId
output githubIdentityId string = github.id
output githubClientId string = github.properties.clientId
output githubPrincipalId string = github.properties.principalId
