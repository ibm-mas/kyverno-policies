import argparse
import sys
import urllib3

from kubernetes import config
from kubernetes.dynamic.exceptions import NotFoundError
from openshift.dynamic import DynamicClient

urllib3.disable_warnings()
k8s_client = config.new_client_from_config()
dynClient = DynamicClient(k8s_client)

parser = argparse.ArgumentParser()
parser.add_argument("-n", "--namespace", required=False, default=None)
args = parser.parse_args()

def get_policy_names():
    """
    Dynamically discover all Kyverno policies in the cluster.
    Returns a list of policy names.
    """
    clusterPolicies = dynClient.resources.get(api_version="kyverno.io/v1", kind="ClusterPolicy")
    policies = clusterPolicies.get()
    policyNames = [policy.metadata.name for policy in policies.items]
    return policyNames


clusterPolicies = dynClient.resources.get(
    api_version="kyverno.io/v1", kind="ClusterPolicy"
)

policyNames = get_policy_names()
failuresByPolicyRule = {}
failuresByNamespace = {}

policyReports = dynClient.resources.get(
    api_version="wgpolicyk8s.io/v1alpha2", kind="PolicyReport"
)
reports = policyReports.get(namespace=args.namespace)
for report in reports.items:
    resourceId = f"{report.scope.kind}:{report.scope.namespace}/{report.scope.name}"
    resourceIdNoNamespace = f"{report.scope.kind}:{report.scope.name}"
    for result in report.results:
        # result.rule = result.rule.replace("autogen-", "")
        policyRuleName = f"{result.policy}/{result.rule}"
        if result.result == "fail":
            if result.policy not in failuresByPolicyRule:
                failuresByPolicyRule[result.policy] = {result.rule: []}
            if result.rule not in failuresByPolicyRule[result.policy]:
                failuresByPolicyRule[result.policy][result.rule] = []

            failuresByPolicyRule[result.policy][result.rule].append(resourceId)

            if report.scope.namespace not in failuresByNamespace:
                failuresByNamespace[report.scope.namespace] = {policyRuleName: []}
            if policyRuleName not in failuresByNamespace[report.scope.namespace]:
                failuresByNamespace[report.scope.namespace][policyRuleName] = []

            failuresByNamespace[report.scope.namespace][policyRuleName].append(resourceIdNoNamespace)


# print()
# print()
# print("Failures by Policy")
# print("================================================================================")
# for policyName in failuresByPolicyRule:
#     print()
#     print(policyName)
#     print("--------------------------------------------------------------------------------")
#     for policyRule in failuresByPolicyRule[policyName]:
#         print()
#         print(f"{policyRule} ({len(failuresByPolicyRule[policyName][policyRule])} failures)")
#         for resource in failuresByPolicyRule[policyName][policyRule]:
#             print(f"- {resource}")

print()
print()
print("Failures by Namespace")
print("================================================================================")
for namespace in failuresByNamespace:
    print()
    print(namespace)
    print("--------------------------------------------------------------------------------")
    for policyRule in failuresByNamespace[namespace]:
        print(f"{policyRule} ({len(failuresByNamespace[namespace][policyRule])} failures)")
        for resource in failuresByNamespace[namespace][policyRule]:
            print(f"- {resource}")
