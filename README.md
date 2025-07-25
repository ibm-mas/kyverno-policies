kyverno-policies
===============================================================================

Policy List
-------------------------------------------------------------------------------
All MAS ClusterPolicies are prefixed as `mas-` and are constrained to the standard MAS namespaces only (`mas-*`) allowing them to be deployed into a cluster without impacting anything unrelated to Maximo Application Suite.

All policies are configured to operate in **Audit** mode only.

### Security Context
- **[Disallow Priviledge Escalation](policies/security-context/disallow-priviledge-escalation/disallow-priviledge-escalation.yaml)** ensures that all permissions are dropped from our pods, with only those required added back.  This policy is based on the standard Kyverno [require-drop-all](https://github.com/kyverno/policies/tree/main/best-practices/require-drop-all) policy.
- **[Disallow Run as root User](policies/security-context/disallow-run-as-root-user/disallow-run-as-root-user.yaml)** ensures that our containers do not use `runAsUser` to set the user to root (uid 0), which can potentially allow an attacker to gain access to the host and escalate privileges.  This policy is based on the standard Kyverno [require-run-as-non-root-user](https://github.com/kyverno/policies/tree/main/pod-security/restricted/require-run-as-non-root-user) policy.
- **[Disallow sysctls](policies/security-context/disallow-sysctls/disallow-sysctls.yaml)**
- **[Require Drop All](policies/security-context/require-image-digest/require-image-digest.yaml)** ensures that our container images are immutable and eliminates the potential for man in the middle attacks via image tag spoofing
- **[Require Run as Non-root](policies/security-context/require-run-as-nonroot/require-run-as-nonroot.yaml)** ensures that our containers are not ran as as root, which can potentially allow an attacker to gain access to the host and escalate privileges.  This policy is based on the standard Kyverno [require-run-as-nonroot](https://github.com/kyverno/policies/tree/main/pod-security/restricted/require-run-as-nonroot) policy.
- **[Require Read-Only root Filesystem](policies/security-context/require-ro-rootfs/require-ro-rootfs.yaml)**

### Scheduling
- **[Disallow Master Node Tolerations](policies/scheduling/disallow-master-infra-tolerations/disallow-master-infra-tolerations.yaml)** ensures that no pods are configured to allow scheduling on nodes tainted with the `node-role.kubernetes.io` taints for  master, infra, or control-plane nodes.
- **[Disallow Node Selection](policies/scheduling/disallow-node-selection/disallow-node-selection.yaml)**
- **[Require TopologySpreadConstraints](policies/scheduling/require-topologyspreadconstraints/require-topologyspreadconstraints.yaml)**

### Role Based Access Control
- **[Disallow Role with Wildcards](policies/rbac/disallow-role-with-wildcards/disallow-role-with-wildcards.yaml)** ensures that our Roles do not use `*` to define either the resources or the verbs of any rule, this ensures the permissions granted follow the principle of least privilege (PoLP).

### Other
- **[Disallow Pod Template Hash](policies/other/disallow-pod-template-hash/disallow-pod-template-hash.yaml)**
- **[Disallow Service External IPs](policies/other/disallow-service-external-ips/disallow-service-external-ips.yaml)**
- **[Require Image Digest](policies/other/require-image-digest/require-image-digest.yaml)** ensures that all references to container images are immutable, eliminating the potential for man-in-the-middle attacks via image registry/tag spoofing.
- **[Require Pod Probes](policies/other/require-pod-probes/require-pod-probes.yaml)** ensures that all pods define liveness, readiness, & startup probes to support standard Kubernetes lifecycle management.  This policy is based on the standard Kyverno [require-probes](https://github.com/kyverno/policies/tree/main/best-practices/require-probes) policy.
- **[Require Unique Pod Probes](policies/other/require-pod-probes-unique/require-pod-probes-unique.yaml)** ensures that the liveness and readiness probes are not the same; liveness and readiness checks accomplish different goals and reusing the same probe for both is an anti-pattern that can lead to problems at runtime.
- **[Require Pod Requests and Limits](policies/other/require-pod-requests-limits/require-pod-requests-limits.yaml)** ensures that all pods define resource requests and limits, enabling optimal scheduling and preventing unexpected resource consumption.  This policy is based on the standard Kyverno [require-pod-requests-limits](https://github.com/kyverno/policies/tree/main/best-practices/require-pod-requests-limits) policy.
- **[Require StorageClass](policies/other/require-storageclass/require-storageclass.yaml)**


Install Kyverno
-------------------------------------------------------------------------------
https://kyverno.io/docs/installation/methods/

```bash
helm repo add kyverno https://kyverno.github.io/kyverno/
helm repo update

# Install Kyverno
set -f
helm install kyverno kyverno/kyverno -n kyverno --create-namespace --set --enablePolicyException=true --set --exceptionNamespace=*
set +f

# Increase memory limit for the reports controller
oc -n kyverno set resources deployment kyverno-reports-controller -c=controller --limits=memory=1024Mi
```

Install Kyverno CLI
-------------------------------------------------------------------------------

```bash
curl -LO https://github.com/kyverno/kyverno/releases/download/v1.14.4/kyverno-cli_v1.14.4_linux_x86_64.tar.gz
tar -xvf kyverno-cli_v1.14.4_linux_x86_64.tar.gz
mv kyverno /usr/local/bin
rm kyverno-cli_v1.14.4_linux_x86_64.tar.gz
kyverno version
```

Testing Policies
-------------------------------------------------------------------------------
https://kyverno.io/docs/testing-policies/

```bash
kyverno test policies
```


Applying Policies
-------------------------------------------------------------------------------
Note that some of these policies require additional permissions to be enabled for the `kyverno-reports-controller` service account, these permissions are documented in [policies/kyverno-additional-rbac.yaml](policies/kyverno-additional-rbac.yaml).

Clone the repo and install:
```bash
kustomize build policies/ | oc apply -f -
```

Install directly from GitHub:
```bash
kustomize build https://github.com/ibm-mas/kyverno-policies//policies/ | oc apply -f -
```

Validating Policies
-------------------------------------------------------------------------------
A simple pytest script has been provided to easily generate a compliance report for the MAS Kyverno policies:

```
pytest -q -r A test_policies.py

...

PASSED test_policies.py::testPolicies[mas-disallow-pod-template-hash]
PASSED test_policies.py::testPolicies[mas-disallow-service-external-ips]
PASSED test_policies.py::testPolicies[mas-require-image-digest]
PASSED test_policies.py::testPolicies[mas-require-pod-probes-unique]
PASSED test_policies.py::testPolicies[mas-require-pod-requests-limits]
PASSED test_policies.py::testPolicies[mas-require-storageclass]
PASSED test_policies.py::testPolicies[mas-disallow-master-infra-tolerations]
PASSED test_policies.py::testPolicies[mas-disallow-node-selection]
PASSED test_policies.py::testPolicies[mas-disallow-run-as-root-user]
PASSED test_policies.py::testPolicies[mas-disallow-sysctls]
PASSED test_policies.py::testPolicies[mas-require-drop-all]
PASSED test_policies.py::testPolicies[mas-require-ro-rootfs]
FAILED test_policies.py::testPolicies[mas-require-pod-probes] - AssertionError: One or more resources failed to comply with Kyverno policy 'mas-require-pod-probes': ['Deployment:mas-fvtrelease-core/fvtrelease-entitymgr-scimcfg', 'Deployment:mas-fvtrelease-core/fvtrelease-entitymgr-kafkacfg', 'Pod:mas-fvtrelease-core/fvtrelea...
FAILED test_policies.py::testPolicies[mas-disallow-role-with-wildcards] - AssertionError: One or more resources failed to comply with Kyverno policy 'mas-disallow-role-with-wildcards': ['Role:mas-fvtrelease-core/ibm-mas.v9.1.1-ibm-mas-e-bSj8DM1pnhMr18FKNvEcJrxUOiLm4A6qaTxcmK', 'Role:mas-fvtrelease-core/ibm-mas-mobileapi', 'Role:mas-fv...
FAILED test_policies.py::testPolicies[mas-require-topologyspreadconstraints] - AssertionError: One or more resources failed to comply with Kyverno policy 'mas-require-topologyspreadconstraints': ['Deployment:mas-fvtrelease-core/fvtrelease-coreapi']
FAILED test_policies.py::testPolicies[mas-disallow-privilege-escalation] - AssertionError: One or more resources failed to comply with Kyverno policy 'mas-disallow-privilege-escalation': ['ReplicaSet:mas-fvtrelease-core/ibm-truststore-mgr-controller-manager-68fcf96b9', 'Job:mas-fvtrelease-core/fvtrelease-truststore-worker', 'ReplicaSet...
FAILED test_policies.py::testPolicies[mas-require-run-as-nonroot] - AssertionError: One or more resources failed to comply with Kyverno policy 'mas-require-run-as-nonroot': ['CronJob:mas-fvtrelease-core/fvtrelease-accapppoints', 'Deployment:mas-fvtrelease-core/fvtrelease-mobileapi', 'CronJob:mas-fvtrelease-core/fvtrelease-adopti...
5 failed, 12 passed in 24.36s
```

Auditing Policies
-------------------------------------------------------------------------------
```bash
oc get clusterpolicies
NAME                                    ADMISSION   BACKGROUND   READY   AGE    MESSAGE
mas-disallow-master-infra-tolerations   true        true         True    157m   Ready
mas-disallow-node-selection             true        true         True    65m    Ready
mas-disallow-pod-template-hash          true        true         True    54m    Ready
mas-disallow-privilege-escalation       true        true         True    156m   Ready
mas-disallow-role-with-wildcards        true        true         True    156m   Ready
mas-disallow-run-as-root-user           true        true         True    156m   Ready
mas-disallow-service-external-ips       true        true         True    48m    Ready
mas-disallow-sysctls                    true        true         True    34m    Ready
mas-require-drop-all-capabilities       true        true         True    156m   Ready
mas-require-image-digest                true        true         True    156m   Ready
mas-require-pod-probes                  true        true         True    156m   Ready
mas-require-requests-limits             true        true         True    156m   Ready
mas-require-ro-rootfs                   true        true         True    11m    Ready
mas-require-run-as-nonroot              true        true         True    156m   Ready
mas-require-storageclass                true        true         True    85m    Ready
mas-require-topologyspreadconstraints   true        true         True    97m    Ready
```

```bash
oc get policyreports --all-namespaces
NAMESPACE           NAME                                   KIND         NAME                                                     PASS   FAIL   WARN   ERROR   SKIP   AGE
mas-dev-core        002c3a02-54f2-46e3-89a8-17ab45cf1a05   ReplicaSet   dev-entitymgr-idpcfg-5f5798c74b                          2      0      0      0       0      13h
mas-dev-core        04d61b8e-259c-4870-9d29-b5ead018b121   Deployment   dev-entitymgr-watsonstudiocfg                            2      0      0      0       0      13h
mas-dev-core        054c52bc-0c0f-4fb2-9bd6-ce1efa1dce7d   Pod          dev-coreapi-84679768d9-g8jnm                             2      0      0      0       0      13h
mas-dev-core        0594038c-880c-48e6-8a35-220e96219d3f   ReplicaSet   ibm-truststore-mgr-controller-manager-5f8d54d5d9         1      1      0      0       0      13h
mas-dev-core        0dc53114-03bf-4ad5-a075-ed3e290074eb   Pod          dev-usage-daily-29201000-g8q5v                           2      0      0      0       0      25m
mas-dev-core        0e9a0e31-372d-47c3-a333-6053b87e9f26   ReplicaSet   dev-workspace-coordinator-7db47b488f                     2      0      0      0       0      13h
mas-dev-core        13ae29e2-a963-40dc-8319-963cbcd5dd32   Pod          dev-workspace-coordinator-7db47b488f-gft7w               2      0      0      0       0      13h
mas-dev-core        14604ed3-dbf3-46bb-9d6c-ad5f79d100e6   Pod          dev-entitymgr-suite-65dc7564dc-hshv9                     2      0      0      0       0      13h
mas-dev-core        14a85bf4-2656-40b2-8093-61944bc9f6c6   Pod          dev-entitymgr-ws-5c56d74d7c-j8thw                        2      0      0      0       0      13h
mas-dev-core        175a856c-a6d5-4b04-9ee1-1578926bc7da   Pod          dev-entitymgr-jdbccfg-694ff6d665-575gt                   2      0      0      0       0      13h
mas-dev-core        189f3205-3217-4a82-9efc-d72dba08c0e1   Pod          dev-usage-historical-29201010-29n65                      2      0      0      0       0      15m
mas-dev-core        1960ea25-9ebe-4b77-8bc6-c97d2bf1e852   Deployment   dev-entitymgr-suite                                      2      0      0      0       0      13h
mas-dev-core        19a6639f-ec42-44a3-9ff3-d9174857812c   Deployment   dev-catalogmgr                                           2      0      0      0       0      13h
mas-dev-core        1a351b0d-0240-4a91-b8e0-c1023acd26e8   Deployment   dev-admin-dashboard                                      2      0      0      0       0      13h
mas-dev-core        1aa30cf4-189d-44dd-8c17-70f0e5fa7a5b   Pod          ibm-truststore-mgr-controller-manager-5f8d54d5d9-p2dbd   2      0      0      0       0      13h
mas-dev-core        1af6bb61-10b3-48dc-9fd5-d2d02a7f468d   Deployment   ibm-truststore-mgr-controller-manager                    1      1      0      0       0      13h
```
