(function () {
  function shouldIgnoreClick(target) {
    return Boolean(target.closest("a,button,input,select,textarea,form,label"));
  }

  document.querySelectorAll("form[data-confirm]").forEach(function (form) {
    form.addEventListener("submit", function (event) {
      var message = form.getAttribute("data-confirm") || "هل أنت متأكد؟";
      if (!window.confirm(message)) {
        event.preventDefault();
      }
    });
  });

  document.querySelectorAll("tr[data-href]").forEach(function (row) {
    row.addEventListener("click", function (event) {
      if (shouldIgnoreClick(event.target)) {
        return;
      }
      var href = row.getAttribute("data-href");
      if (href) {
        window.location.href = href;
      }
    });
  });

  document.querySelectorAll("input[data-table-filter-input]").forEach(function (input) {
    var targetSelector = input.getAttribute("data-table-target");
    var counterSelector = input.getAttribute("data-table-counter");
    var table = targetSelector ? document.querySelector(targetSelector) : null;
    if (!table) {
      return;
    }
    var tbody = table.querySelector("tbody");
    if (!tbody) {
      return;
    }
    var rows = Array.prototype.slice.call(tbody.querySelectorAll("tr"));
    var counter = counterSelector ? document.querySelector(counterSelector) : null;

    function updateFilter() {
      var query = (input.value || "").trim().toLowerCase();
      var visible = 0;
      rows.forEach(function (row) {
        var isEmptyState = row.children.length === 1 && row.children[0].hasAttribute("colspan");
        if (isEmptyState) {
          row.classList.remove("hidden-row");
          return;
        }
        var text = row.textContent.toLowerCase();
        var match = !query || text.indexOf(query) !== -1;
        row.classList.toggle("hidden-row", !match);
        if (match) {
          visible += 1;
        }
      });
      if (counter) {
        counter.textContent = visible + " نتيجة";
      }
    }

    input.addEventListener("input", updateFilter);
  });
})();
