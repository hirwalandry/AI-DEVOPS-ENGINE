import json
import stripe
from django.shortcuts import render
from django.views import View
from django.http import HttpResponseRedirect, JsonResponse, HttpResponse
from django.contrib import messages
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from .models import GitHubIntegration
from .auth_decorators import require_api_key
from django.utils.decorators import method_decorator
from django.core.serializers import serialize
from django.views.generic import ListView
from django.shortcuts import redirect
from .models import GitHubIntegration, RunAuditLog, DeveloperAPIKey, Deployment
from .emails import send_instant_usage_invoice_email
from .auth_decorators import require_api_key
from .tasks import execute_background_remediation_task, execute_deployment

stripe.api_key = settings.STRIPE_SECRET_KEY


class GitHubAppCallbackView(View):
    def get(self, request):
        installation_id = request.GET.get('installation_id')
        setup_action = request.GET.get('setup_action')

        if not installation_id:
            messages.error(request, "Security handshake aborted: Missing installation confirmation token.")
            return HttpResponseRedirect('/dashboard/error')

        user_org_name = request.user.username

        integration, created = GitHubIntegration.objects.update_or_create(
            organization_name=user_org_name,
            defaults={
                'installation_id': installation_id,
                'encrypted_access_token': "",
            },
        )

        messages.success(request, "Successfully integrated with organization workspace profiles.")
        return HttpResponseRedirect('/dashboard/')


class UserDashboardView(View):
    def get(self, request):
        integrations = GitHubIntegration.objects.all()
        return render(request, "dashboard.html", {"integrations": integrations})


class LogsStreamView(View):
    def get(self, request):
        tenant = getattr(request, "tenant", None)
        logs = RunAuditLog.objects.for_tenant(tenant).order_by('-created_at')[:50] if tenant else RunAuditLog.objects.all().order_by('-created_at')[:50]
        data = [
            {
                "project_id": log.project_id,
                "repository_name": log.repository_name,
                "target_language": log.target_language,
                "execution_status": log.execution_status,
                "execution_summary": log.execution_summary,
                "created_at": log.created_at.isoformat(),
            }
            for log in logs
        ]
        return JsonResponse(data, safe=False)


class LogDetailView(View):
    def get(self, request, project_id):
        log = RunAuditLog.objects.filter(project_id=project_id).first()
        if not log:
            return JsonResponse({"error": "No log found for this project"}, status=404)
        return JsonResponse({
            "project_id": log.project_id,
            "repository_name": log.repository_name,
            "target_language": log.target_language,
            "execution_status": log.execution_status,
            "execution_summary": log.execution_summary,
            "created_at": log.created_at.isoformat(),
        })


class CreateStripeCheckoutSessionView(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        org_name = request.user.username
        ENTERPRISE_PLAN_PRICE_ID = settings.STRIPE_ENTERPRISE_PRICE_ID

        try:
            checkout_session = stripe.checkout.Session.create(
                customer_email=request.user.email,
                payment_method_types=['card'],
                mode='subscription',
                line_items=[{'price': ENTERPRISE_PLAN_PRICE_ID, 'quantity': 1}],
                metadata={"organization_name": org_name},
                success_url=settings.STRIPE_SUCCESS_URL + "?session_id={CHECKOUT_SESSION_ID}",
                cancel_url=settings.STRIPE_CANCEL_URL,
            )
            return HttpResponseRedirect(checkout_session.url)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)


@method_decorator(csrf_exempt, name='dispatch')
class StripeWebhookListenerView(View):
    def post(self, request, *args, **kwargs):
        payload = request.body
        sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')

        try:
            event = stripe.Webhook.construct_event(
                payload, sig_header, settings.STRIPE_WEBHOOK_SIGNING_SECRET
            )
        except (ValueError, stripe.error.SignatureVerificationError):
            return HttpResponse(status=400)

        if event['type'] == 'checkout.session.completed':
            session = event['data']['object']
            org_name = session['metadata'].get('organization_name')
            print(f"[Billing] Subscription completed for {org_name}")

        elif event['type'] == 'customer.subscription.deleted':
            subscription = event['data']['object']
            print(f"[Billing] Subscription cancelled for customer {subscription.get('customer')}")

        return HttpResponse(status=200)


@method_decorator(csrf_exempt, name='dispatch')
class UsageMeteringWebhookView(View):
    def post(self, request, *args, **kwargs):
        auth_header = request.META.get('HTTP_AUTHORIZATION')
        if not auth_header or auth_header != "Bearer LocalSecretInternalTokenBetweenServices":
            return JsonResponse({"error": "Unauthorized internal service access."}, status=403)

        try:
            body = json.loads(request.body)
            project_id = body.get("project_id")
            org_name = body.get("organization_name")

            print(f"[Meter] Usage unit recorded: 1 bug fix for {org_name}, project {project_id}")

            User = get_user_model()
            try:
                user = User.objects.get(username=org_name)
                send_instant_usage_invoice_email(
                    user_email=user.email,
                    org_name=org_name,
                    project_id=project_id,
                )
            except User.DoesNotExist:
                print(f"[Meter] No user found for org {org_name} — skipping email notification.")

            return JsonResponse({"status": "METER_RECORDED", "project_id": project_id}, status=200)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)



@method_decorator(csrf_exempt, name='dispatch')
@method_decorator(require_api_key, name='dispatch')
class CLIEngineTriggerGatewayView(View):
    def post(self, request, *args, **kwargs):
        try:
            body = json.loads(request.body)
            project_id = body.get("project_id")
            target_language = body.get("target_language")
            bug_description = body.get("bug_description")
            buggy_file_content = body.get("buggy_file_content")

            if not all([project_id, target_language, bug_description, buggy_file_content]):
                return JsonResponse({"error": "Malformed payload structure: Missing parameters."}, status=400)

            integration = GitHubIntegration.objects.filter(
                organization_name=request.organization_name
            ).first()
            installation_id = str(integration.installation_id) if integration else "cli_context_direct"

            execute_background_remediation_task.delay(
                project_id=project_id,
                installation_id=installation_id,
                repository_full_name=f"{request.organization_name}/cli-workspace",
                pull_request_number=0,
                clone_url="local_stream",
                bug_description=bug_description,
                buggy_file_content=buggy_file_content,
                target_language=target_language,
                base_branch="main",
                target_file_path="",
                latest_commit_sha="",
            )

            return JsonResponse({
                "status": "QUEUED_FROM_CLI",
                "message": f"Remediation thread [{project_id}] successfully scheduled for sandbox execution.",
            }, status=202)

        except Exception as e:
            return JsonResponse({"error": f"Internal pipeline gateway error: {str(e)}"}, status=500)


class APIKeyDashboardListView(LoginRequiredMixin, ListView):
    model = DeveloperAPIKey
    template_name = "api_key_management.html"
    context_object_name = "api_keys"

    def get_queryset(self):
        org_name = self.request.user.username
        return DeveloperAPIKey.objects.filter(organization_name=org_name).order_by("-created_at")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        raw_key = self.request.session.pop("LAST_GENERATED_RAW_KEY", None)
        if raw_key:
            context["raw_key_display"] = raw_key
        return context


class GenerateNewAPIKeyView(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        org_name = request.user.username

        existing_keys_count = DeveloperAPIKey.objects.filter(organization_name=org_name, is_active=True).count()
        if existing_keys_count >= 5:
            messages.error(request, "Security threshold reached: You cannot maintain more than 5 active API keys simultaneously.")
            return redirect("api_key_dashboard")

        raw_token, key_instance = DeveloperAPIKey.generate_key_for_org(org_name)

        request.session["LAST_GENERATED_RAW_KEY"] = raw_token

        messages.success(request, "New cryptographic API key token successfully initialized.")
        return redirect("api_key_dashboard")


class RevokeAPIKeyView(LoginRequiredMixin, View):
    def post(self, request, key_id, *args, **kwargs):
        org_name = request.user.username

        try:
            key_record = DeveloperAPIKey.objects.get(id=key_id, organization_name=org_name)
            key_record.is_active = False
            key_record.save()
            messages.warning(request, f"API credential token with prefix {key_record.prefix} has been revoked.")
        except DeveloperAPIKey.DoesNotExist:
            messages.error(request, "Requested key context allocation not found.")

        return redirect("api_key_dashboard")


class DeploymentListView(View):
    def get(self, request):
        tenant = getattr(request, "tenant", None)
        deployments = Deployment.objects.for_tenant(tenant).order_by('-created_at')[:100] if tenant else Deployment.objects.all().order_by('-created_at')[:100]
        data = [
            {
                "id": d.id,
                "repository_name": d.repository_name,
                "commit_sha": d.commit_sha,
                "branch": d.branch,
                "status": d.status,
                "strategy": d.strategy,
                "target_url": d.target_url,
                "logs": d.logs,
                "triggered_by": d.triggered_by,
                "created_at": d.created_at.isoformat(),
                "deployed_at": d.deployed_at.isoformat() if d.deployed_at else None,
            }
            for d in deployments
        ]
        return JsonResponse(data, safe=False)


class DeploymentDetailView(View):
    def get(self, request, deployment_id):
        tenant = getattr(request, "tenant", None)
        dep = Deployment.objects.for_tenant(tenant).filter(id=deployment_id).first() if tenant else Deployment.objects.filter(id=deployment_id).first()
        if not dep:
            return JsonResponse({"error": "Deployment not found"}, status=404)
        return JsonResponse({
            "id": dep.id,
            "organization_name": dep.organization_name,
            "repository_name": dep.repository_name,
            "commit_sha": dep.commit_sha,
            "branch": dep.branch,
            "status": dep.status,
            "strategy": dep.strategy,
            "target_url": dep.target_url,
            "logs": dep.logs,
            "triggered_by": dep.triggered_by,
            "created_at": dep.created_at.isoformat(),
            "deployed_at": dep.deployed_at.isoformat() if dep.deployed_at else None,
        })


@method_decorator(csrf_exempt, name='dispatch')
class TriggerDeploymentView(View):
    def post(self, request, *args, **kwargs):
        try:
            body = json.loads(request.body)
            repository_full_name = body.get("repository_full_name")
            commit_sha = body.get("commit_sha")
            branch = body.get("branch", "main")
            strategy = body.get("strategy", "docker")

            if not all([repository_full_name, commit_sha]):
                return JsonResponse({"error": "Missing required fields: repository_full_name, commit_sha"}, status=400)

            org_name = getattr(request, "tenant", None) or request.user.username
            integration = GitHubIntegration.objects.filter(organization_name=org_name).first()
            installation_id = str(integration.installation_id) if integration else "cli_context_direct"

            execute_deployment.delay(
                organization_name=org_name,
                installation_id=installation_id,
                repository_full_name=repository_full_name,
                commit_sha=commit_sha,
                branch=branch,
                strategy=strategy,
            )

            return JsonResponse({
                "status": "DEPLOY_QUEUED",
                "message": f"Deployment of {repository_full_name} @ {commit_sha[:7]} queued.",
            }, status=202)

        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)
