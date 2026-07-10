"use strict";

const path = require("path");
const root = __dirname;

module.exports = {
  apps: [
    {
      name: "titan-web",
      cwd: root,
      script: path.join(root, "scripts", "start_web.sh"),
      interpreter: "bash",
      autorestart: true,
      restart_delay: 3000,
      max_restarts: 10,
      time: true,
      env: {
        APP_TZ: "Asia/Kolkata",
        WEB_PORT: "5000"
      }
    },
    {
      name: "titan-gateway",
      cwd: root,
      script: path.join(root, "scripts", "start_bot.sh"),
      interpreter: "bash",
      autorestart: true,
      restart_delay: 5000,
      max_restarts: 10,
      time: true,
      env: {
        APP_TZ: "Asia/Kolkata",
        GATEWAY_PORT: "3000"
      }
    }
  ]
};
