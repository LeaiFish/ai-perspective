/* The report archive is the permalink target, including for same-day revisions. */
(async function () {
  const host = document.getElementById("focus");
  const tracks = {tech: "技术", product: "产品", people: "用户"};
  const requested = new URLSearchParams(location.search).get("issue");
  const base = "./data/trends/";
  function el(tag, text, cls) {
    const node = document.createElement(tag);
    if (text) node.textContent = text;
    if (cls) node.className = cls;
    return node;
  }
  function link(text, href, cls) {
    const node = el("a", text, cls);
    node.href = href;
    return node;
  }
  async function json(name) {
    const resp = await fetch(base + name, {cache: "no-cache"});
    if (!resp.ok) throw Error("issue_unavailable");
    return resp.json();
  }
  function reportIssue(report) {
    return report.revision_of ? report.report_id : new Intl.DateTimeFormat("sv-SE", {
      timeZone: "Asia/Shanghai", year: "numeric", month: "2-digit", day: "2-digit"
    }).format(new Date(report.period_end));
  }
  async function load() {
    if (requested === "seed") return {board: await json("focus-seed.json"), issue: "seed"};
    if (requested) {
      let path;
      if (/^\d{4}-\d{2}-\d{2}$/.test(requested)) path = "daily/";
      else if (/^[a-f0-9]{64}$/.test(requested)) path = "revisions/";
      else throw Error("invalid_issue");
      const report = await json(path + requested + ".json");
      if (!report.focus || reportIssue(report) !== requested) throw Error("no_focus");
      return {board: report.focus, issue: requested};
    }
    const latest = await json("latest.json");
    if (latest.daily?.focus) return {board: latest.daily.focus, issue: reportIssue(latest.daily)};
    return {board: await json("focus-seed.json"), issue: "seed"};
  }
  try {
    const {board, issue} = await load();
    const stories = new Map(board.stories.map(story => [story.id, story]));
    const issueUrl = "?issue=" + issue;
    const localHome = requested ? issueUrl + "#home" : "./focus.html#home";
    const date = document.getElementById("edition-date");
    date.dateTime = board.date;
    date.textContent = "判断更新于 " + board.date.replaceAll("-", ".");
    const days = board.stories.flatMap(s => s.evidence.map(e => e.date)).sort();
    const footer = document.getElementById("period");
    footer.append("本期材料 · " + days[0] + " 至 " + days.at(-1), link("本期固定链接", issueUrl, "issue-link home-link"));
    if (requested) footer.append(link("查看最新一期", "./focus.html", "issue-link home-link"));
    const home = el("div", "", "home");
    const mast = el("div", "", "mast");
    mast.append(el("h1", "我关注的"), el("p", "近期方向判断"));
    const leads = el("div", "", "leads");
    for (const id of board.leads) {
      const s = stories.get(id);
      const card = link("", issueUrl + "#" + id, "lead");
      card.append(el("span", tracks[s.track], "kicker"), el("h2", s.title), el("p", s.summary), el("span", "查看依据", "more"));
      leads.append(card);
    }
    const channels = el("div", "", "channels");
    for (const [key, name] of Object.entries(tracks)) {
      const column = el("section", "", "column");
      column.append(el("h3", name));
      const rows = board.stories.filter(s => s.track === key).flatMap(s => s.evidence.map((e, i) => ({s, e, i})));
      const seen = new Set();
      for (const {s, e, i} of rows.sort((a, b) => b.e.date.localeCompare(a.e.date))) {
        if (seen.has(e.url)) continue;
        seen.add(e.url);
        const row = link("", issueUrl + "#" + s.id + "/" + (i + 1), "entry");
        row.append(el("span", e.date.slice(5).replace("-", ".") + " · " + e.source, "meta"), el("strong", e.title));
        column.append(row);
      }
      channels.append(column);
    }
    home.append(mast, leads, el("h2", "三条线索", "explore"), channels);
    function render() {
      const [id, number] = location.hash.slice(1).split("/");
      if (!id || id === "home") { host.replaceChildren(home); return; }
      const s = stories.get(id);
      if (!s) { host.replaceChildren(el("p", "本期没有这条判断。"), link("返回本期首页", localHome, "back")); return; }
      const article = el("article", "", "detail current");
      const back = link("返回本期首页", localHome, "back");
      const note = el("div", "", "note");
      note.append(el("h2", "为什么这样判断"), el("p", s.analysis));
      article.append(back, el("div", tracks[s.track] + " · 方向判断", "kicker"), el("h1", s.title), note, el("h2", "具体依据"));
      let selected;
      s.evidence.forEach((e, i) => {
        const item = el("section", "", "piece");
        const a = link(e.label, e.url, "source");
        if (new URL(e.url).protocol !== "https:") throw Error("invalid_source");
        a.target = "_blank";
        a.rel = "noopener noreferrer";
        item.append(el("span", e.date + " · " + e.source, "meta"), el("h3", e.title), el("p", e.detail), a);
        article.append(item);
        if (String(i + 1) === number) { selected = item; item.classList.add("selected"); }
      });
      host.replaceChildren(article);
      if (selected) selected.scrollIntoView({block:"center"}); else window.scrollTo(0,0);
    }
    render();
    window.addEventListener("hashchange", render);
  } catch {
    host.replaceChildren(el("p", "这一期的判断暂时无法读取。"), link("打开最新一期", "./focus.html", "back"), link("查看首期", "?issue=seed", "back home-link"));
  }
})();
