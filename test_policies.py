import logging
import pytest

from kubernetes import config
from openshift.dynamic import DynamicClient

logger = logging.getLogger()

k8s_client = config.new_client_from_config()
dynClient = DynamicClient(k8s_client)

@pytest.mark.parametrize("policyName", [
    # Other
    "mas-disallow-pod-template-hash",
    "mas-disallow-service-external-ips",
    "mas-require-image-digest",
    "mas-require-pod-probes",
    "mas-require-pod-probes-unique",
    "mas-require-pod-requests-limits",
    "mas-require-storageclass",
    # RBAC
    "mas-disallow-role-with-wildcards",
    # Scheduling
    "mas-disallow-master-infra-tolerations",
    "mas-disallow-node-selection",
    "mas-require-topologyspreadconstraints",
    # Security Context
    "mas-disallow-privilege-escalation",
    "mas-disallow-run-as-root-user",
    "mas-disallow-sysctls",
    "mas-require-drop-all",
    "mas-require-ro-rootfs",
    "mas-require-run-as-nonroot",
])

def testPolicies(policyName):
    policyReports = dynClient.resources.get(
        api_version="wgpolicyk8s.io/v1alpha2", kind="PolicyReport"
    )
    reports = policyReports.get()
    failures = []
    for report in reports.items:
        resourceId = f"{report.scope.kind}:{report.scope.namespace}/{report.scope.name}"
        for result in report.results:
            if result.policy == policyName:
                if result.result == "fail":
                    failures.append(resourceId)
                break

    assert len(failures) == 0, f"One or more resources failed to comply with Kyverno policy '{policyName}': {failures}"
