from django.urls import path
from .views import (
    GitHubAppCallbackView,
    UserDashboardView,
    LogsStreamView,
    CreateStripeCheckoutSessionView,
    StripeWebhookListenerView,
    UsageMeteringWebhookView,
    CLIEngineTriggerGatewayView,
    APIKeyDashboardListView,
    GenerateNewAPIKeyView,
    RevokeAPIKeyView,
    DeploymentListView,
    DeploymentDetailView,
    TriggerDeploymentView,
)

urlpatterns = [
    path('auth/github/callback/', GitHubAppCallbackView.as_view(), name='github_callback'),
    path('dashboard/', UserDashboardView.as_view(), name='user_dashboard'),
    path('api/v1/logs-stream/', LogsStreamView.as_view(), name='logs_stream'),
    path('billing/create-checkout-session/', CreateStripeCheckoutSessionView.as_view(), name='stripe_checkout'),
    path('api/v1/billing/stripe-webhook/', StripeWebhookListenerView.as_view(), name='stripe_webhook_ingress'),
    path('api/v1/meter-event/', UsageMeteringWebhookView.as_view(), name='internal_telemetry_meter'),
    path('api/v1/cli/trigger-fix', CLIEngineTriggerGatewayView.as_view(), name='cli_gateway_endpoint'),
    path('dashboard/developer-tokens/', APIKeyDashboardListView.as_view(), name='api_key_dashboard'),
    path('dashboard/developer-tokens/generate/', GenerateNewAPIKeyView.as_view(), name='generate_key'),
    path('dashboard/developer-tokens/revoke/<int:key_id>/', RevokeAPIKeyView.as_view(), name='revoke_key'),
    path('api/v1/deployments/', DeploymentListView.as_view(), name='deployment_list'),
    path('api/v1/deployments/<int:deployment_id>/', DeploymentDetailView.as_view(), name='deployment_detail'),
    path('api/v1/deployments/trigger/', TriggerDeploymentView.as_view(), name='trigger_deployment'),
]
