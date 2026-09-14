param location string
param staleAfterMinutes int
param tags object

resource workspace 'Microsoft.OperationalInsights/workspaces@2023-09-01' existing = {
  scope: resourceGroup('RiskPulse')
  name: 'workspaceriskpulsebaaf'
}

var source = replace(loadTextContent('../queries/job-logs.kql'), '__JOB_NAME__', 'aql-recorder')
var failureQuery = '${source}\n${loadTextContent('../queries/failure.kql')}'
var missingQuery = '${source}\n${replace(loadTextContent('../queries/missing-success.kql'), '__STALE_MINUTES__', string(staleAfterMinutes))}'

resource receiver 'Microsoft.Insights/actionGroups@2023-01-01' = {
  name: 'aql-phase0-owners'
  location: 'global'
  tags: tags
  properties: {
    groupShortName: 'AQL phase0'
    enabled: true
    armRoleReceivers: [
      {
        name: 'subscription-owner'
        roleId: '8e3af657-a8ff-443c-a75c-2fe8c4bcb635'
        useCommonAlertSchema: true
      }
    ]
  }
}

resource failure 'Microsoft.Insights/scheduledQueryRules@2023-12-01' = {
  name: 'aql-recorder-failure'
  location: location
  kind: 'LogAlert'
  tags: tags
  properties: {
    displayName: 'AQL recorder failed'
    description: 'An AQL CLI failure or AQL job platform failure. Manual alert acceptance is labelled, not an ingestion heartbeat.'
    enabled: true
    severity: 2
    evaluationFrequency: 'PT5M'
    windowSize: 'PT5M'
    overrideQueryTimeRange: 'PT15M'
    scopes: [
      workspace.id
    ]
    skipQueryValidation: false
    autoMitigate: true
    criteria: {
      allOf: [
        {
          query: failureQuery
          metricMeasureColumn: 'Failures'
          timeAggregation: 'Maximum'
          operator: 'GreaterThan'
          threshold: 0
          failingPeriods: {
            numberOfEvaluationPeriods: 1
            minFailingPeriodsToAlert: 1
          }
        }
      ]
    }
    actions: {
      actionGroups: [
        receiver.id
      ]
      customProperties: {
        application: 'agentic-quant-lab'
        phase: '0'
        signal: 'failure'
      }
    }
  }
}

resource missing 'Microsoft.Insights/scheduledQueryRules@2023-12-01' = {
  name: 'aql-recorder-missing-success'
  location: location
  kind: 'LogAlert'
  tags: tags
  properties: {
    displayName: 'AQL missing verified ingestion'
    description: 'No remotely verified and reconciled Azure record/catch-up completion within ${staleAfterMinutes} minutes, including never/no rows. Expected while recording remains manual.'
    enabled: true
    severity: 2
    evaluationFrequency: 'PT5M'
    windowSize: 'PT5M'
    overrideQueryTimeRange: 'P2D'
    scopes: [
      workspace.id
    ]
    skipQueryValidation: false
    autoMitigate: true
    criteria: {
      allOf: [
        {
          query: missingQuery
          metricMeasureColumn: 'MissingSuccess'
          timeAggregation: 'Maximum'
          operator: 'GreaterThan'
          threshold: 0
          failingPeriods: {
            numberOfEvaluationPeriods: 1
            minFailingPeriodsToAlert: 1
          }
        }
      ]
    }
    actions: {
      actionGroups: [
        receiver.id
      ]
      customProperties: {
        application: 'agentic-quant-lab'
        phase: '0'
        signal: 'no-verified-ingestion'
      }
    }
  }
}

output actionGroupId string = receiver.id
output failureAlertId string = failure.id
output missingSuccessAlertId string = missing.id
output workspaceId string = workspace.id
output workspaceCustomerId string = workspace.properties.customerId
