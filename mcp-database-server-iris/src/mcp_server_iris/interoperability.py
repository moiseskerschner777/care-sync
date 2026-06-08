from enum import Enum
from mcp.types import Tool, TextContent
from mcp_server_iris.tools import transaction, raise_on_error
from iris import IRISReference


class ProductionStatus(Enum):
    Unknown = 0
    Running = 1
    Stopped = 2
    Suspended = 3
    Troubled = 4
    NetworkStopped = 5
    ShardWorkerProhibited = 6


log_types = [
    "ASSERT",
    "ERROR",
    "WARNING",
    "INFO",
    "TRACE",
    "ALERT",
]


class LogType(Enum):
    Assert = 1
    Error = 2
    Warning = 3
    Info = 4
    Trace = 5
    Alert = 6


def production_items_status(iris, running: bool, name: str) -> list[str]:
    result = []
    namespace = iris.classMethodString("%SYSTEM.Process", "NameSpace")
    prod = iris.classMethodObject("Ens.Config.Production", "%OpenId", name)
    if not prod:
        raise ValueError(f"Production {name} not found")
    items = prod.getObject("Items")
    for i in range(1, items.invokeInteger("Count") + 1):
        item = items.invokeObject("GetAt", i)
        item_name = item.getString("Name")
        status_info = []
        enabled = item.getBoolean("Enabled")
        status_info += [f"Enabled={enabled}"]
        if enabled:
            val = iris.getString(
                "^IRIS.Temp.EnsHostMonitor", namespace, item_name, "%Status"
            )
            status_info += [f"Status={val}"]

        result.append(f"{item_name}: " + "; ".join(status_info))
    return result


# ---------------------------------------------------------------------------
# Tool definitions
# ---------------------------------------------------------------------------

def list_tools() -> list[Tool]:
    return [
        Tool(
            name="interoperability_production_create",
            description="Create an Interoperability Production",
            inputSchema={
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "Production class name (e.g. MyPkg.MyProduction)"},
                },
                "required": ["name"],
            },
        ),
        Tool(
            name="interoperability_production_status",
            description="Status of an Interoperability Production",
            inputSchema={
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "Production name (optional, defaults to running production)"},
                    "full_status": {"type": "boolean", "description": "Include per-item status", "default": False},
                },
            },
        ),
        Tool(
            name="interoperability_production_start",
            description="Start an Interoperability Production",
            inputSchema={
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "Production name (optional)"},
                },
            },
        ),
        Tool(
            name="interoperability_production_stop",
            description="Stop an Interoperability Production",
            inputSchema={
                "type": "object",
                "properties": {
                    "timeout": {"type": "integer", "description": "Timeout in seconds (default 10)"},
                    "force": {"type": "boolean", "description": "Force stop", "default": False},
                },
            },
        ),
        Tool(
            name="interoperability_production_recover",
            description="Recover an Interoperability Production",
            inputSchema={"type": "object", "properties": {}},
        ),
        Tool(
            name="interoperability_production_needsupdate",
            description="Check if an Interoperability Production needs update",
            inputSchema={"type": "object", "properties": {}},
        ),
        Tool(
            name="interoperability_production_update",
            description="Update Interoperability Production",
            inputSchema={
                "type": "object",
                "properties": {
                    "timeout": {"type": "integer"},
                    "force": {"type": "boolean", "default": False},
                },
            },
        ),
        Tool(
            name="interoperability_production_logs",
            description="Get Interoperability Production logs",
            inputSchema={
                "type": "object",
                "properties": {
                    "item_name": {"type": "string"},
                    "limit": {"type": "integer", "default": 10},
                    "log_type_info": {"type": "boolean", "default": False},
                    "log_type_alert": {"type": "boolean", "default": False},
                    "log_type_error": {"type": "boolean", "default": True},
                    "log_type_warning": {"type": "boolean", "default": True},
                },
            },
        ),
        Tool(
            name="interoperability_production_queues",
            description="Get Interoperability Production queues",
            inputSchema={"type": "object", "properties": {}},
        ),
    ]


# ---------------------------------------------------------------------------
# Handlers
# ---------------------------------------------------------------------------

async def _create(args: dict, iris, db) -> list[TextContent]:
    name = args["name"]
    if "." not in name:
        raise ValueError(
            "Production name must be in format packagenamespace.productionname"
        )
    with transaction(iris):
        prod = iris.classMethodObject("%Dictionary.ClassDefinition", "%OpenId", name)
        if prod:
            raise ValueError(f"Class {name} already exists")
        prod = iris.classMethodObject("Ens.Config.Production", "%New", name)
        raise_on_error(iris, prod.invokeString("SaveToClass"))
        raise_on_error(iris, prod.invokeString("%Save"))
        raise_on_error(iris, iris.classMethodString("%SYSTEM.OBJ", "Compile", name, "ck-d"))
    return [TextContent(type="text", text="true")]


async def _status(args: dict, iris, db) -> list[TextContent]:
    name = args.get("name")
    full_status = args.get("full_status", False)
    refname = IRISReference(iris)
    refname.setValue(name)
    refstatus = IRISReference(iris)
    raise_on_error(
        iris,
        iris.classMethodString("Ens.Director", "GetProductionStatus", refname, refstatus),
    )
    if not refname.getValue():
        raise ValueError("No running production found")
    name = refname.getValue()
    status = ProductionStatus(int(refstatus.getValue()))
    reason = IRISReference(iris)
    needsupdate = iris.classMethodBoolean("Ens.Director", "ProductionNeedsUpdate", reason)
    reason_update = f"Production needs update: {reason.getValue()}" if needsupdate else ""

    if status == ProductionStatus.Running and full_status:
        items_status = production_items_status(iris, True, name)
        newline = "\n"
        text = f"Production {name} is running with items: \n{newline.join(items_status)}\n{reason_update}"
    else:
        text = f"Production {name} with status: {status.name}\n{reason_update}"
    return [TextContent(type="text", text=text)]


async def _start(args: dict, iris, db) -> list[TextContent]:
    name = args.get("name")
    raise_on_error(
        iris,
        iris.classMethodString("Ens.Director", "StartProduction", *([name] if name else [])),
    )
    refname = IRISReference(iris)
    name and refname.setValue(name)
    refstatus = IRISReference(iris)
    status = iris.classMethodString("Ens.Director", "GetProductionStatus", refname, refstatus)
    if not name:
        name = refname.getValue()
    if status != "1" or ProductionStatus(int(refstatus.getValue())) != ProductionStatus.Running:
        raise ValueError(f"Production {name} not started.")
    return [TextContent(type="text", text="Started production")]


async def _stop(args: dict, iris, db) -> list[TextContent]:
    timeout = args.get("timeout")
    force = args.get("force", False)
    raise_on_error(
        iris,
        iris.classMethodString("Ens.Director", "StopProduction", timeout or 10, force),
    )
    return [TextContent(type="text", text="Stopped production")]


async def _recover(args: dict, iris, db) -> list[TextContent]:
    raise_on_error(iris, iris.classMethodString("Ens.Director", "RecoverProduction"))
    return [TextContent(type="text", text="Recovered")]


async def _needsupdate(args: dict, iris, db) -> list[TextContent]:
    reason = IRISReference(iris)
    result = iris.classMethodBoolean("Ens.Director", "ProductionNeedsUpdate", reason)
    if result:
        raise ValueError(f"Production needs update: {reason.getValue()}")
    return [TextContent(type="text", text="Production does not need update")]


async def _update(args: dict, iris, db) -> list[TextContent]:
    timeout = args.get("timeout")
    force = args.get("force", False)
    raise_on_error(
        iris,
        iris.classMethodString("Ens.Director", "UpdateProduction", timeout, force),
    )
    return [TextContent(type="text", text="Production updated")]


async def _logs(args: dict, iris, db) -> list[TextContent]:
    item_name = args.get("item_name")
    limit = args.get("limit", 10)
    log_type = []
    args.get("log_type_info", False) and log_type.append(LogType.Info.value)
    args.get("log_type_alert", False) and log_type.append(LogType.Alert.value)
    args.get("log_type_error", True) and log_type.append(LogType.Error.value)
    args.get("log_type_warning", True) and log_type.append(LogType.Warning.value)
    logs = []
    with db.cursor() as cur:
        sql = f"""
select top ? TimeLogged , %External(Type) Type, ConfigName, Text
from Ens_Util.Log
where
{"ConfigName = ?" if item_name else "1=1"}
{f"and type in ({', '.join(['?'] * len(log_type))})" if log_type else ""}
order by id desc
"""
        params = [limit, *([item_name] if item_name else []), *log_type]
        cur.execute(sql, params)
        for row in cur.fetchall():
            logs.append(f"{row[0]} {row[1]} {row[2]} {row[3]}")
    return [TextContent(type="text", text="\n".join(logs))]


async def _queues(args: dict, iris, db) -> list[TextContent]:
    with db.cursor() as cur:
        cur.execute("select * from Ens.Queue_Enumerate()")
        rows = cur.fetchall()
    queues = [", ".join([f"{cell}" for cell in row]) for row in rows]
    return [TextContent(type="text", text="\n".join(queues))]


_DISPATCH = {
    "interoperability_production_create": _create,
    "interoperability_production_status": _status,
    "interoperability_production_start": _start,
    "interoperability_production_stop": _stop,
    "interoperability_production_recover": _recover,
    "interoperability_production_needsupdate": _needsupdate,
    "interoperability_production_update": _update,
    "interoperability_production_logs": _logs,
    "interoperability_production_queues": _queues,
}


async def call_tool(name: str, args: dict, iris, db) -> list[TextContent]:
    handler = _DISPATCH.get(name)
    if handler is None:
        raise ValueError(f"Unknown interoperability tool: {name}")
    return await handler(args, iris, db)
