# Smart Workflow Architecture

## High-Level Flow Diagram

```
┌────────────────────────────────────────────────────────────────────┐
│                     USER PROMPT                                    │
│  "dockerize my application and show me the logs in grafana"       │
└───────────────────────────┬────────────────────────────────────────┘
                            │
                            ↓
┌────────────────────────────────────────────────────────────────────┐
│                  TOOL: show_app_logs()                             │
│          Smart Dockerize and Show Logs Workflow                    │
└───────────────────────────┬────────────────────────────────────────┘
                            │
                ┌───────────┴───────────┐
                │                       │
                ↓                       ↓
┌───────────────────────┐   ┌──────────────────────┐
│  STEP 1: ANALYZE      │   │  Detect app type     │
│  Application          │   │  Find dependencies   │
│  Structure            │   │  Identify entry      │
└───────┬───────────────┘   └──────────────────────┘
        │
        ↓
┌───────────────────────┐   ┌──────────────────────┐
│  STEP 2: CHECK        │   │  docker ps -a        │
│  Container Status     │   │  Categorize apps     │
│                       │   │  Check running       │
└───────┬───────────────┘   └──────────────────────┘
        │
        ├─→ No containers? ──→ Run dockerize_project()
        ├─→ Stopped? ──────→ docker-compose up -d
        └─→ Running? ──────→ Continue
        │
        ↓
┌───────────────────────┐   ┌──────────────────────┐
│  STEP 3: SETUP        │   │  Check if            │
│  Monitoring Stack     │   │  monitoring exists   │
│                       │   │  Create configs      │
└───────┬───────────────┘   │  Start services      │
        │                   └──────────────────────┘
        ├─→ Not exists? ───→ setup_complete_monitoring()
        ├─→ Not running? ──→ docker-compose -f monitoring.yml up -d
        └─→ Running? ──────→ Continue
        │
        ↓
┌───────────────────────┐   ┌──────────────────────┐
│  STEP 4: VALIDATE     │   │  Test Loki health    │
│  Log Flow             │   │  Test Promtail       │
│  (Auto-Fix)           │   │  Query log count     │
└───────┬───────────────┘   └──────────────────────┘
        │
        ├─→ Issue detected? ─┐
        │                    │
        │    ┌───────────────┴─────────────┐
        │    │  AUTO-FIX WORKFLOW          │
        │    ├─────────────────────────────┤
        │    │  1. Fix Promtail config     │
        │    │  2. Restart services        │
        │    │  3. Wait 10 seconds         │
        │    │  4. Re-validate             │
        │    └───────────────┬─────────────┘
        │                    │
        └────────────────────┴─→ Continue
        │
        ↓
┌───────────────────────┐   ┌──────────────────────┐
│  STEP 5: LAUNCH       │   │  webbrowser.open()   │
│  Grafana Dashboard    │   │  http://localhost:   │
│                       │   │  3001                │
└───────┬───────────────┘   └──────────────────────┘
        │
        ↓
┌───────────────────────┐   ┌──────────────────────┐
│  STEP 6: VERIFY       │   │  Query Loki API      │
│  Logs Visible         │   │  Show log samples    │
│                       │   │  Report status       │
└───────┬───────────────┘   └──────────────────────┘
        │
        ↓
┌────────────────────────────────────────────────────────────────────┐
│                     FINAL STATUS REPORT                            │
│  ✅ ALL SYSTEMS OPERATIONAL                                         │
│  ✅ Application dockerized and running                              │
│  ✅ Monitoring stack operational                                    │
│  ✅ Logs flowing and visible in Grafana                             │
└────────────────────────────────────────────────────────────────────┘
```

## Component Interaction Diagram

```
┌─────────────────┐
│   USER INPUT    │
│  (MCP Client)   │
└────────┬────────┘
         │ Request: show_app_logs(project_root)
         ↓
┌────────────────────────────────────────────────────┐
│              MCP SERVER (server.py)                │
│  ┌──────────────────────────────────────────────┐ │
│  │  Tool 20: show_app_logs()                    │ │
│  └──────────────────┬───────────────────────────┘ │
└─────────────────────┼──────────────────────────────┘
                      │ Calls
                      ↓
┌─────────────────────────────────────────────────────────────────┐
│         ORCHESTRATOR (logging_monitor.py)                       │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │  smart_dockerize_and_show_logs()                          │ │
│  │                                                            │ │
│  │  Calls:                                                    │ │
│  │  • analyze_application()         (analyzer.py)            │ │
│  │  • check_containers_running()    (self)                   │ │
│  │  • start_application_containers() (self)                  │ │
│  │  • dockerize_full_project()      (multi_service_handler)  │ │
│  │  • setup_complete_monitoring()   (self)                   │ │
│  │  • diagnose_monitoring_stack()   (self)                   │ │
│  │  • fix_promtail_config()         (self)                   │ │
│  │  • restart_monitoring_services() (self)                   │ │
│  │  • fetch_logs_from_loki()        (self)                   │ │
│  └───────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
                      │
                      ↓
┌─────────────────────────────────────────────────────────────────┐
│                    DOCKER ENVIRONMENT                           │
│                                                                 │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │ Application  │  │  Monitoring  │  │   Browser    │         │
│  │ Containers   │  │  Stack       │  │              │         │
│  │              │  │              │  │              │         │
│  │ • Backend    │  │ • Grafana    │  │ Opens:       │         │
│  │ • Frontend   │  │ • Loki       │  │ localhost:   │         │
│  │ • Database   │  │ • Promtail   │  │ 3001         │         │
│  └──────┬───────┘  └──────┬───────┘  └──────────────┘         │
│         │                 │                                     │
│         │ stdout/stderr   │                                     │
│         └────────────────→│                                     │
│                           │ Collects & Stores Logs              │
│                           └─────────────────────────────────────┘
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

## Decision Tree

```
START: show_app_logs(project_root)
│
├─→ Are containers running?
│   ├─→ YES → Continue to monitoring check
│   ├─→ NO, but docker-compose.yml exists
│   │   └─→ Run: docker-compose up -d
│   └─→ NO, and no docker-compose.yml
│       └─→ Run: dockerize_full_project()
│
├─→ Is monitoring setup?
│   ├─→ YES → Continue to validation
│   └─→ NO
│       └─→ Run: setup_complete_monitoring()
│
├─→ Are monitoring containers running?
│   ├─→ YES → Continue to validation
│   └─→ NO
│       └─→ Run: docker-compose -f monitoring.yml up -d
│
├─→ Is Loki ready?
│   ├─→ YES → Continue
│   └─→ NO
│       └─→ Wait and retry (up to 3 times)
│
├─→ Is Promtail ready?
│   ├─→ YES → Continue
│   └─→ NO
│       └─→ Wait and retry (up to 3 times)
│
├─→ Are logs flowing?
│   ├─→ YES → Success! Launch Grafana
│   └─→ NO
│       └─→ AUTO-FIX:
│           ├─→ Fix Promtail config
│           ├─→ Restart Promtail & Loki
│           ├─→ Wait 10 seconds
│           ├─→ Re-check logs
│           ├─→ If still no logs → Report issue
│           └─→ If logs flowing → Success!
│
└─→ Launch Grafana in browser
    └─→ Verify logs visible
        └─→ Show sample logs
            └─→ END: Success report
```

## Data Flow

```
┌──────────────┐
│ Application  │
│ Generates    │
│ Logs         │
│ (stdout/     │
│  stderr)     │
└──────┬───────┘
       │
       │ Docker captures
       ↓
┌──────────────────┐
│ Docker Log       │
│ Files            │
│ /var/lib/docker/ │
│ containers/      │
└──────┬───────────┘
       │
       │ Promtail reads
       ↓
┌──────────────────┐         ┌─────────────────┐
│ Promtail         │──HTTP──→│ Loki            │
│ (Log Collector)  │ Push    │ (Log Storage)   │
│                  │ Logs    │                 │
│ Scrapes:         │         │ Stores:         │
│ • Container logs │         │ • Time series   │
│ • Adds labels    │         │ • Indexed by    │
│ • Filters        │         │   labels        │
└──────────────────┘         └────────┬────────┘
                                      │
                                      │ LogQL queries
                                      ↓
                             ┌────────────────────┐
                             │ Grafana            │
                             │ (Visualization)    │
                             │                    │
                             │ Shows:             │
                             │ • Real-time logs   │
                             │ • Time-based view  │
                             │ • Filter by        │
                             │   service/label    │
                             └────────┬───────────┘
                                      │
                                      │ User views in browser
                                      ↓
                             ┌────────────────────┐
                             │ Browser            │
                             │ localhost:3001     │
                             │ (User)             │
                             └────────────────────┘
```

## State Machine

```
┌──────────────┐
│   INITIAL    │ (User runs show_app_logs)
└──────┬───────┘
       │
       ↓
┌──────────────┐
│  ANALYZING   │ (Detect app type & dependencies)
└──────┬───────┘
       │
       ↓
┌──────────────┐
│  CHECKING    │ (Verify container status)
│  CONTAINERS  │
└──────┬───────┘
       │
       ├─→ Need Dockerization? ──→ [DOCKERIZING] ──┐
       │                                            │
       └────────────────────────────────────────────┤
                                                    ↓
┌──────────────┐                          ┌─────────────────┐
│  SETTING UP  │←─────────────────────────│  CONTAINERS     │
│  MONITORING  │                          │  READY          │
└──────┬───────┘                          └─────────────────┘
       │
       ↓
┌──────────────┐
│  VALIDATING  │ (Check Loki, Promtail, logs)
└──────┬───────┘
       │
       ├─→ Issues found? ──→ [FIXING] ──┐
       │                                 │
       └─────────────────────────────────┤
                                         ↓
┌──────────────┐                 ┌──────────────┐
│  LAUNCHING   │←────────────────│  VALIDATED   │
│  GRAFANA     │                 └──────────────┘
└──────┬───────┘
       │
       ↓
┌──────────────┐
│  VERIFYING   │ (Confirm logs visible)
└──────┬───────┘
       │
       ↓
┌──────────────┐
│   SUCCESS    │ (Report complete status)
└──────────────┘
```

## Auto-Fix Logic Flow

```
VALIDATE:
│
├─→ Check Loki health (http://localhost:3100/ready)
│   └─→ Not ready? → Error, can't fix automatically
│
├─→ Check Promtail health (http://localhost:9080/ready)
│   └─→ Not ready? → Error, can't fix automatically
│
├─→ Check logs flowing (query Loki API)
    │
    ├─→ Logs present? → Success, no fix needed
    │
    └─→ No logs? → TRIGGER AUTO-FIX:
        │
        ├─→ Read promtail-config.yml
        │   │
        │   ├─→ Contains "localhost:3100"?
        │   │   └─→ Replace with "loki:3100"
        │   │
        │   └─→ Write fixed config
        │
        ├─→ Restart Promtail container
        │   └─→ docker-compose restart promtail
        │
        ├─→ Restart Loki container
        │   └─→ docker-compose restart loki
        │
        ├─→ Wait 10 seconds (service stabilization)
        │
        ├─→ Re-validate logs
        │   │
        │   ├─→ Logs now present? → Success!
        │   │
        │   └─→ Still no logs? → Report manual intervention needed
        │
        └─→ Return fix report
```

## File Structure

```
docker-mcp/
├── server.py (785 lines)
│   └── @mcp.tool() show_app_logs()
│       └── Calls: smart_dockerize_and_show_logs()
│
├── docker_tools/
│   ├── logging_monitor.py (1485 lines)
│   │   ├── check_containers_running()        [NEW]
│   │   ├── start_application_containers()    [NEW]
│   │   ├── smart_dockerize_and_show_logs()   [NEW] ← Main function
│   │   ├── validate_and_fix_monitoring()     [Existing]
│   │   ├── diagnose_monitoring_stack()       [Existing]
│   │   ├── fix_promtail_config()             [Existing]
│   │   ├── restart_monitoring_services()     [Existing]
│   │   └── ... (other monitoring functions)
│   │
│   ├── analyzer.py
│   │   └── analyze_application()
│   │
│   └── multi_service_handler.py
│       ├── dockerize_full_project()
│       └── detect_services()
│
├── README.md
│   └── Lists all 20 tools
│
├── WORKFLOW_GUIDE.md                         [NEW]
│   └── Complete user documentation
│
├── IMPLEMENTATION_SUMMARY.md                 [NEW]
│   └── Technical implementation details
│
└── ARCHITECTURE.md                           [THIS FILE]
    └── Visual diagrams and architecture
```
