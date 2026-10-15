# Runbook: Kubernetes Pod OOMKilled and CrashLoopBackOff Remediation

**Document ID:** RUNBOOK-K8S-001  
**Category:** Infrastructure  
**Service:** Kubernetes / Container Platform  
**Owner:** Cloud Platform & SRE Team  
**Version:** 2.1  

## 1. Overview and Symptoms
When a container in a Kubernetes pod attempts to allocate more memory than its configured resource limit (`resources.limits.memory`), the Linux kernel Out-Of-Memory (OOM) killer terminates the process with exit code 137. The kubelet restarts the container, leading to a `CrashLoopBackOff` status.

Key diagnostic indicators:
- `kubectl describe pod <pod-name>` shows `Last State: Terminated`, `Reason: OOMKilled`, `Exit Code: 137`.
- Container metrics show memory utilization abruptly hitting 100% of limits before dying.
- Log lines end abruptly with no unhandled Java/Node stack traces.

## 2. Diagnostic Steps
1. Verify pod termination reason:
   ```bash
   kubectl get pod <pod-name> -o jsonpath='{.status.containerStatuses[*].lastState.terminated.reason}'
   ```
2. Inspect current memory limits and usage:
   ```bash
   kubectl top pod <pod-name> --containers
   ```
3. For JVM applications, inspect GC logs and verify `-XX:MaxRAMPercentage` is set to ~75% instead of a fixed heap larger than the container limit.

## 3. Remediation Procedures
1. Immediate Mitigation (Emergency Patch):
   Increase container memory limit by 50% in the deployment spec:
   ```bash
   kubectl set resources deployment/<deployment-name> --limits=memory=1024Mi --requests=memory=512Mi
   ```
2. For JVM memory leaks or metaspace growth, configure JVM flags in the environment:
   `-XX:+ExitOnOutOfMemoryError -XX:MaxRAMPercentage=75.0`
3. Rollout verification:
   ```bash
   kubectl rollout status deployment/<deployment-name>
   ```

## 4. Verification and Rollback
- Verification: Monitor pod restarts for 15 minutes using `kubectl get pods -w`. Restarts must remain 0.
- Rollback: If new limits cause node resource starvation, revert to previous revision:
  ```bash
  kubectl rollout undo deployment/<deployment-name>
  ```
