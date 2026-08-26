const COPY = {
  en: {
    title: "CJK Fonts",
    intro: "Preview the actual 2-bit device bitmaps, then download verified physical font files from GitHub Release.",
    searchLabel: "Search fonts", searchPlaceholder: "Name or description", languageLabel: "Language", categoryLabel: "Category", previewLabel: "Preview size", all: "All",
    languages: { "zh-Hans": "Simplified Chinese", "zh-Hant": "Traditional Chinese", ja: "Japanese" },
    categories: { "sans-serif": "Sans serif", serif: "Serif", handwriting: "Handwriting", "rounded-sans": "Rounded sans", display: "Display", fangsong: "Fangsong" },
    downloads: "Download physical sizes", uiFont: "UI font package", source: "Source", manifest: "Release manifest", maker: "Make a custom font", theme: "Website theme", themeLight: "Light", themeDark: "Dark", themeSystem: "System", deviceColor: "Reader body color", deviceBlack: "Black body", deviceSilver: "Gray body", displayMode: "Reader screen appearance", displayLight: "Light screen", displayDark: "Dark screen",
    footer: "Pages hosts only this catalog and compact PNG previews. Font binaries remain on GitHub Release.",
    loading: "Loading catalog…", empty: "No matching fonts.", error: "Catalog unavailable. Try again later.", families: count => `${count} font ${count === 1 ? "family" : "families"}`, lastUpdated: "Last updated", releaseNotes: "Release notes", actualPreview: size => `${size} pt · reader-scale 480×800 preview`,
  },
  zh: {
    title: "CJK 字体库",
    intro: "预览设备实际使用的 2-bit 点阵，并从 GitHub Release 下载已校验的物理字号字体。",
    searchLabel: "搜索字体", searchPlaceholder: "名称或简介", languageLabel: "语言", categoryLabel: "类型", previewLabel: "预览字号", all: "全部",
    languages: { "zh-Hans": "简体中文", "zh-Hant": "繁体中文", ja: "日语" },
    categories: { "sans-serif": "无衬线体", serif: "衬线体", handwriting: "手写体", "rounded-sans": "圆体", display: "展示体", fangsong: "仿宋体" },
    downloads: "下载物理字号", uiFont: "UI 字体包", source: "字体来源", manifest: "Release 清单", maker: "制作自制字体", theme: "网页主题", themeLight: "浅色", themeDark: "深色", themeSystem: "跟随系统", deviceColor: "阅读器机身颜色", deviceBlack: "黑色机身", deviceSilver: "灰色机身", displayMode: "阅读器屏幕外观", displayLight: "白底黑字", displayDark: "黑底白字",
    footer: "Pages 只托管目录和轻量 PNG 预览；字体二进制仍由 GitHub Release 分发。",
    loading: "正在加载字体目录…", empty: "没有匹配的字体。", error: "字体目录暂时不可用，请稍后重试。", families: count => `${count} 个字体家族`, lastUpdated: "最后更新", releaseNotes: "发行说明", actualPreview: size => `${size} pt · 480×800 实机比例预览`,
  },
  ja: {
    title: "CJK フォントカタログ",
    intro: "端末で使われる実際の 2-bit ビットマップを確認し、検証済みの物理サイズを GitHub Release から取得できます。",
    searchLabel: "フォント検索", searchPlaceholder: "名前または説明", languageLabel: "言語", categoryLabel: "分類", previewLabel: "プレビューサイズ", all: "すべて",
    languages: { "zh-Hans": "簡体字中国語", "zh-Hant": "繁体字中国語", ja: "日本語" },
    categories: { "sans-serif": "ゴシック体", serif: "明朝体", handwriting: "手書き体", "rounded-sans": "丸ゴシック体", display: "ディスプレイ体", fangsong: "仿宋体" },
    downloads: "物理サイズをダウンロード", uiFont: "UI フォントパッケージ", source: "入手元", manifest: "Release マニフェスト", maker: "個人用フォントを作成", theme: "サイトテーマ", themeLight: "ライト", themeDark: "ダーク", themeSystem: "システム", deviceColor: "リーダー本体カラー", deviceBlack: "ブラック本体", deviceSilver: "グレー本体", displayMode: "リーダー画面表示", displayLight: "白地に黒", displayDark: "黒地に白",
    footer: "Pages はカタログと軽量 PNG のみを配信し、フォント本体は GitHub Release に置かれます。",
    loading: "カタログを読み込み中…", empty: "該当するフォントはありません。", error: "カタログを読み込めませんでした。", families: count => `${count} ファミリー`, lastUpdated: "最終更新", releaseNotes: "リリースノート", actualPreview: size => `${size} pt · 480×800 実機比率プレビュー`,
  },
};

const THEME_STORAGE_KEY = "crosspoint-font-catalog-theme";
const THEME_MODES = ["light", "dark", "system"];
const DEFAULT_PREVIEW_SIZE = "18";
const state = { catalog: null, locale: "en", themeMode: "system", prefersDark: false, query: "", language: "", category: "", previewSize: DEFAULT_PREVIEW_SIZE, deviceColor: "black", displayMode: "light" };
const nodes = {
  catalog: document.querySelector("#catalog"), status: document.querySelector("#status"), search: document.querySelector("#search"),
  language: document.querySelector("#language-filter"), category: document.querySelector("#category-filter"), previewSize: document.querySelector("#preview-size"), theme: document.querySelector("#theme-switcher"),
  deviceColor: document.querySelector("#device-color"), displayMode: document.querySelector("#display-mode"),
  template: document.querySelector("#font-card-template"), manifest: document.querySelector("#manifest-link"), lastUpdated: document.querySelector("#last-updated"),
};

function preferredLocale() {
  const stored = localStorage.getItem("crosspoint-font-catalog-locale");
  if (COPY[stored]) return stored;
  const language = navigator.language.toLowerCase();
  if (language.startsWith("zh")) return "zh";
  if (language.startsWith("ja")) return "ja";
  return "en";
}

function preferredThemeMode() {
  const stored = localStorage.getItem(THEME_STORAGE_KEY);
  return THEME_MODES.includes(stored) ? stored : "system";
}

function resolvedTheme() {
  return state.themeMode === "system" ? (state.prefersDark ? "dark" : "light") : state.themeMode;
}

function updatePreviewAppearance(preview, dark) {
  preview.classList.toggle("preview--light", !dark);
  preview.closest(".preview-frame")?.classList.toggle("preview-frame--dark", dark);
}

function applyTheme() {
  const theme = resolvedTheme();
  document.documentElement.dataset.theme = theme;
  document.documentElement.style.colorScheme = theme;
  nodes.theme.querySelectorAll("button").forEach(button => {
    button.setAttribute("aria-pressed", String(button.dataset.theme === state.themeMode));
  });
  document.querySelectorAll(".preview").forEach(preview => {
    updatePreviewAppearance(preview, state.displayMode === "dark");
  });
}

function populateThemeSwitcher() {
  const copy = COPY[state.locale];
  nodes.theme.setAttribute("aria-label", copy.theme);
  nodes.theme.replaceChildren(...[
    ["light", copy.themeLight],
    ["dark", copy.themeDark],
    ["system", copy.themeSystem],
  ].map(([mode, label]) => {
    const button = document.createElement("button");
    button.type = "button";
    button.dataset.theme = mode;
    button.textContent = label;
    button.title = copy.theme;
    button.addEventListener("click", () => {
      state.themeMode = mode;
      localStorage.setItem(THEME_STORAGE_KEY, mode);
      applyTheme();
    });
    return button;
  }));
}

function populateDeviceControls() {
  const copy = COPY[state.locale];
  for (const [node, stateKey, options] of [
    [nodes.deviceColor, "deviceColor", [["black", copy.deviceBlack], ["silver", copy.deviceSilver]]],
    [nodes.displayMode, "displayMode", [["light", copy.displayLight], ["dark", copy.displayDark]]],
  ]) {
    node.replaceChildren(...options.map(([value, label]) => {
      const button = document.createElement("button");
      button.type = "button";
      button.textContent = label;
      button.dataset.value = value;
      button.setAttribute("aria-pressed", String(state[stateKey] === value));
      button.addEventListener("click", () => {
        state[stateKey] = value;
        updateDeviceControlStates();
        render();
      });
      return button;
    }));
  }
}
function updateDeviceControlStates() {
  for (const [node, stateKey] of [[nodes.deviceColor, "deviceColor"], [nodes.displayMode, "displayMode"]]) {
    node.querySelectorAll("button").forEach(button => {
      button.setAttribute("aria-pressed", String(button.dataset.value === state[stateKey]));
    });
  }
}
function applyCopy() {
  const copy = COPY[state.locale];
  document.documentElement.lang = state.locale;
  document.querySelectorAll("[data-copy]").forEach(node => { const value = copy[node.dataset.copy]; if (typeof value === "string") node.textContent = value; });
  document.querySelectorAll("[data-copy-placeholder]").forEach(node => { node.placeholder = copy[node.dataset.copyPlaceholder]; });
  document.querySelectorAll("[data-locale]").forEach(button => button.setAttribute("aria-pressed", String(button.dataset.locale === state.locale)));
  populateThemeSwitcher();
  populateDeviceControls();
  applyTheme();
  updateLastUpdated();
  render();
}

function formatDate(iso) {
  const date = String(iso || "").slice(0, 10);
  return date.length === 10 ? date : "";
}

function updateLastUpdated() {
  const copy = COPY[state.locale];
  const date = state.catalog?.updatedAt ? formatDate(state.catalog.updatedAt) : "";
  nodes.lastUpdated.textContent = date ? `${copy.lastUpdated} ${date} · ${copy.releaseNotes}` : "";
  nodes.lastUpdated.href = state.catalog?.manifestUrl ? state.catalog.manifestUrl.replace(/\/download\/([^/]+)\/fonts\.json$/, "/tag/$1") : "";
}

function optionValues(key) {
  if (!state.catalog) return [];
  const values = new Set();
  state.catalog.families.forEach(family => {
    if (key === "languages") family.languages.forEach(value => values.add(value));
    else if (family[key]) values.add(family[key]);
  });
  return [...values].sort((a, b) => a.localeCompare(b));
}

function filterOptionLabel(kind, value) {
  return COPY[state.locale][kind]?.[value] || value;
}

function populateFilters() {
  const allText = COPY[state.locale].all;
  for (const [node, kind, values] of [
    [nodes.language, "languages", optionValues("languages")],
    [nodes.category, "categories", optionValues("category")],
  ]) {
    const selected = node.value;
    node.replaceChildren(new Option(allText, ""), ...values.map(value => new Option(filterOptionLabel(kind, value), value)));
    node.value = values.includes(selected) ? selected : "";
  }
  const selectedSize = state.previewSize;
  nodes.previewSize.replaceChildren(...state.catalog.previewSizes.map(size => {
    const button = document.createElement("button");
    button.type = "button";
    button.dataset.previewSize = String(size);
    button.textContent = `${size} pt`;
    button.setAttribute("aria-pressed", String(String(size) === selectedSize));
    button.addEventListener("click", () => {
      state.previewSize = String(size);
      render();
    });
    return button;
  }));
  if (!state.catalog.previewSizes.map(String).includes(selectedSize)) state.previewSize = String(state.catalog.previewSizes[0]);
  nodes.previewSize.querySelectorAll("button").forEach(button => {
    button.setAttribute("aria-pressed", String(button.dataset.previewSize === state.previewSize));
  });
}

function humanBytes(value) {
  const units = ["B", "KiB", "MiB"];
  let size = value; let unit = 0;
  while (size >= 1024 && unit < units.length - 1) { size /= 1024; unit += 1; }
  return `${size.toFixed(unit === 0 ? 0 : 1)} ${units[unit]}`;
}
async function sha256Hex(buffer) {
  const digest = await crypto.subtle.digest("SHA-256", buffer);
  return Array.from(new Uint8Array(digest), value => value.toString(16).padStart(2, "0")).join("");
}

async function downloadUiFontPackage(family, link) {
  const copy = COPY[state.locale];
  const uiFiles = family.files.filter(file => [8, 10, 12].includes(file.physicalSize));
  if (uiFiles.length !== 3 || typeof JSZip === "undefined") throw new Error("UI package unavailable");
  const originalText = link.textContent;
  link.textContent = `${originalText}…`;
  link.setAttribute("aria-busy", "true");
  try {
    const zip = new JSZip();
    const folder = zip.folder(family.name);
    const fonts = [];
    for (const file of uiFiles) {
      const response = await fetch(file.downloadUrl);
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      const buffer = await response.arrayBuffer();
      if (buffer.byteLength !== file.byteSize || await sha256Hex(buffer) !== file.sha256) throw new Error("Font verification failed");
      folder.file(file.name, buffer);
      fonts.push({ size: file.physicalSize, role: "ui", file: file.name, styles: family.styles, sizeBytes: file.byteSize, sha256: file.sha256 });
    }
    folder.file("manifest.json", JSON.stringify({ format: 1, family: familyDisplayName(family), id: family.name, role: "ui", cpfontVersion: 4, uiSizes: [8, 10, 12], readerSizes: [], styles: family.styles, fonts }, null, 2) + "\n");
    folder.file("SHA256SUMS", uiFiles.map(file => `${file.sha256}  ${file.name}`).join("\n") + "\n");
    const blob = await zip.generateAsync({ type: "blob", compression: "DEFLATE", compressionOptions: { level: 6 } });
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement("a");
    anchor.href = url;
    anchor.download = `${family.name}.cpfontpkg`;
    anchor.click();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
  } finally {
    link.textContent = originalText;
    link.removeAttribute("aria-busy");
  }
}

function familyDisplayName(family) {
  return family.displayNames[state.locale] || family.displayNames.en || family.name;
}

function render() {
  if (!state.catalog) return;
  const copy = COPY[state.locale];
  populateFilters();
  const query = state.query.trim().toLocaleLowerCase();
  const families = state.catalog.families.filter(family => {
    const searchableNames = Object.values(family.displayNames).join(" ");
    const matchesText = !query || `${family.name} ${searchableNames} ${family.description || ""}`.toLocaleLowerCase().includes(query);
    const matchesLanguage = !state.language || family.languages.includes(state.language);
    const matchesCategory = !state.category || family.category === state.category;
    return matchesText && matchesLanguage && matchesCategory;
  });
  nodes.catalog.replaceChildren();
  families.forEach(family => {
    const fragment = nodes.template.content.cloneNode(true);
    const displayName = familyDisplayName(family);
    fragment.querySelector("h2").textContent = displayName;
    fragment.querySelector(".family-id").textContent = family.name;
    const description = fragment.querySelector(".description");
    description.textContent = family.description || "";
    description.hidden = !family.description;
    const device = fragment.querySelector(".device-preview");
    device.classList.remove("device-preview--black", "device-preview--silver");
    device.classList.add(`device-preview--${state.deviceColor}`);
    const preview = fragment.querySelector(".preview");
    preview.src = family.previews[state.previewSize];
    preview.alt = `${displayName}, ${state.previewSize} pt`;
    updatePreviewAppearance(preview, state.displayMode === "dark");
    preview.addEventListener("error", () => preview.classList.add("is-broken"), { once: true });
    fragment.querySelector(".tags").textContent = [...family.languages, family.category].filter(Boolean).join(" · ");
    const downloads = fragment.querySelector(".downloads");
    downloads.setAttribute("aria-label", `${family.name}: ${copy.downloads}`);
    const badge = document.createElement("a");
    badge.className = "ui-font-badge";
    badge.href = "#";
    badge.textContent = copy.uiFont;
    badge.setAttribute("aria-label", `${copy.uiFont}: ${family.name}`);
    badge.addEventListener("click", async event => {
      event.preventDefault();
      try { await downloadUiFontPackage(family, badge); }
      catch (error) { nodes.status.textContent = `${copy.uiFont}: ${error.message}`; }
    });
    downloads.append(badge);
    if (family.role !== "ui") {
      family.files.filter(file => ![8, 10, 12].includes(file.physicalSize)).forEach(file => {
        const link = document.createElement("a");
        link.href = file.downloadUrl;
        link.textContent = `${file.physicalSize} pt`;
        link.setAttribute("aria-label", `${file.physicalSize} pt, ${humanBytes(file.byteSize)}`);
        link.title = `${file.physicalSize} pt · ${humanBytes(file.byteSize)}`;
        link.rel = "noopener noreferrer";
        downloads.append(link);
      });
    }
    const source = fragment.querySelector(".source-link");
    if (family.sourceUrl) { source.href = family.sourceUrl; source.textContent = copy.source; }
    else source.remove();
    nodes.catalog.append(fragment);
  });
  nodes.status.textContent = families.length ? copy.families(families.length) : copy.empty;
}

function validateCatalog(catalog) {
  if (catalog?.schemaVersion !== 1 || catalog.cpfontVersion !== 4 || catalog.manifestVersion !== 2 || !Array.isArray(catalog.families)) throw new Error("Unsupported catalog schema");
  return catalog;
}

async function loadCatalog() {
  nodes.status.textContent = COPY[state.locale].loading;
  try {
    const response = await fetch("catalog.json", { cache: "no-cache" });
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    state.catalog = validateCatalog(await response.json());
    state.previewSize = state.catalog.previewSizes.map(String).includes(DEFAULT_PREVIEW_SIZE)
      ? DEFAULT_PREVIEW_SIZE
      : String(state.catalog.previewSizes[0]);
    nodes.manifest.href = state.catalog.manifestUrl;
    updateLastUpdated();
    render();
  } catch (error) {
    console.error(error);
    nodes.status.textContent = COPY[state.locale].error;
  }
}

document.querySelectorAll("[data-locale]").forEach(button => button.addEventListener("click", () => { state.locale = button.dataset.locale; localStorage.setItem("crosspoint-font-catalog-locale", state.locale); applyCopy(); }));
nodes.search.addEventListener("input", event => { state.query = event.target.value; render(); });
nodes.language.addEventListener("change", event => { state.language = event.target.value; render(); });
nodes.category.addEventListener("change", event => { state.category = event.target.value; render(); });

const colorScheme = window.matchMedia("(prefers-color-scheme: dark)");
state.prefersDark = colorScheme.matches;
const handleColorSchemeChange = event => {
  state.prefersDark = event.matches;
  if (state.themeMode === "system") applyTheme();
};
if (typeof colorScheme.addEventListener === "function") colorScheme.addEventListener("change", handleColorSchemeChange);
else colorScheme.addListener(handleColorSchemeChange);

state.locale = preferredLocale();
state.themeMode = preferredThemeMode();
applyCopy();
loadCatalog();
