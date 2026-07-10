"use strict";

// Security/integrity preload must run before the legacy gateway imports axios
// and creates its Express application.
require("./runtime_guard").prepareGatewayRuntime();
require("../Gateway.js");
