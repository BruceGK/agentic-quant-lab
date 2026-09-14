targetScope = 'subscription'

@description('First day of the budget creation month in UTC; retain this date on redeployment.')
param startDate string

@minValue(1)
param monthlyBudget int = 65

resource actionGroup 'Microsoft.Insights/actionGroups@2023-01-01' existing = {
  scope: resourceGroup('aql-phase0')
  name: 'aql-phase0-owners'
}

resource budget 'Microsoft.Consumption/budgets@2024-08-01' = {
  name: 'aql-phase0-costs'
  properties: {
    category: 'Cost'
    amount: monthlyBudget
    timeGrain: 'Monthly'
    timePeriod: {
      startDate: startDate
    }
    filter: {
      dimensions: {
        name: 'ResourceGroupName'
        operator: 'In'
        values: [
          'aql-phase0'
          'aql-phase0-managed'
        ]
      }
    }
    notifications: {
      actual80: {
        enabled: true
        operator: 'GreaterThanOrEqualTo'
        threshold: 80
        thresholdType: 'Actual'
        contactEmails: []
        contactGroups: [
          actionGroup.id
        ]
      }
      forecast100: {
        enabled: true
        operator: 'GreaterThanOrEqualTo'
        threshold: 100
        thresholdType: 'Forecasted'
        contactEmails: []
        contactGroups: [
          actionGroup.id
        ]
      }
    }
  }
}

output subscriptionId string = subscription().subscriptionId
output budgetName string = budget.name
output monthlyBudget int = monthlyBudget
