import logging
import pytest
import urllib3

from kubernetes import config
from kubernetes.dynamic.exceptions import NotFoundError
from openshift.dynamic import DynamicClient

logger = logging.getLogger()

urllib3.disable_warnings()

k8s_client = config.new_client_from_config()
dynClient = DynamicClient(k8s_client)

def get_policy_names():
    """
    Dynamically discover all Kyverno policies in the cluster.
    Returns a list of policy names.
    """
    clusterPolicies = dynClient.resources.get(api_version="kyverno.io/v1", kind="ClusterPolicy")
    policies = clusterPolicies.get()
    policyNames = [policy.metadata.name for policy in policies.items]
    return policyNames

@pytest.mark.parametrize("policyName", get_policy_names())
def testPolicies(policyName):
    policyReports = dynClient.resources.get(
        api_version="wgpolicyk8s.io/v1alpha2", kind="PolicyReport"
    )
    reports = policyReports.get(namespace=None)
    failures = []
    policyMatchCount = 0
    for report in reports.items:
        resourceId = f"{report.scope.kind}:{report.scope.namespace}/{report.scope.name}"
        logger.debug(f"Processing report {report.metadata.name} for {resourceId}")
        for result in report.results:
            if result.policy == policyName:
                logger.debug(f" - Processing result {result.policy}/{result.rule} {result.result}")
                policyMatchCount += 1
                if result.result == "fail":
                    failures.append(resourceId)
                    break

    assert len(failures) == 0, f"{len(failures)}/{policyMatchCount} resources failed to comply with Kyverno policy '{policyName}': {failures}"
