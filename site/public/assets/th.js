// Alat kecil di sisi pengguna: tema, harakat, ukuran teks Arab, tombol salin. Situs tetap berfungsi tanpa JS.
(() => {
  const baca = (k) => { try { return localStorage.getItem(k); } catch (e) { return null; } };
  const simpan = (k, v) => { try { localStorage.setItem(k, v); } catch (e) {} };
  const root = document.documentElement;
  const tema = baca("th-tema");
  if (tema) root.dataset.theme = tema;
  let skala = parseFloat(baca("th-ar") || "1") || 1;
  const aturSkala = () => { root.style.setProperty("--ar", skala); simpan("th-ar", skala); };
  aturSkala();
  const HARAKAT = /[ً-ْٰـ]/g;
  function terapkanHarakat(on) {
    document.querySelectorAll(".ar").forEach((el) => {
      if (!el.dataset.asli) el.dataset.asli = el.innerHTML;
      el.innerHTML = on ? el.dataset.asli : el.dataset.asli.replace(HARAKAT, "");
    });
  }
  document.addEventListener("DOMContentLoaded", () => {
    const bh = document.getElementById("btn-harakat");
    if (baca("th-harakat") === "false") { bh?.setAttribute("aria-pressed", "false"); terapkanHarakat(false); }
    bh?.addEventListener("click", () => {
      const on = bh.getAttribute("aria-pressed") !== "true";
      bh.setAttribute("aria-pressed", on); terapkanHarakat(on); simpan("th-harakat", on);
    });
    document.getElementById("btn-besar")?.addEventListener("click", () => { skala = Math.min(1.6, +(skala + 0.1).toFixed(2)); aturSkala(); });
    document.getElementById("btn-kecil")?.addEventListener("click", () => { skala = Math.max(0.8, +(skala - 0.1).toFixed(2)); aturSkala(); });
    document.getElementById("btn-tema")?.addEventListener("click", () => {
      const gelap = root.dataset.theme ? root.dataset.theme === "dark" : matchMedia("(prefers-color-scheme: dark)").matches;
      root.dataset.theme = gelap ? "light" : "dark"; simpan("th-tema", root.dataset.theme);
    });
    document.querySelectorAll("[data-salin]").forEach((b) => b.addEventListener("click", async () => {
      const sumber = b.dataset.salinDari ? document.querySelector(b.dataset.salinDari)?.textContent : b.dataset.salin;
      const status = document.getElementById("status-salin");
      try { await navigator.clipboard.writeText(sumber || ""); if (status) status.textContent = b.dataset.pesan || "Tersalin."; }
      catch (e) { if (status) status.textContent = "Tidak bisa menyalin otomatis. Pilih teksnya lalu salin manual."; }
    }));
  });
})();
