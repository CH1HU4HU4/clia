import { type Spec } from "../args.ts";
import { SPEC as AUTH_LOGIN } from "./auth/login.ts";
import { SPEC as AUTH_LOGOUT } from "./auth/logout.ts";
import { SPEC as AUTH_STATUS } from "./auth/status.ts";
import { SPEC as CONFIG_GET } from "./config/get.ts";
import { SPEC as CONFIG_LIST } from "./config/list.ts";
import { SPEC as CONFIG_SET } from "./config/set.ts";
import { SPEC as CONFIG_UNSET } from "./config/unset.ts";
import { SPEC as PROJECT_CREATE } from "./project/create.ts";
import { SPEC as PROJECT_DELETE } from "./project/delete.ts";
import { SPEC as PROJECT_GET } from "./project/get.ts";
import { SPEC as PROJECT_LIST } from "./project/list.ts";
import { SPEC as PROJECT_UPDATE } from "./project/update.ts";
import { SPEC as WHOAMI } from "./whoami.ts";
import { SPEC as COMPLETION } from "./meta/completion.ts";
import { SPEC as HELP } from "./meta/help.ts";
import { SPEC as SCHEMA } from "./meta/schema.ts";
import { SPEC as VERSION } from "./meta/version.ts";

const AUTH_GROUP: Spec = {
  path: ["auth"],
  summary: "Authenticate and inspect credentials",
  description: "Log in, log out, and check the current credential.",
  arguments: [],
  flags: [],
  examples: [],
  group: true,
};

const CONFIG_GROUP: Spec = {
  path: ["config"],
  summary: "Read and write CLI configuration",
  description: "Inspect and update the user config. Project config never holds secrets.",
  arguments: [],
  flags: [],
  examples: [],
  group: true,
};

const PROJECT_GROUP: Spec = {
  path: ["project"],
  summary: "Work with projects",
  description: "Create, inspect, update, and delete projects.",
  arguments: [],
  flags: [],
  examples: [],
  group: true,
};

const ALL: Spec[] = [
  AUTH_GROUP, AUTH_LOGIN, AUTH_LOGOUT, AUTH_STATUS,
  CONFIG_GROUP, CONFIG_GET, CONFIG_SET, CONFIG_LIST, CONFIG_UNSET,
  PROJECT_GROUP, PROJECT_LIST, PROJECT_GET, PROJECT_CREATE, PROJECT_UPDATE, PROJECT_DELETE,
  WHOAMI, VERSION, COMPLETION, SCHEMA, HELP,
];

export const SPECS: Record<string, Spec> = {};
for (const spec of ALL) SPECS[spec.path.join(" ")] = spec;

export function allSpecs(): Record<string, Spec> {
  return SPECS;
}
