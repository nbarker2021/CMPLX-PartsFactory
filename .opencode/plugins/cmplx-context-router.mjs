const CMPLX_TERMS =
  /\b(CMPLX|CQE|Manny|TMN|SNAP|MMDB|MDHG|MORSR|TarPit|SpeedLight|Aletheia|morphon|repo-kernel|PartsFactory)\b/i;

const READ_TOOLS = /read|grep|glob|list|bash|shell|search/i;
const EDIT_TOOLS = /edit|write|patch|multiedit/i;
const CATALOG_TOOLS = /catalog|discover|composition|compose|test/i;

function textFromParts(parts = []) {
  return parts
    .map((part) => {
      if (typeof part === "string") return part;
      if (part && typeof part.text === "string") return part.text;
      if (part && typeof part.content === "string") return part.content;
      return "";
    })
    .join("\n");
}

function pushTextPart(parts, text) {
  if (!Array.isArray(parts)) return;
  parts.push({ type: "text", text });
}

function appendOutput(output, text) {
  if (!output || typeof output.output !== "string") return;
  if (output.output.includes("[CMPLX hook route]")) return;
  output.output = `${output.output}\n\n${text}`;
}

function routeForTool(tool) {
  if (EDIT_TOOLS.test(tool)) {
    return {
      gate: "pre-edit/post-edit",
      skills: "cmplx-memory-review + cmplx-tool-discovery",
      lane: "boundary check, existing implementation search, then durable memory if identity changes",
    };
  }
  if (CATALOG_TOOLS.test(tool)) {
    return {
      gate: "specialized-skill",
      skills: "cmplx-tool-discovery / cmplx-catalog-build / cmplx-composition-test",
      lane: "existing indexes, catalog evidence, conservation/provenance notes",
    };
  }
  if (READ_TOOLS.test(tool)) {
    return {
      gate: "pre-tool/post-tool",
      skills: "cmplx-memory-review + cmplx-tool-discovery",
      lane: "bounded reads, existing indexes first, report what changed",
    };
  }
  return {
    gate: "post-tool",
    skills: "cmplx-hook-pause-gates",
    lane: "absorb result into working map before continuing",
  };
}

const SYSTEM_ROUTE = [
  "CMPLX hook route:",
  "Anywhere normal AI would continue underinformed, refresh context first.",
  "Use cmplx-memory-review for identity/lineage, cmplx-tool-discovery for capability evidence, cmplx-repo-kernel-control for controller evidence, cmplx-catalog-build for catalog mutation, and cmplx-composition-test for wiring/parity checks.",
  "Names are addresses, not essence; durable review memory lives under D:\\PartsFactory\\identity_review.",
].join(" ");

export default async function CMPLXContextRouterPlugin() {
  return {
    async "experimental.chat.system.transform"(_input, output) {
      if (Array.isArray(output.system) && !output.system.some((item) => item.includes("CMPLX hook route:"))) {
        output.system.push(SYSTEM_ROUTE);
      }
    },

    async "chat.message"(_input, output) {
      const text = textFromParts(output.parts);
      const relevant = CMPLX_TERMS.test(text) || text.length > 500;
      if (!relevant) return;
      pushTextPart(
        output.parts,
        [
          "[CMPLX hook route]",
          "Before answering or using tools, refresh the proper lane:",
          "cmplx-hook-pause-gates -> cmplx-memory-review -> matching tool skill.",
          "If this touches lineage, names, repo history, hooks, skills, tools, catalog, or composition, check identity_review and existing indexes first.",
        ].join(" ")
      );
    },

    async "tool.execute.after"(input, output) {
      const route = routeForTool(input.tool || "");
      appendOutput(
        output,
        [
          "[CMPLX hook route]",
          `Gate: ${route.gate}.`,
          `Refresh via: ${route.skills}.`,
          `Lane: ${route.lane}.`,
          "Do not continue from raw tool output alone; update the working map or checkpoint when the identity map changes.",
        ].join(" ")
      );
    },

    async "experimental.session.compacting"(_input, output) {
      if (Array.isArray(output.context)) {
        output.context.push(
          [
            "CMPLX compaction hook:",
            "Preserve user corrections, sources read, files changed, hook/skill/tool route decisions, unresolved risks, and next reads.",
            "Resume from D:\\PartsFactory\\identity_review checkpoints instead of restarting.",
          ].join(" ")
        );
      }
    },
  };
}
