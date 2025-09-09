import logging
import os
import yaml
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
    Dynamically discover all Kyverno policies in the policies directory.
    Returns a list of policy names.
    """
    policyNames = []
    policiesDir = os.path.join(os.path.dirname(__file__), 'policies')
    
    # Walk through all directories under policies
    for root, _ , files in os.walk(policiesDir):
        for file in files:
            if file.endswith('.yaml'):
                file_path = os.path.join(root, file)
                try:
                    with open(file_path, 'r') as f:
                        policy = yaml.safe_load(f)
                        if (policy and
                            policy.get('kind') == 'ClusterPolicy' and
                            policy.get('metadata', {}).get('name')):
                            policyNames.append(policy['metadata']['name'])
                except (yaml.YAMLError, IOError) as e:
                    logger.warning(f"Error reading policy file {file_path}: {e}")
    
    return policyNames

@pytest.mark.parametrize("policyName", get_policy_names())

def testPolicies(policyName):
    clusterPolicies = dynClient.resources.get(
        api_version="kyverno.io/v1", kind="ClusterPolicy"
    )
    try:
        policy = clusterPolicies.get(name=policyName)
    except NotFoundError as e:
        pytest.fail(f"Policy is not installed: {e}")

    assert policy.metadata.name == policyName

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
