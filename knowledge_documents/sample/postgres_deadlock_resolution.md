# Procedure: PostgreSQL Connection Pool Exhaustion and Deadlock Resolution

**Document ID:** PROC-DB-004  
**Category:** Database  
**Service:** PostgreSQL Core & RDS  
**Owner:** Database Reliability Engineering (DBRE)  
**Version:** 3.0  

## 1. Overview and Symptoms
Symptoms include client timeouts with error `FATAL: remaining connection slots are reserved for non-replication superuser connections` or `canceling statement due to lock timeout`. Application health checks report 500 errors on database operations.

Common Root Causes:
- Leaked database connections in application thread pools (missing session close in `finally` blocks).
- Unindexed long-running analytical queries blocking table rows during write operations.
- Deadlocks caused by inconsistent row update ordering across microservices.

## 2. Diagnostic Investigation
1. Identify blocking locks and active queries:
   ```sql
   SELECT pid, usename, client_addr, state, now() - query_start AS duration, query
   FROM pg_stat_activity
   WHERE state != 'idle' AND (now() - query_start) > interval '10 seconds'
   ORDER BY duration DESC;
   ```
2. Detect exclusive locks waiting on other transactions:
   ```sql
   SELECT blocked_locks.pid AS blocked_pid, blocking_locks.pid AS blocking_pid,
          blocked_activity.query AS blocked_statement, blocking_activity.query AS current_statement
   FROM pg_catalog.pg_locks blocked_locks
   JOIN pg_catalog.pg_stat_activity blocked_activity ON blocked_activity.pid = blocked_locks.pid
   JOIN pg_catalog.pg_locks blocking_locks ON blocking_locks.locktype = blocked_locks.locktype
   WHERE NOT blocked_locks.granted;
   ```

## 3. Resolution Steps
1. Terminate orphaned blocking backend sessions:
   ```sql
   SELECT pg_terminate_backend(<blocking_pid>);
   ```
2. Enforce safety timeouts to prevent cascading pileups:
   ```sql
   ALTER SYSTEM SET statement_timeout = '15s';
   ALTER SYSTEM SET idle_in_transaction_session_timeout = '30s';
   SELECT pg_reload_conf();
   ```
3. Restart or flush PgBouncer connection pool:
   `PAUSE dbname; RELOAD; RESUME dbname;`

## 4. Risks and Verification
- Terminating an active transaction will cause an immediate rollback for that specific HTTP client request.
- Verification: Confirm active connections drop below 70% of `max_connections` and queries execute under 200ms.
