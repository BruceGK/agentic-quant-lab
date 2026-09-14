targetScope = 'resourceGroup'

@description('Existing AQL foundation outputs; do not supply any RiskPulse data resources.')
param postgresServerName string
param storageAccountName string

@allowed([
  'centralus'
  'westus3'
])
param location string = 'centralus'

@description('riskpulseacr12345.azurecr.io/aql-recorder@sha256:<digest>, or a verified locked git-<40hex> tag.')
param imageRef string

@minLength(40)
@maxLength(40)
param recorderGitSha string

@description('Explicit ISO date for acceptance catch-up. Never inferred from wall-clock deployment time.')
param catchupStart string

param universeCiks string = '320193'
param ingestCiks string = universeCiks

@description('Enable only after the GitHub azure-production environment is reviewer/main-branch protected.')
param githubRunnerEnabled bool = false

@secure()
@description('Optional genuine SEC contact. Empty means recording MUST fail until configured. Never a build argument.')
param secUserAgent string = ''

@allowed([
  1800
  3600
])
param replicaTimeout int = 1800

resource managedEnvironment 'Microsoft.App/managedEnvironments@2025-01-01' existing = {
  name: 'aql-recorder-env'
}

resource registry 'Microsoft.ContainerRegistry/registries@2023-07-01' existing = {
  scope: resourceGroup('RiskPulse')
  name: 'riskpulseacr12345'
}

resource runtime 'Microsoft.ManagedIdentity/userAssignedIdentities@2023-01-31' existing = {
  name: 'aql-recorder-runtime'
}

resource github 'Microsoft.ManagedIdentity/userAssignedIdentities@2023-01-31' existing = {
  name: 'aql-github'
}

resource postgres 'Microsoft.DBforPostgreSQL/flexibleServers@2024-08-01' existing = {
  name: postgresServerName
}

resource storage 'Microsoft.Storage/storageAccounts@2023-05-01' existing = {
  name: storageAccountName
}

var databaseUrl = 'host=${postgres.properties.fullyQualifiedDomainName} port=5432 dbname=aql user=aql_recorder sslmode=verify-full sslrootcert=/etc/ssl/certs/ca-certificates.crt'
var tags = {
  application: 'agentic-quant-lab'
  phase: '0'
  recording: 'manual-acceptance-only'
  managedBy: 'aql-bicep'
}

resource job 'Microsoft.App/jobs@2025-01-01' = {
  name: 'aql-recorder'
  location: location
  tags: tags
  identity: {
    type: 'UserAssigned'
    userAssignedIdentities: {
      '${runtime.id}': {}
    }
  }
  properties: {
    environmentId: managedEnvironment.id
    workloadProfileName: 'Consumption'
    configuration: {
      triggerType: 'Manual'
      replicaRetryLimit: 0
      replicaTimeout: replicaTimeout
      manualTriggerConfig: {
        parallelism: 1
        replicaCompletionCount: 1
      }
      registries: [
        {
          server: registry.properties.loginServer
          identity: runtime.id
        }
      ]
      secrets: empty(secUserAgent) ? [] : [
        {
          name: 'sec-user-agent'
          value: secUserAgent
        }
      ]
    }
    template: {
      containers: [
        {
          name: 'recorder'
          image: imageRef
          args: [
            'record'
          ]
          resources: {
            cpu: json('0.5')
            memory: '1Gi'
          }
          env: concat([
            {
              name: 'LEDGER_BACKEND'
              value: 'azure'
            }
            {
              name: 'AZURE_STORAGE_ACCOUNT_URL'
              value: 'https://${storage.name}.blob.${environment().suffixes.storage}'
            }
            {
              name: 'AZURE_STORAGE_CONTAINER'
              value: 'aql-audit-ledger'
            }
            {
              name: 'AZURE_LEDGER_PREFIX'
              value: 'sec'
            }
            {
              name: 'DATABASE_AUTH'
              value: 'azure'
            }
            {
              name: 'DATABASE_URL'
              value: databaseUrl
            }
            {
              name: 'AZURE_CLIENT_ID'
              value: runtime.properties.clientId
            }
            {
              name: 'AZURE_SUBSCRIPTION_ID'
              value: subscription().subscriptionId
            }
            {
              name: 'UNIVERSE_CIKS'
              value: universeCiks
            }
            {
              name: 'INGEST_CIKS'
              value: ingestCiks
            }
            {
              name: 'CATCHUP_START'
              value: catchupStart
            }
            {
              name: 'RECORDER_GIT_SHA'
              value: recorderGitSha
            }
            {
              name: 'RECORDER_RUN_MODE'
              value: 'acceptance'
            }
          ], empty(secUserAgent) ? [] : [
            {
              name: 'SEC_USER_AGENT'
              secretRef: 'sec-user-agent'
            }
          ])
        }
      ]
    }
  }
}

resource jobRunnerRole 'Microsoft.Authorization/roleDefinitions@2022-04-01' = {
  name: guid(resourceGroup().id, 'aql-manual-job-runner')
  properties: {
    roleName: 'AQL manual job runner (${uniqueString(resourceGroup().id)})'
    description: 'Read/start AQL job and read executions only. No job writes, secrets, ACR, Blob, database, role assignments, or deployments.'
    type: 'CustomRole'
    assignableScopes: [
      resourceGroup().id
    ]
    permissions: [
      {
        actions: [
          'Microsoft.App/jobs/read'
          'Microsoft.App/jobs/start/action'
          'Microsoft.App/jobs/executions/read'
          'Microsoft.App/jobs/execution/read'
        ]
        notActions: []
        dataActions: []
        notDataActions: []
      }
    ]
  }
}

resource githubRunner 'Microsoft.Authorization/roleAssignments@2022-04-01' = if (githubRunnerEnabled) {
  name: guid(job.id, github.id, jobRunnerRole.id)
  scope: job
  properties: {
    principalId: github.properties.principalId
    principalType: 'ServicePrincipal'
    roleDefinitionId: jobRunnerRole.id
  }
}

output subscriptionId string = subscription().subscriptionId
output resourceGroupName string = resourceGroup().name
output jobName string = job.name
output jobId string = job.id
output environmentId string = managedEnvironment.id
output imageRef string = imageRef
output recorderGitSha string = recorderGitSha
output databaseUrl string = databaseUrl
output storageAccountUrl string = 'https://${storage.name}.blob.${environment().suffixes.storage}'
output runtimeClientId string = runtime.properties.clientId
output githubClientId string = github.properties.clientId
output githubPrincipalId string = github.properties.principalId
output githubRunnerEnabled bool = githubRunnerEnabled
output githubRoleAssignmentId string = extensionResourceId(job.id, 'Microsoft.Authorization/roleAssignments', guid(job.id, github.id, jobRunnerRole.id))
