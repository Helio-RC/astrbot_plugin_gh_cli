const bridge = window.AstrBotPluginPage;

const rows = document.getElementById("rows");
const errorBox = document.getElementById("error");
const btnRefresh = document.getElementById("btn-refresh");
const btnExport = document.getElementById("btn-export");
const btnClear = document.getElementById("btn-clear");
const filterSender = document.getElementById("filter-sender");
const filterGroup = document.getElementById("filter-group");
const filterOk = document.getElementById("filter-ok");

const SOURCE_LABEL = { command: "指令", tool: "AI 工具" };
const GROUP_LABEL = {
  repo: "仓库", issue: "Issue", pr: "PR", release: "Release",
  gist: "Gist", search: "搜索", run: "Actions", api: "API",
};

function esc(text) {
  return String(text ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;");
}

function showError(message) {
  errorBox.textContent = message;
  errorBox.hidden = false;
}

function clearError() {
  errorBox.hidden = true;
}

function renderRows(entries) {
  if (!entries.length) {
    rows.innerHTML = '<tr><td colspan="11" class="empty">暂无记录</td></tr>';
    return;
  }
  rows.innerHTML = entries
    .map(
      (e) => `
      <tr class="${e.ok ? "ok" : "fail"}">
        <td class="mono">${esc(e.ts)}</td>
        <td>${esc(e.sender) || "-"}</td>
        <td class="mono small">${esc(e.umo) || "-"}</td>
        <td>${esc(SOURCE_LABEL[e.source] ?? e.source)}</td>
        <td>${esc(GROUP_LABEL[e.group] ?? e.group)}</td>
        <td>${esc(e.action)}</td>
        <td>${esc(e.repo) || "-"}</td>
        <td class="mono small">${esc((e.params ?? []).join(", "))}</td>
        <td class="small">${esc(e.body_preview) || "-"}</td>
        <td>${e.ok ? "✅" : "❌"}</td>
        <td class="small err-text">${esc(e.error) || ""}</td>
      </tr>`,
    )
    .join("");
}

async function loadStats() {
  try {
    const stats = await bridge.apiGet("audit/stats");
    document.getElementById("stat-total").textContent = `总数: ${stats.total}`;
    document.getElementById("stat-ok").textContent = `成功: ${stats.ok_count}`;
    document.getElementById("stat-fail").textContent = `失败: ${stats.fail_count}`;
  } catch (err) {
    showError(`加载统计失败: ${err.message}`);
  }
}

async function loadEntries() {
  clearError();
  rows.innerHTML = '<tr><td colspan="11" class="empty">加载中...</td></tr>';
  try {
    const params = {
      sender: filterSender.value,
      group: filterGroup.value,
      ok: filterOk.value,
      limit: 200,
    };
    const entries = await bridge.apiGet("audit/list", params);
    renderRows(entries);
    fillFilterOptions(entries);
  } catch (err) {
    showError(`加载审计日志失败: ${err.message}`);
    rows.innerHTML = "";
  }
}

function fillFilterOptions(entries) {
  const senders = [...new Set(entries.map((e) => e.sender).filter(Boolean))].sort();
  const groups = [...new Set(entries.map((e) => e.group).filter(Boolean))].sort();
  fillSelect(filterSender, senders, "全部发起人");
  fillSelect(filterGroup, groups, "全部指令组");
}

function fillSelect(select, values, placeholder) {
  const current = select.value;
  select.innerHTML = `<option value="">${placeholder}</option>` +
    values.map((v) => `<option value="${esc(v)}">${esc(v)}</option>`).join("");
  select.value = values.includes(current) ? current : "";
}

btnRefresh.addEventListener("click", () => {
  loadEntries();
  loadStats();
});

btnExport.addEventListener("click", async () => {
  try {
    await bridge.download("audit/export", { limit: 1000 }, "audit.json");
  } catch (err) {
    showError(`导出失败: ${err.message}`);
  }
});

btnClear.addEventListener("click", async () => {
  if (btnClear.dataset.arm !== "1") {
    btnClear.dataset.arm = "1";
    btnClear.textContent = "再次点击确认清空";
    setTimeout(() => {
      delete btnClear.dataset.arm;
      btnClear.textContent = "清空日志";
    }, 3000);
    return;
  }
  delete btnClear.dataset.arm;
  btnClear.textContent = "清空日志";
  try {
    const resp = await bridge.apiPost("audit/clear");
    if (!resp || resp.cleared === false) {
      throw new Error("服务端返回失败");
    }
    loadEntries();
    loadStats();
  } catch (err) {
    showError(`清空失败: ${err.message}`);
  }
});

[filterSender, filterGroup, filterOk].forEach((el) =>
  el.addEventListener("change", loadEntries),
);

await bridge.ready();
loadEntries();
loadStats();
