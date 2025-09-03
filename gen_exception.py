import sys
import urllib3

from kubernetes import config
from kubernetes.dynamic.exceptions import NotFoundError
from openshift.dynamic import DynamicClient

urllib3.disable_warnings()
k8s_client = config.new_client_from_config()
dynClient = DynamicClient(k8s_client)

policyNames = [
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
    "mas-require-drop-all-capabilities",
    "mas-require-ro-rootfs",
    "mas-require-run-as-nonroot",

    # Additional Policies
    "ford-require-high-availability",
    "ford-require-pdb",
    "ford-require-reasonable-pdbs",
    "ford-require-replicas-allow-disruption",
    "ford-validate-hpa-minreplicas",
]


clusterPolicies = dynClient.resources.get(
    api_version="kyverno.io/v1", kind="ClusterPolicy"
)

failures = {}
for policyName in policyNames:
    try:
        policy = clusterPolicies.get(name=policyName)
    except NotFoundError as e:
        print(f"Policy is not installed: {e}", file=sys.stderr)

    policyReports = dynClient.resources.get(
        api_version="wgpolicyk8s.io/v1alpha2", kind="PolicyReport"
    )
    reports = policyReports.get(namespace="redhat-marketplace")
    for report in reports.items:
        resourceId = f"{report.scope.kind}:{report.scope.namespace}/{report.scope.name}"
        for result in report.results:
            if result.policy == policyName and result.result == "fail":
                if policyName not in failures:
                    failures[policyName] = []
                if result.rule not in failures[policyName]:
                    failures[policyName].append(result.rule)
                    print(f"{policyName} {result.rule} failed ({resourceId})")
