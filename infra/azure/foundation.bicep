targetScope = 'subscription'

@allowed([
  'eastus2'
])
param location string = 'eastus2'

@allowed([
  'centralus'
  'westus3'
])
param postgresLocation string = 'centralus'

@description('Object ID of the current operator, not an email, client ID, or runtime identity.')
@minLength(36)
@maxLength(36)
param administratorObjectId string

@description('An isolated PostgreSQL Entra administrator role mapped by object ID.')
param administratorPrincipalName string = 'aql_migration_admin'

@description('Approved public IPv4 addresses, WITHOUT CIDR suffixes. Every rule is a single /32.')
@minLength(1)
param operatorIpv4Addresses string[]

@description('Observed, explicitly approved job egress IPv4s. Empty denies runtime DB access until measured.')
param environmentOutboundIpv4Addresses string[] = []

param createTestDatabase bool = false

@minValue(5)
@maxValue(1440)
param staleAfterMinutes int = 1440

var tags = {
  application: 'agentic-quant-lab'
  phase: '0'
  recording: 'manual-acceptance-only'
  managedBy: 'aql-bicep'
}

resource aql 'Microsoft.Resources/resourceGroups@2024-03-01' = {
  name: 'aql-phase0'
  location: location
  tags: tags
}

module resources 'modules/foundation-resources.bicep' = {
  name: 'aql-foundation-resources'
  scope: aql
  params: {
    location: location
    postgresLocation: postgresLocation
    administratorObjectId: administratorObjectId
    administratorPrincipalName: administratorPrincipalName
    approvedIpv4Addresses: union(operatorIpv4Addresses, environmentOutboundIpv4Addresses)
    createTestDatabase: createTestDatabase
    tags: tags
  }
}

// Only an AQL principal's AcrPull assignment is written in the shared resource group.
module registryAccess 'modules/registry-access.bicep' = {
  name: 'aql-registry-pull'
  scope: resourceGroup('RiskPulse')
  params: {
    runtimePrincipalId: resources.outputs.runtimePrincipalId
  }
}

module monitoring 'modules/monitoring.bicep' = {
  name: 'aql-monitoring'
  scope: aql
  params: {
    location: location
    staleAfterMinutes: staleAfterMinutes
    tags: tags
  }
}

output subscriptionId string = subscription().subscriptionId
output tenantId string = tenant().tenantId
output resourceGroupName string = aql.name
output location string = location
output postgresLocation string = postgresLocation
output postgresServerName string = resources.outputs.postgresServerName
output postgresServerId string = resources.outputs.postgresServerId
output postgresHost string = resources.outputs.postgresHost
output databaseName string = 'aql'
output testDatabaseName string = createTestDatabase ? 'aql_test' : ''
output administratorObjectId string = administratorObjectId
output administratorPrincipalName string = administratorPrincipalName
output storageAccountName string = resources.outputs.storageAccountName
output storageAccountId string = resources.outputs.storageAccountId
output storageAccountUrl string = resources.outputs.storageAccountUrl
output storageContainerName string = 'aql-audit-ledger'
output acceptanceContainerName string = createTestDatabase ? 'aql-audit-acceptance' : ''
output ledgerPrefix string = 'sec'
output runtimeIdentityId string = resources.outputs.runtimeIdentityId
output runtimeClientId string = resources.outputs.runtimeClientId
output runtimePrincipalId string = resources.outputs.runtimePrincipalId
output githubIdentityId string = resources.outputs.githubIdentityId
output githubClientId string = resources.outputs.githubClientId
output githubPrincipalId string = resources.outputs.githubPrincipalId
output githubFederatedSubject string = 'repo:BruceGK/agentic-quant-lab:environment:azure-production'
output registryId string = registryAccess.outputs.registryId
output registryLoginServer string = registryAccess.outputs.registryLoginServer
output jobName string = 'aql-recorder'
output actionGroupId string = monitoring.outputs.actionGroupId
output failureAlertId string = monitoring.outputs.failureAlertId
output missingSuccessAlertId string = monitoring.outputs.missingSuccessAlertId
output workspaceId string = monitoring.outputs.workspaceId
output workspaceCustomerId string = monitoring.outputs.workspaceCustomerId
output staleAfterMinutes int = staleAfterMinutes
output databaseUrl string = 'host=${resources.outputs.postgresHost} port=5432 dbname=aql user=aql_recorder sslmode=verify-full sslrootcert=/etc/ssl/certs/ca-certificates.crt'
